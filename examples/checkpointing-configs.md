# Checkpointing Strategy Configuration Examples

This document shows how to configure different checkpointing strategies in Styx.

## Coordinated Checkpointing (Default)

Coordinated checkpointing ensures global consistency by having all workers take snapshots simultaneously.

```yaml
# docker-compose.yml
services:
  worker:
    environment:
      - CHECKPOINTING_STRATEGY=COORDINATED
      - SNAPSHOT_FREQUENCY_SEC=10
```

**Benefits:**
- Global consistency guarantees
- Coordinated recovery points
- Simpler recovery logic

**Use Cases:**
- Strong consistency requirements
- Small to medium clusters
- Applications requiring global consistency

## Uncoordinated Checkpointing

Uncoordinated checkpointing allows workers to take snapshots independently for higher availability.

```yaml
# docker-compose.yml
services:
  worker:
    environment:
      - CHECKPOINTING_STRATEGY=UNCOORDINATED
      - SNAPSHOT_FREQUENCY_SEC=5.0
```

**Benefits:**
- Higher availability
- Independent worker checkpointing
- Lower latency during normal operation
- No global coordination overhead

**Use Cases:**
- High availability requirements
- Large clusters
- Applications tolerant of eventual consistency

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `CHECKPOINTING_STRATEGY` | `COORDINATED` | Strategy: `COORDINATED` or `UNCOORDINATED` |
| `SNAPSHOT_FREQUENCY_SEC` | `10` | Snapshot frequency for both strategies (seconds) |

## Quick Switch Examples

### Switch to Uncoordinated Checkpointing

```bash
# Method 1: Environment variable
export CHECKPOINTING_STRATEGY=UNCOORDINATED
docker-compose up

# Method 2: Docker Compose override
# docker-compose.override.yml
services:
  worker:
    environment:
      - CHECKPOINTING_STRATEGY=UNCOORDINATED
      - SNAPSHOT_FREQUENCY_SEC=5.0
```

### Switch to Coordinated Checkpointing

```bash
# Method 1: Environment variable
export CHECKPOINTING_STRATEGY=COORDINATED
docker-compose up

# Method 2: Docker Compose override
# docker-compose.override.yml
services:
  worker:
    environment:
      - CHECKPOINTING_STRATEGY=COORDINATED
      - SNAPSHOT_FREQUENCY_SEC=15
```

### Customize Settings
```bash
# Adjust snapshot intervals
export CHECKPOINTING_STRATEGY=UNCOORDINATED
export SNAPSHOT_FREQUENCY_SEC=2.0
docker-compose up
```

## Performance Considerations

### Coordinated Checkpointing
- **Latency**: Higher due to global synchronization
- **Throughput**: May be reduced during snapshot coordination
- **Storage**: More efficient due to coordinated compaction
- **Recovery**: Faster and more predictable

### Uncoordinated Checkpointing
- **Latency**: Lower during normal operation
- **Throughput**: Higher due to no coordination overhead
- **Storage**: Potentially higher due to more delta files
- **Recovery**: More complex but allows partial recovery

## Monitoring

Both strategies provide logging to monitor checkpointing behavior:

```bash
# View checkpointing logs
docker-compose logs worker | grep -i snapshot

# Coordinated checkpointing logs
# "Taking COORDINATED snapshot at epoch: 42"

# Uncoordinated checkpointing logs  
# "Worker 1 completed uncoordinated snapshot 5 in 45.23ms"
``` 