#!/bin/bash

# Test runner script for Styx with Docker Compose
# Usage: ./scripts/run_tests.sh [COORDINATED|UNCOORDINATED] [test_pattern]

set -e

# Default values
CHECKPOINTING_STRATEGY=${1:-COORDINATED}
TEST_PATTERN=${2:-""}
SNAPSHOT_FREQUENCY_SEC=${3:-10}

echo "Running tests with checkpointing strategy: $CHECKPOINTING_STRATEGY"
echo "Snapshot frequency: $SNAPSHOT_FREQUENCY_SEC seconds"
echo "Test pattern: $TEST_PATTERN"

# Create test results directory
mkdir -p test_results

# Clean up any existing containers
echo "Cleaning up existing containers..."
docker compose -f docker-compose.test.yml down -v 2>/dev/null || true

# Build and start the test environment
echo "Building and starting test environment..."
export CHECKPOINTING_STRATEGY=$CHECKPOINTING_STRATEGY
export SNAPSHOT_FREQUENCY_SEC=$SNAPSHOT_FREQUENCY_SEC

# Start infrastructure services first
echo "Starting infrastructure services..."
docker compose -f docker-compose.test.yml up -d kafka zookeeper minio

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Start coordinator
echo "Starting coordinator..."
docker compose -f docker-compose.test.yml up -d coordinator

# Wait for coordinator to be ready
echo "Waiting for coordinator to be ready..."
sleep 5

# Run tests
echo "Running tests..."
docker compose -f docker-compose.test.yml run --rm test-runner

# Check test results
if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed!"
fi

# Clean up
echo "Cleaning up..."
docker compose -f docker-compose.test.yml down -v

echo "Tests completed!" 