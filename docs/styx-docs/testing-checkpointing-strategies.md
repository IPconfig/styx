# Testing Checkpointing Strategies

This document explains how to run tests for both coordinated and uncoordinated checkpointing strategies in Styx using Docker Compose.

## Overview

The Styx system now supports two checkpointing strategies:
- **Coordinated Checkpointing** (original): Global coordination through the coordinator service
- **Uncoordinated Checkpointing** (new): Independent snapshot creation by each worker

## Prerequisites

- Docker and Docker Compose installed
- At least 4GB of available memory
- Ports 9092, 19092, 9000, 9001, 8886, 8000 available

## Quick Start

### 1. Run Tests with Coordinated Checkpointing (Original)

```bash
# Run all tests with coordinated checkpointing
./scripts/run_tests.sh COORDINATED

# Run with custom snapshot frequency
./scripts/run_tests.sh COORDINATED "" 5
```

### 2. Run Tests with Uncoordinated Checkpointing (New)

```bash
# Run all tests with uncoordinated checkpointing
./scripts/run_tests.sh UNCOORDINATED

# Run with custom snapshot frequency
./scripts/run_tests.sh UNCOORDINATED "" 15
```

### 3. Run Original Experiments

```bash
# Run YCSB-T experiment with coordinated checkpointing
./scripts/run_original_experiments.sh ycsbt

# Run TPC-C experiment with coordinated checkpointing
./scripts/run_original_experiments.sh tpcc 4 4 1000 60 results/tpcc_test 10 1000

# Run scalability experiments
./scripts/run_original_experiments.sh scalability
```

## Test Infrastructure

### Docker Compose Test Configuration

The test environment uses `docker-compose.test.yml` which includes:

- **Kafka**: Message broker for event streaming
- **Zookeeper**: Coordination service for Kafka
- **MinIO**: Object storage for snapshots
- **Coordinator**: Styx coordinator service
- **Test Runner**: Container for executing tests

### Environment Variables

| Variable | Description | Default | Values |
|----------|-------------|---------|--------|
| `CHECKPOINTING_STRATEGY` | Checkpointing strategy to use | `COORDINATED` | `COORDINATED`, `UNCOORDINATED` |
| `SNAPSHOT_FREQUENCY_SEC` | Snapshot frequency in seconds | `10` | `1-300` |
| `KAFKA_URL` | Kafka broker URL | `kafka:29092` | Host:port format |
| `MINIO_HOST` | MinIO host | `minio` | Hostname |
| `MINIO_PORT` | MinIO port | `9000` | Port number |

## Test Types

### 1. Configuration Tests

These tests validate that the environment is properly configured:

- Environment variable validation
- Checkpointing strategy validation
- Snapshot frequency validation
- Kafka configuration validation
- MinIO configuration validation

### 2. Strategy-Specific Tests

These tests validate behavior specific to each checkpointing strategy:

#### Coordinated Checkpointing Tests
- Verifies coordinator communication
- Tests global snapshot coordination
- Validates snapshot completion tracking

#### Uncoordinated Checkpointing Tests
- Verifies independent snapshot creation
- Tests local snapshot management
- Validates no coordinator dependency

### 3. Integration Tests

These tests validate end-to-end functionality:

- Fault tolerance simulation
- Snapshot compaction simulation
- End-to-end workflow simulation
- State persistence and recovery

## Running Tests Manually

### Using Docker Compose Directly

```bash
# Set environment variables
export CHECKPOINTING_STRATEGY=COORDINATED
export SNAPSHOT_FREQUENCY_SEC=10

# Start infrastructure
docker compose -f docker-compose.test.yml up -d kafka zookeeper minio

# Start coordinator
docker compose -f docker-compose.test.yml up -d coordinator

# Run tests
docker compose -f docker-compose.test.yml run --rm test-runner

# Clean up
docker compose -f docker-compose.test.yml down -v
```

### Using the Simple Test Runner

```bash
# Run tests directly
python tests/simple_test_runner.py
```

## Test Results

Test results are displayed in the console with the following format:

```
============================================================
Running Checkpointing Strategy Tests
============================================================
Running tests with COORDINATED checkpointing strategy
Snapshot frequency: 10 seconds
✓ Checkpointing strategy environment variable test passed
✓ Snapshot frequency configuration test passed
⏭ Skipping coordinated checkpointing test (not using COORDINATED strategy)
✓ Snapshot storage configuration test passed
...
============================================================
Test Results: 12 passed, 0 failed, 0 skipped
============================================================
```

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check if ports are in use
   lsof -i :9092 -i :9000 -i :8886
   
   # Stop conflicting services
   docker compose -f docker-compose.test.yml down -v
   ```

2. **Memory Issues**
   ```bash
   # Increase Docker memory limit
   # In Docker Desktop: Settings > Resources > Memory > 4GB
   ```

3. **Service Startup Issues**
   ```bash
   # Check service logs
   docker compose -f docker-compose.test.yml logs kafka
   docker compose -f docker-compose.test.yml logs minio
   docker compose -f docker-compose.test.yml logs coordinator
   ```

4. **Test Failures**
   ```bash
   # Run with verbose output
   docker compose -f docker-compose.test.yml run --rm test-runner python -u tests/simple_test_runner.py
   ```

### Debug Mode

To run tests in debug mode with more verbose output:

```bash
# Set debug environment variable
export DEBUG=true

# Run tests with debug output
./scripts/run_tests.sh COORDINATED
```

## Performance Testing

### Comparing Strategies

To compare performance between coordinated and uncoordinated checkpointing:

```bash
# Run coordinated checkpointing tests
./scripts/run_tests.sh COORDINATED
# Note the results

# Run uncoordinated checkpointing tests
./scripts/run_tests.sh UNCOORDINATED
# Compare the results
```

### Benchmarking

For performance benchmarking, use the original experiment scripts:

```bash
# Benchmark with coordinated checkpointing
./scripts/run_original_experiments.sh ycsbt 8 10000 8 0.8 5000 120 results/coordinated_bench 30 10

# Benchmark with uncoordinated checkpointing (modify scripts to use UNCOORDINATED)
export CHECKPOINTING_STRATEGY=UNCOORDINATED
./scripts/run_original_experiments.sh ycsbt 8 10000 8 0.8 5000 120 results/uncoordinated_bench 30 10
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Test Checkpointing Strategies

on: [push, pull_request]

jobs:
  test-coordinated:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Coordinated Tests
        run: ./scripts/run_tests.sh COORDINATED

  test-uncoordinated:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Uncoordinated Tests
        run: ./scripts/run_tests.sh UNCOORDINATED
```

## Best Practices

1. **Always clean up**: Use `docker compose down -v` to remove volumes
2. **Check resource usage**: Monitor CPU and memory during tests
3. **Use appropriate snapshot frequencies**: Lower frequencies for testing, higher for production
4. **Validate results**: Always check test output for failures
5. **Document changes**: Update this document when adding new tests

## Support

For issues with testing:

1. Check the troubleshooting section above
2. Review Docker and service logs
3. Verify environment configuration
4. Check system resources (CPU, memory, disk space)
5. Ensure all required ports are available 