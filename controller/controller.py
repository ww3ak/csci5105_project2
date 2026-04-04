from concurrent import futures
import threading

import grpc
from project2_pb2 import *
import project2_pb2_grpc
from utils.config import CONTROLLER_PORT, NODE_PORT
from utils.utils import choose_closest_node, create_storage_node, cosine_similarity
# Import cosine_similarity for extra credit emplemtnation of multi node repartitioning


MAX_VECTORS_PER_NODE = 1000

# Threshold added for extra credit implementation of multi node repartitioning 
# Controls when a query is considered "near a boundary."
SIMILARITY_GAP_THRESHOLD = 0.05

class ControllerService(project2_pb2_grpc.ControllerServiceServicer):
    def __init__(self) -> None:
        self.repartitioning: bool = False
        self.next_node_num: int = 2
        self.total_vectors: int = 0
        self.nodes: list[dict[str, str | list[float]]] = [
            {
                "target": f"storage-node-1:{NODE_PORT}",
                "centroid": [],
            }
        ]

    def _run_split(self, old_target: str, new_node_num: int) -> None:
        try:
            new_target: str = create_storage_node(new_node_num)
            with grpc.insecure_channel(old_target) as channel:
                stub = project2_pb2_grpc.StorageNodeServiceStub(channel)
                response: SplitPartitionResponse = stub.SplitPartition(
                    SplitPartitionRequest(new_node_target=new_target)
                )

            self.nodes = [node for node in self.nodes if node["target"] != old_target]
            self.nodes.append(
                {
                    "target": response.old_target,
                    "centroid": list(response.old_centroid.values),
                }
            )
            self.nodes.append(
                {
                    "target": response.new_target,
                    "centroid": list(response.new_centroid.values),
                }
            )
        finally:
            self.repartitioning = False

    def Put(self, request: PutRequest, context: grpc.ServicerContext) -> PutResponse:
        # TODO:
        # High-level steps:
        # 1. Choose the closest node for request.record.embedding by calling:
        #       choose_closest_node(self.nodes, list(request.record.embedding))
        closest_node = choose_closest_node(self.nodes, list(request.record.embedding))
        # need target for stub chanel
        target = closest_node["target"]
        # 2. Open a gRPC channel to that node's target and forward the request with:
        #       StorageNodeServiceStub(...).StoreRecord(StoreRecordRequest(record=request.record))
        with grpc.insecure_channel(target) as channel:
            stub = project2_pb2_grpc.StorageNodeServiceStub(channel)
            response = stub.StoreRecord(StoreRecordRequest(record=request.record))
        # 3. Update self.total_vectors.
        self.total_vectors += 1
        # 4. Update the centroid stored in self.nodes for the node that handled the Put.
        for node in self.nodes:
            if node["target"] == target:
                node["centroid"] = list(response.centroid.values)
                break
        # 5. If the node's count exceeds MAX_VECTORS_PER_NODE and a split is not already running:
        #       - set self.repartitioning = True
        #       - choose the next node number
        #       - start a background thread that calls self._run_split(...)

        # dont want to get confused by last split
        split_triggered = False
        if response.count > MAX_VECTORS_PER_NODE and not self.repartitioning:
            self.repartitioning = True
            split_triggered = True
            new_node_num = self.next_node_num
            self.next_node_num += 1
            threading.Thread(target=self._run_split, args=(target, new_node_num)).start()
        
        # Controller blocks additional Put requests until forked thread completes repartitioning
        while self.repartitioning == True:
            pass

        return PutResponse(
            ok=response.ok,
            target=response.target,
            target_count=response.count,
            split_triggered=split_triggered,
        )

    def Search(
        self, request: SearchRequest, context: grpc.ServicerContext
    ) -> SearchLocalResponse:
        # TODO:
        # Implement the controller-side Search path.
        #
        # High-level steps:
        # 1. Convert the incoming embedding into a plain Python list:
        query_embedding = list(request.embedding)
        # 2. Choose the closest node by calling:
        closest_node = choose_closest_node(self.nodes, query_embedding)
        # need target for stub chanel
        target = closest_node["target"]
        # 3. Forward the search to that node with:
        #       StorageNodeServiceStub(...).SearchLocal(
        #           SearchLocalRequest(query_embedding=query_embedding, top_k=5)
        #       )
        with grpc.insecure_channel(target) as channel:
            stub = project2_pb2_grpc.StorageNodeServiceStub(channel)
            response = stub.SearchLocal(SearchLocalRequest(query_embedding=query_embedding, top_k=5))
        # 4. Return the SearchLocalResponse from that node.
        #
        # Note:
        # The proto returns SearchLocalResponse here, so you can directly return
        # the storage node's SearchLocal response object.
        return response
    
    # Extra credit implementation of a multi node repartitioning scheme
    # Uncomment to test!
    # def Search(        
    #         self, request: SearchRequest, context: grpc.ServicerContext
    # ) -> SearchLocalResponse:
    #     query_embedding = list(request.embedding)

    #     # First score all nodes by centroid similariy
    #     nodes_scores = []
    #     for node in self.nodes:
    #         if node["centroid"]:
    #             score = cosine_similarity(query_embedding, list(node["centroid"]))
    #             nodes_scores.append((node, score))

    #     # Fall back to do single node routing if only one node or no centroids
    #     if len(nodes_scores) < 2:
    #         if nodes_scores:
    #             target = nodes_scores[0][0]["target"]
    #         else:
    #             self.nodes[0]["target"]

    #         with grpc.insecure_channel(target) as channel:
    #             stub = project2_pb2_grpc.StorageNodeServiceStub(channel)
    #             return stub.SearchLocal(SearchLocalRequest(query_embedding=query_embedding, top_k=5))

    #     # Sort descending by similarity score
    #     nodes_scores.sort(key=lambda x: x[1], reverse=True)
    #     best_node, best_score = nodes_scores[0]
    #     second_node, second_score = nodes_scores[1]
    #     gap = best_score - second_score

    #     if gap > SIMILARITY_GAP_THRESHOLD:
    #         # Query clearly within partition -> single node routing
    #         with grpc.insecure_channel(best_node["target"]) as channel:
    #             stub = project2_pb2_grpc.StorageNodeServiceStub(channel)
    #             return stub.SearchLocal(SearchLocalRequest(query_embedding=query_embedding, top_k=5))
    #     else:
    #         # multi node! -> check top nodes and merge
    #         results = []
    #         total_vectors_searched = 0

    #         for node, _ in [nodes_scores[0], nodes_scores[1]]:
    #             with grpc.insecure_channel(node["target"]) as channel:
    #                 stub = project2_pb2_grpc.StorageNodeServiceStub(channel)
    #                 response = stub.SearchLocal(SearchLocalRequest(query_embedding=query_embedding, top_k=5))
    #             results.extend(response.hits)
    #             total_vectors_searched += response.vectors_searched

    #         # Merge and return global top-5
    #         merged = sorted(results, key=lambda h: h.score, reverse=True)[:5]
    #         return SearchLocalResponse(
    #             hits=merged,
    #             target=f"{best_node['target']}+{second_node['target']}",
    #             vectors_searched=total_vectors_searched,)


    def ClusterStatus(
        self, request: ClusterStatusRequest, context: grpc.ServicerContext
    ) -> ClusterStatusResponse:
        nodes_info: list[NodeInfo] = []
        for node in self.nodes:
            with grpc.insecure_channel(str(node["target"])) as channel:
                stub = project2_pb2_grpc.StorageNodeServiceStub(channel)
                stats: NodeStats = stub.GetNodeStats(GetNodeStatsRequest())

            node_info = NodeInfo(target=str(node["target"]))
            node_info.stats.CopyFrom(stats)
            nodes_info.append(node_info)

        return ClusterStatusResponse(nodes=nodes_info)


def serve() -> None:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=16))
    project2_pb2_grpc.add_ControllerServiceServicer_to_server(ControllerService(), server)
    server.add_insecure_port(f"[::]:{CONTROLLER_PORT}")
    server.start()
    print(f"Controller listening on {CONTROLLER_PORT}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
