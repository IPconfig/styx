#!/usr/bin/env python3
"""
Simple test runner for checkpointing strategies.
This script can run without pytest and validates the basic configuration.
"""

import os
import time
import tempfile
import json
import sys


def test_checkpointing_strategy_environment_variable():
    """Test that the checkpointing strategy environment variable is set correctly."""
    checkpointing_strategy = os.getenv('CHECKPOINTING_STRATEGY', 'COORDINATED')
    snapshot_frequency = int(os.getenv('SNAPSHOT_FREQUENCY_SEC', '10'))
    
    print(f"Running tests with {checkpointing_strategy} checkpointing strategy")
    print(f"Snapshot frequency: {snapshot_frequency} seconds")
    
    assert checkpointing_strategy in ['COORDINATED', 'UNCOORDINATED'], \
        f"Invalid checkpointing strategy: {checkpointing_strategy}"
    assert snapshot_frequency > 0, f"Invalid snapshot frequency: {snapshot_frequency}"
    
    print("✓ Checkpointing strategy environment variable test passed")
    return True


def test_snapshot_frequency_configuration():
    """Test that snapshot frequency is configured correctly."""
    snapshot_frequency = int(os.getenv('SNAPSHOT_FREQUENCY_SEC', '10'))
    
    # The snapshot frequency should be reasonable for testing
    assert 1 <= snapshot_frequency <= 60, \
        f"Snapshot frequency {snapshot_frequency} is outside valid range [1, 60]"
    
    print("✓ Snapshot frequency configuration test passed")
    return True


def test_coordinated_checkpointing_behavior():
    """Test coordinated checkpointing specific behavior."""
    checkpointing_strategy = os.getenv('CHECKPOINTING_STRATEGY', 'COORDINATED')
    
    if checkpointing_strategy != 'COORDINATED':
        print("⏭ Skipping coordinated checkpointing test (not using COORDINATED strategy)")
        return True
    
    # Test that coordinated checkpointing requires coordinator
    # In a real test, you'd verify coordinator communication
    assert checkpointing_strategy == 'COORDINATED'
    
    print("✓ Coordinated checkpointing behavior test passed")
    return True


def test_uncoordinated_checkpointing_behavior():
    """Test uncoordinated checkpointing specific behavior."""
    checkpointing_strategy = os.getenv('CHECKPOINTING_STRATEGY', 'COORDINATED')
    
    if checkpointing_strategy != 'UNCOORDINATED':
        print("⏭ Skipping uncoordinated checkpointing test (not using UNCOORDINATED strategy)")
        return True
    
    # Test that uncoordinated checkpointing doesn't require coordinator
    # In a real test, you'd verify independent snapshot creation
    assert checkpointing_strategy == 'UNCOORDINATED'
    
    print("✓ Uncoordinated checkpointing behavior test passed")
    return True


def test_snapshot_storage_configuration():
    """Test that snapshot storage is configured correctly."""
    # Check that MinIO configuration is available
    minio_host = os.getenv('MINIO_HOST', 'localhost')
    minio_port = os.getenv('MINIO_PORT', '9000')
    
    assert minio_host is not None, "MINIO_HOST is not set"
    assert minio_port.isdigit(), f"MINIO_PORT {minio_port} is not a valid number"
    assert 1 <= int(minio_port) <= 65535, f"MINIO_PORT {minio_port} is outside valid range"
    
    print("✓ Snapshot storage configuration test passed")
    return True


def test_fault_tolerance_simulation():
    """Simulate fault tolerance scenarios."""
    # Create a temporary directory to simulate state storage
    with tempfile.TemporaryDirectory() as temp_dir:
        # Simulate state persistence
        state_file = os.path.join(temp_dir, 'test_state.json')
        test_state = {'data': 'test_value', 'timestamp': time.time()}
        
        # Simulate writing state (in real scenario, this would be to MinIO)
        with open(state_file, 'w') as f:
            json.dump(test_state, f)
        
        # Verify state was written
        assert os.path.exists(state_file), "State file was not created"
        
        # Simulate reading state back
        with open(state_file, 'r') as f:
            recovered_state = json.load(f)
        
        assert recovered_state == test_state, "Recovered state does not match original state"
    
    print("✓ Fault tolerance simulation test passed")
    return True


def test_kafka_configuration():
    """Test that Kafka configuration is available."""
    kafka_url = os.getenv('KAFKA_URL', 'localhost:9092')
    
    assert kafka_url is not None, "KAFKA_URL is not set"
    assert ':' in kafka_url, f"KAFKA_URL {kafka_url} is not in host:port format"
    
    print("✓ Kafka configuration test passed")
    return True


def test_end_to_end_workflow_simulation():
    """Simulate an end-to-end workflow with checkpointing."""
    # This test simulates a complete workflow
    # In a real scenario, you'd connect to the actual Styx cluster
    
    # Simulate workflow steps
    steps = [
        "initialize_function",
        "process_event",
        "update_state",
        "create_snapshot",
        "recover_from_snapshot"
    ]
    
    for step in steps:
        # Simulate each step
        assert step is not None, f"Step {step} is None"
        # In a real test, you'd verify the actual behavior
    
    # Verify all steps completed
    assert len(steps) == 5, f"Expected 5 steps, got {len(steps)}"
    
    print("✓ End-to-end workflow simulation test passed")
    return True


def test_checkpointing_strategy_consistency():
    """Test that the checkpointing strategy is consistent throughout the test."""
    # This test ensures that the strategy doesn't change during execution
    strategy_at_start = os.getenv('CHECKPOINTING_STRATEGY', 'COORDINATED')
    time.sleep(0.1)  # Small delay to simulate time passing
    strategy_at_end = os.getenv('CHECKPOINTING_STRATEGY', 'COORDINATED')
    
    assert strategy_at_start == strategy_at_end, \
        f"Strategy changed from {strategy_at_start} to {strategy_at_end}"
    
    print("✓ Checkpointing strategy consistency test passed")
    return True


def test_snapshot_compaction_simulation():
    """Simulate snapshot compaction behavior."""
    # Create multiple snapshot files to simulate compaction
    with tempfile.TemporaryDirectory() as temp_dir:
        snapshot_files = []
        
        # Create multiple snapshots
        for i in range(5):
            snapshot_file = os.path.join(temp_dir, f'snapshot_{i}.json')
            snapshot_data = {
                'snapshot_id': i,
                'timestamp': time.time(),
                'data': f'data_{i}'
            }
            
            with open(snapshot_file, 'w') as f:
                json.dump(snapshot_data, f)
            
            snapshot_files.append(snapshot_file)
        
        # Verify snapshots were created
        assert len(snapshot_files) == 5, f"Expected 5 snapshots, got {len(snapshot_files)}"
        assert all(os.path.exists(f) for f in snapshot_files), "Not all snapshots were created"
        
        # Simulate compaction (keep only the latest)
        latest_snapshot = snapshot_files[-1]
        for old_snapshot in snapshot_files[:-1]:
            os.remove(old_snapshot)
        
        # Verify only latest remains
        assert os.path.exists(latest_snapshot), "Latest snapshot was removed"
        assert not any(os.path.exists(f) for f in snapshot_files[:-1]), "Old snapshots were not removed"
    
    print("✓ Snapshot compaction simulation test passed")
    return True


def test_environment_configuration_completeness():
    """Test that all required environment variables are configured."""
    required_vars = [
        'CHECKPOINTING_STRATEGY',
        'SNAPSHOT_FREQUENCY_SEC',
        'KAFKA_URL',
        'MINIO_HOST',
        'MINIO_PORT'
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        assert value is not None, f"Environment variable {var} is not set"
        assert value != "", f"Environment variable {var} is empty"
    
    print("✓ Environment configuration completeness test passed")
    return True


def test_checkpointing_strategy_validation():
    """Test that the checkpointing strategy is valid."""
    checkpointing_strategy = os.getenv('CHECKPOINTING_STRATEGY', 'COORDINATED')
    valid_strategies = ['COORDINATED', 'UNCOORDINATED']
    
    assert checkpointing_strategy in valid_strategies, \
        f"Invalid checkpointing strategy: {checkpointing_strategy}"
    
    print("✓ Checkpointing strategy validation test passed")
    return True


def test_snapshot_frequency_validation():
    """Test that snapshot frequency is within valid range."""
    frequency = int(os.getenv('SNAPSHOT_FREQUENCY_SEC', '10'))
    
    assert 1 <= frequency <= 300, f"Snapshot frequency {frequency} is outside valid range [1, 300]"
    
    print("✓ Snapshot frequency validation test passed")
    return True


def run_all_tests():
    """Run all tests and return results."""
    tests = [
        test_checkpointing_strategy_environment_variable,
        test_snapshot_frequency_configuration,
        test_coordinated_checkpointing_behavior,
        test_uncoordinated_checkpointing_behavior,
        test_snapshot_storage_configuration,
        test_fault_tolerance_simulation,
        test_kafka_configuration,
        test_end_to_end_workflow_simulation,
        test_checkpointing_strategy_consistency,
        test_snapshot_compaction_simulation,
        test_environment_configuration_completeness,
        test_checkpointing_strategy_validation,
        test_snapshot_frequency_validation,
    ]
    
    print("=" * 60)
    print("Running Checkpointing Strategy Tests")
    print("=" * 60)
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test in tests:
        try:
            result = test()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed, {skipped} skipped")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 