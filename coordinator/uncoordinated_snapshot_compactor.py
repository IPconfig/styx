import io
import logging
import os
from collections import defaultdict

from minio import Minio
from styx.common.serialization import msgpack_deserialization, msgpack_serialization
from styx.common.types import OperatorPartition, KVPairs

MINIO_URL: str = f"{os.environ['MINIO_HOST']}:{os.environ['MINIO_PORT']}"
MINIO_ACCESS_KEY: str = os.environ['MINIO_ROOT_USER']
MINIO_SECRET_KEY: str = os.environ['MINIO_ROOT_PASSWORD']
SNAPSHOT_BUCKET_NAME: str = os.getenv('SNAPSHOT_BUCKET_NAME', "styx-snapshots")


def get_uncoordinated_snapshots_per_worker(snapshot_files: list[str],
                                           max_snap_id: int
                                           ) -> dict[int, dict[OperatorPartition, list[tuple[int, str]]]]:
    """
    Organize uncoordinated snapshots by worker ID and operator partition.
    
    Returns:
        dict[worker_id, dict[operator_partition, list[snapshot_id, file_path]]]
    """
    snapshots_per_worker: dict[int, dict[OperatorPartition, list[tuple[int, str]]]] = defaultdict(lambda: defaultdict(list))
    
    for sn_file in snapshot_files:
        if not sn_file.startswith("uncoordinated/"):
            continue
            
        parts = sn_file.split("/")
        if len(parts) < 5:
            continue
            
        # Format: uncoordinated/worker_id/operator_name/partition/snapshot_id.bin
        worker_id = int(parts[1])
        operator_name = parts[2]
        partition = int(parts[3])
        snapshot_id = int(parts[4].split(".")[0])
        
        if snapshot_id <= max_snap_id:
            operator_partition = (operator_name, partition)
            snapshots_per_worker[worker_id][operator_partition].append((snapshot_id, sn_file))
    
    # Sort snapshots by ID for each worker and operator partition
    for worker_id in snapshots_per_worker:
        for operator_partition in snapshots_per_worker[worker_id]:
            snapshots_per_worker[worker_id][operator_partition].sort(key=lambda x: x[0])
    
    return snapshots_per_worker


def compact_uncoordinated_deltas(minio_client, snapshot_files, max_snap_id):
    """
    Compact uncoordinated snapshots by merging delta files for each worker.
    """
    snapshots_per_worker = get_uncoordinated_snapshots_per_worker(snapshot_files, max_snap_id)
    logging.warning(f"Compacting uncoordinated snapshots for {len(snapshots_per_worker)} workers")
    
    snapshots_to_delete: list[str] = []
    
    for worker_id, worker_snapshots in snapshots_per_worker.items():
        logging.info(f"Compacting snapshots for worker {worker_id}")
        
        for operator_partition, snapshots in worker_snapshots.items():
            if len(snapshots) <= 1:
                continue  # No compaction needed
                
            operator_name, partition = operator_partition
            data: KVPairs = {}
            
            # Merge all delta files for this operator partition
            for sn_id, sn_name in snapshots:
                partition_data = msgpack_deserialization(
                    minio_client.get_object(SNAPSHOT_BUCKET_NAME, sn_name).data
                )
                if partition_data:
                    data.update(partition_data)
                snapshots_to_delete.append(sn_name)
            
            # Store the merged snapshot as the new base (snapshot 0)
            if data:
                merged_snapshot_path = f"uncoordinated/{worker_id}/{operator_name}/{partition}/0.bin"
                sn_data: bytes = msgpack_serialization(data)
                minio_client.put_object(SNAPSHOT_BUCKET_NAME, merged_snapshot_path, 
                                       io.BytesIO(sn_data), len(sn_data))
                logging.info(f"Created merged snapshot: {merged_snapshot_path}")
    
    # Cleanup old delta files
    if snapshots_to_delete:
        logging.warning(f"Deleting {len(snapshots_to_delete)} uncoordinated delta files")
        cleanup_compacted_files(minio_client, [], snapshots_to_delete)


def cleanup_compacted_files(minio_client, sequencer_files_to_delete: list[str], data_files_to_delete: list[str]):
    """Delete compacted files from MinIO"""
    try:
        for file_path in sequencer_files_to_delete + data_files_to_delete:
            minio_client.remove_object(SNAPSHOT_BUCKET_NAME, file_path)
            logging.debug(f"Deleted: {file_path}")
    except Exception as e:
        logging.error(f"Error cleaning up compacted files: {e}")


def start_uncoordinated_snapshot_compaction(max_snap_id: int):
    """Start the uncoordinated snapshot compaction process"""
    try:
        minio_client: Minio = Minio(MINIO_URL, access_key=MINIO_ACCESS_KEY, 
                                   secret_key=MINIO_SECRET_KEY, secure=False)
        
        # List all snapshot files
        snapshot_files: list[str] = [
            sn_file.object_name
            for sn_file in minio_client.list_objects(bucket_name=SNAPSHOT_BUCKET_NAME, recursive=True)
            if sn_file.object_name.endswith(".bin")
        ]
        
        compact_uncoordinated_deltas(minio_client, snapshot_files, max_snap_id)
        logging.warning(f"Uncoordinated snapshot compaction completed for snapshot {max_snap_id}")
        
    except Exception as e:
        logging.error(f"Error in uncoordinated snapshot compaction: {e}")
        raise 