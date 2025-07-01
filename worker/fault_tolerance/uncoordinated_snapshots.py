import io
import socket
import time
from typing import Iterable

from minio import Minio

from styx.common.logging import logging
from styx.common.message_types import MessageType
from styx.common.serialization import msgpack_serialization, msgpack_deserialization
from styx.common.tcp_networking import NetworkingManager
from styx.common.types import OperatorPartition, KVPairs
from styx.common.serialization import Serializer

from worker.fault_tolerance.base_snapshoter import BaseSnapshotter

# Environment variables for MinIO configuration
import os

MINIO_URL: str = f"{os.environ['MINIO_HOST']}:{os.environ['MINIO_PORT']}"
MINIO_ACCESS_KEY: str = os.environ['MINIO_ROOT_USER']
MINIO_SECRET_KEY: str = os.environ['MINIO_ROOT_PASSWORD']
SNAPSHOT_BUCKET_NAME: str = os.getenv('SNAPSHOT_BUCKET_NAME', "styx-snapshots")
COORDINATOR_HOST: str = os.environ['DISCOVERY_HOST']
COORDINATOR_PORT: int = int(os.environ['DISCOVERY_PORT'])


class UncoordinatedSnapshotsMinio(BaseSnapshotter):
    """
    Uncoordinated snapshotter that allows workers to take snapshots independently
    without waiting for global coordination. Each worker maintains its own
    snapshot sequence and can checkpoint at any time.
    """

    def __init__(self, worker_id: int, n_assigned_partitions: int):
        self.worker_id: int = worker_id
        self.snapshot_id: int = 0
        self.n_assigned_partitions: int = n_assigned_partitions
        self.completed_snapshots: int = 0
        self.snapshot_in_progress: bool = False
        self.snapshot_start: float = 0.0
        self.current_input_offsets = None
        self.current_output_offsets = None
        self.current_epoch_counter = -1
        self.current_t_counter = -1
        self.last_snapshot_time: float = 0.0
        self.snapshot_interval: float = float(os.getenv('SNAPSHOT_FREQUENCY_SEC', 10.0))

    def snapshot_completed_callback(self, _, ):
        """Callback when a snapshot is completed - no coordinator notification needed"""
        self.completed_snapshots += 1
        if self.completed_snapshots == self.n_assigned_partitions:
            snapshot_end = time.time() * 1000
            logging.info(f"Worker {self.worker_id} completed uncoordinated snapshot {self.snapshot_id} "
                        f"in {snapshot_end - self.snapshot_start:.2f}ms")
            
            # Optionally notify coordinator for monitoring purposes (non-blocking)
            self._notify_coordinator_async(snapshot_end)
            
            self.snapshot_id += 1
            self.snapshot_in_progress = False
            self.completed_snapshots = 0
            self.last_snapshot_time = time.time()

    def _notify_coordinator_async(self, snapshot_end: float):
        """Asynchronously notify coordinator about snapshot completion (non-blocking)"""
        try:
            msg = NetworkingManager.encode_message(
                msg=(self.worker_id, self.snapshot_id, "UNCOORDINATED",
                     self.snapshot_start, snapshot_end,
                     self.current_input_offsets, self.current_output_offsets,
                     self.current_epoch_counter, self.current_t_counter),
                msg_type=MessageType.SnapID,
                serializer=Serializer.MSGPACK
            )
            # Use a separate thread to avoid blocking
            import threading
            def send_notification():
                try:
                    s = socket.socket()
                    s.connect((COORDINATOR_HOST, COORDINATOR_PORT))
                    s.send(msg)
                    s.close()
                except Exception as e:
                    logging.debug(f"Failed to notify coordinator of uncoordinated snapshot: {e}")
            
            threading.Thread(target=send_notification, daemon=True).start()
        except Exception as e:
            logging.debug(f"Error in coordinator notification: {e}")

    def should_take_snapshot(self) -> bool:
        """Determine if it's time to take a snapshot based on local timing"""
        return (time.time() - self.last_snapshot_time > self.snapshot_interval and 
                not self.snapshot_in_progress)

    def start_snapshotting(self,
                           current_input_offsets: dict[OperatorPartition, int],
                           current_output_offsets: dict[OperatorPartition, int],
                           current_epoch_counter: int,
                           current_t_counter: int):
        """Start the snapshotting process"""
        self.snapshot_in_progress = True
        self.snapshot_start = time.time() * 1000
        self.current_input_offsets = current_input_offsets
        self.current_output_offsets = current_output_offsets
        self.current_epoch_counter = current_epoch_counter
        self.current_t_counter = current_t_counter

    @staticmethod
    def store_snapshot(snapshot_id: int,
                       snapshot_name: str,
                       data_to_snapshot: tuple):
        """Store snapshot data to MinIO"""
        minio_client: Minio = Minio(MINIO_URL, access_key=MINIO_ACCESS_KEY, 
                                   secret_key=MINIO_SECRET_KEY, secure=False)
        sn_data: bytes = msgpack_serialization(data_to_snapshot)
        minio_client.put_object(SNAPSHOT_BUCKET_NAME, snapshot_name, 
                               io.BytesIO(sn_data), len(sn_data))
        return True

    def retrieve_snapshot(self, snapshot_id: int, registered_operators: Iterable[OperatorPartition]):
        """Retrieve snapshot data - similar to coordinated version but worker-specific"""
        self.snapshot_id = snapshot_id + 1
        if snapshot_id == -1:
            return {}, None, None, 0, 0

        minio_client: Minio = Minio(MINIO_URL, access_key=MINIO_ACCESS_KEY, 
                                   secret_key=MINIO_SECRET_KEY, secure=False)

        data: dict[OperatorPartition, KVPairs] = {}

        for operator_partition in registered_operators:
            operator_name, partition = operator_partition
            # Get the delta files for this specific worker
            snapshot_files: list[str] = [
                sn_file.object_name
                for sn_file in minio_client.list_objects(
                    bucket_name=SNAPSHOT_BUCKET_NAME,
                    prefix=f"uncoordinated/{self.worker_id}/{operator_name}/{partition}/",
                    recursive=True
                )
                if sn_file.object_name.endswith(".bin")
            ]
            
            snapshot_merge_order: list[tuple[int, str]] = sorted([
                (int(snapshot_file.split("/")[-1].split(".")[0]), snapshot_file)
                for snapshot_file in snapshot_files
            ], key=lambda item: item[0])
            
            for sn_id, sn_name in snapshot_merge_order:
                if sn_id > snapshot_id:
                    # recover only from a stable snapshot
                    continue
                partition_data = msgpack_deserialization(
                    minio_client.get_object(SNAPSHOT_BUCKET_NAME, sn_name).data
                )
                if operator_partition in data and partition_data:
                    data[operator_partition].update(partition_data)
                else:
                    data[operator_partition] = partition_data

        # Retrieve worker-specific sequencer metadata
        sequencer_snapshot_files: list[str] = [
            sn_file.object_name
            for sn_file in minio_client.list_objects(
                bucket_name=SNAPSHOT_BUCKET_NAME,
                prefix=f"uncoordinated/{self.worker_id}/sequencer/",
                recursive=True
            )
            if sn_file.object_name.endswith(".bin")
        ]
        
        sequencer_merge_order: list[tuple[int, str]] = sorted([
            (int(snapshot_file.split("/")[-1].split(".")[0]), snapshot_file)
            for snapshot_file in sequencer_snapshot_files
        ], key=lambda item: item[0])
        
        topic_partition_offsets: dict[OperatorPartition, int] = {}
        topic_partition_output_offsets: dict[OperatorPartition, int] = {}
        epoch: int = 0
        t_counter: int = 0
        
        for sn_id, sn_name in sequencer_merge_order:
            if sn_id > snapshot_id:
                continue
            (topic_partition_offsets, topic_partition_output_offsets,
             epoch, t_counter) = msgpack_deserialization(
                minio_client.get_object(SNAPSHOT_BUCKET_NAME, sn_name).data
            )

        return data, topic_partition_offsets, topic_partition_output_offsets, epoch, t_counter

    def get_snapshot_path(self, operator_name: str, partition: int, snapshot_id: int) -> str:
        """Generate the path for uncoordinated snapshots"""
        return f"uncoordinated/{self.worker_id}/{operator_name}/{partition}/{snapshot_id}.bin"

    def get_sequencer_path(self, snapshot_id: int) -> str:
        """Generate the path for uncoordinated sequencer snapshots"""
        return f"uncoordinated/{self.worker_id}/sequencer/{snapshot_id}.bin" 