import pathlib
import sys
import unittest

from project2_pb2 import (
	Centroid,
	PutRequest,
	Record,
	SearchHit,
	SearchLocalRequest,
	SearchLocalResponse,
	SearchRequest,
	SplitPartitionRequest,
	StoreRecordRequest,
	StoreRecordResponse,
)

from controller.controller import ControllerService
from storage_node.node import StorageNodeService

class ControllerTestSetup(unittest.TestCase):
	def setUp(self):
		pass

class TestPut(ControllerTestSetup):
	def test_put(self):
		pass

class TestSearch(ControllerTestSetup):
	def test_search(self):
		pass


class StorageNodeTestSetup(unittest.TestCase):
	def setUp(self):
		pass


class TestStoreRecord(StorageNodeTestSetup):
	def test_store_record(self):
		pass


class TestSearchLocal(StorageNodeTestSetup):
	def test_search_local(self):
		pass


class TestSplitPartition(StorageNodeTestSetup):
	def test_split_partition(self):
		pass


if __name__ == "__main__":
	unittest.main()
