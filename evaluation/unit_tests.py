"""
Unit tests for controller/controller.py and storage_node/node.py.

Uses real in-process gRPC servers — no Docker, no mocks.
Run from the repository root inside the devcontainer:

    python evaluation/unit_tests.py
"""

import unittest
from concurrent import futures

import grpc
import project2_pb2_grpc
from project2_pb2 import Record, Context, PutRequest, SearchRequest, StoreRecordRequest, SearchLocalRequest, SplitPartitionRequest

from utils.utils import wait_for_grpc_target
from storage_node.node import StorageNodeService
from controller.controller import ControllerService


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

EMBEDDING = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

def make_record(id="test-record-001"):
    return Record(
        id=id,
        text="Distributed systems use replication for fault tolerance.",
        context=Context(doc_type="test", doc_name="fixture", doc_locator="test"),
        embedding=EMBEDDING,
    )


# gRPC helpers 
def start_node(port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    project2_pb2_grpc.add_StorageNodeServiceServicer_to_server(StorageNodeService(), server)
    server.add_insecure_port(f"localhost:{port}")
    server.start()
    wait_for_grpc_target(f"localhost:{port}")
    stub = project2_pb2_grpc.StorageNodeServiceStub(grpc.insecure_channel(f"localhost:{port}"))
    return server, stub

def start_controller(port, node_port):

    service = ControllerService()
    service.nodes = [{"target": f"localhost:{node_port}", "centroid": []}]

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    project2_pb2_grpc.add_ControllerServiceServicer_to_server(service, server)
    server.add_insecure_port(f"localhost:{port}")
    server.start()
    wait_for_grpc_target(f"localhost:{port}")
    stub = project2_pb2_grpc.ControllerServiceStub(grpc.insecure_channel(f"localhost:{port}"))
    return server, stub

class TestStorageNode(unittest.TestCase):

    def setUp(self):
        self.server, self.stub = start_node(port=15001)

    def tearDown(self):
        self.server.stop(grace=0)

    def test_store_record_ok(self):
        resp = self.stub.StoreRecord(StoreRecordRequest(record=make_record()))
        self.assertTrue(resp.ok)

    def test_store_record_count_is_one(self):
        resp = self.stub.StoreRecord(StoreRecordRequest(record=make_record()))
        self.assertEqual(resp.count, 1)

    def test_store_record_count_increments(self):
        self.stub.StoreRecord(StoreRecordRequest(record=make_record(id="rec-1")))
        resp = self.stub.StoreRecord(StoreRecordRequest(record=make_record(id="rec-2")))
        self.assertEqual(resp.count, 2)

    def test_store_record_centroid_is_set(self):
        resp = self.stub.StoreRecord(StoreRecordRequest(record=make_record()))
        self.assertGreater(len(resp.centroid.values), 0)

    def test_search_local_returns_stored_record(self):
        self.stub.StoreRecord(StoreRecordRequest(record=make_record()))
        resp = self.stub.SearchLocal(SearchLocalRequest(query_embedding=EMBEDDING, top_k=5))
        self.assertEqual(len(resp.hits), 1)
        self.assertEqual(resp.hits[0].id, "test-record-001")

    def test_search_local_vectors_searched_equals_record_count(self):
        self.stub.StoreRecord(StoreRecordRequest(record=make_record(id="rec-1")))
        self.stub.StoreRecord(StoreRecordRequest(record=make_record(id="rec-2")))
        resp = self.stub.SearchLocal(SearchLocalRequest(query_embedding=EMBEDDING, top_k=5))
        self.assertEqual(resp.vectors_searched, 2)

    def test_split_partition_counts_add_up(self):
        new_server, _ = start_node(port=15002)
        try:
            for i in range(10):
                self.stub.StoreRecord(StoreRecordRequest(record=make_record(id=f"rec-{i}")))
            resp = self.stub.SplitPartition(SplitPartitionRequest(new_node_target="localhost:15002"))
            self.assertTrue(resp.ok)
            self.assertGreater(resp.old_count, 0)
            self.assertGreater(resp.new_count, 0)
            self.assertEqual(resp.old_count + resp.new_count, 10)
        finally:
            new_server.stop(grace=0)


class TestController(unittest.TestCase):

    def setUp(self):
        # Start a real node first then point the controller at it
        self.node_server, self.node_stub = start_node(port=15011)
        self.ctrl_server, self.stub = start_controller(port=15010, node_port=15011)

    def tearDown(self):
        self.ctrl_server.stop(grace=0)
        self.node_server.stop(grace=0)

    def test_put_ok(self):
        resp = self.stub.Put(PutRequest(record=make_record()))
        self.assertTrue(resp.ok)

    def test_put_target_count_is_one_after_first_insert(self):
        resp = self.stub.Put(PutRequest(record=make_record()))
        self.assertEqual(resp.target_count, 1)

    def test_put_two_records_both_ok(self):
        self.stub.Put(PutRequest(record=make_record(id="rec-1")))
        resp = self.stub.Put(PutRequest(record=make_record(id="rec-2")))
        self.assertTrue(resp.ok)

    def test_search_returns_hit_after_put(self):
        self.stub.Put(PutRequest(record=make_record()))
        resp = self.stub.Search(SearchRequest(embedding=EMBEDDING))
        self.assertGreater(len(resp.hits), 0)

    def test_search_returns_correct_record_id(self):
        self.stub.Put(PutRequest(record=make_record()))
        resp = self.stub.Search(SearchRequest(embedding=EMBEDDING))
        self.assertEqual(resp.hits[0].id, "test-record-001")

    def test_search_vectors_searched_is_nonzero(self):
        self.stub.Put(PutRequest(record=make_record()))
        resp = self.stub.Search(SearchRequest(embedding=EMBEDDING))
        self.assertGreater(resp.vectors_searched, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)