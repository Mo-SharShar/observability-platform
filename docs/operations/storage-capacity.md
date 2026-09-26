# Storage and Capacity

## Purpose

This document describes the current storage baseline of the observability platform and the main storage areas used by the telemetry backends.

Storage monitoring is important because metrics, logs, and traces continuously generate data that must be retained and served by the observability backends.

The current lab uses:

- Grafana Mimir for metrics
- Grafana Loki for logs
- Grafana Tempo for traces

## Storage Architecture

```text
Payment API / Kubernetes
          │
          ├──────── Metrics ────────► Mimir
          │
          ├──────── Logs ───────────► Loki
          │
          └──────── Traces ─────────► Tempo
                                      │
                                      ▼
                                  Local Storage
```

Each backend maintains its own storage structures and lifecycle.

The storage layer is therefore distributed across the telemetry backends rather than being stored inside Grafana itself.

## Current Storage Baseline

The observed storage baseline in the lab environment is approximately:

| Backend / Area | Approximate Usage |
|---|---:|
| Mimir | ~194 MB |
| Loki | ~102 MB |
| Tempo | ~800 MB |
| Host root filesystem | ~27 GB used |

The host filesystem has approximately:

```text
Total:      48 GB
Used:       27 GB
Available:  19 GB
Usage:      ~60%
```

These values represent the observed lab baseline at the time of measurement and should not be treated as fixed capacity limits.

## Mimir Storage

The observed Mimir storage footprint was approximately:

```text
Total Mimir footprint: ~194 MB

Blocks:     ~112 MB
TSDB:        ~82 MB
Compactor:   ~124 KB
```

The main storage areas represent different parts of Mimir's metrics storage and processing state.

Conceptually:

```text
Metrics
   │
   ▼
Mimir
   │
   ├── TSDB data
   ├── Blocks
   └── Compactor state
```

Mimir is therefore one of the storage consumers that must be monitored as metrics volume increases.

## Loki Storage

The observed Loki storage footprint was approximately:

```text
Total Loki footprint: ~102 MB

Chunks / fake:       ~57 MB
WAL:                  ~45 MB
Chunks / index:      ~1.2 MB
```

Loki stores log data in chunks and maintains additional state such as the write-ahead log.

Conceptually:

```text
Application Logs
      │
      ▼
     Loki
      │
      ├── Chunks
      ├── Index
      └── WAL
```

The relative size of these areas can change as log volume and workload characteristics change.

## Tempo Storage

The observed Tempo storage footprint was approximately:

```text
Total Tempo footprint: ~800 MB

Blocks:       ~791 MB
Live-store:   ~7.3 MB
WAL:          ~8 KB
```

Tempo was the largest telemetry backend by observed storage footprint in the current lab baseline.

The main storage areas include trace blocks and live-store data.

Conceptually:

```text
Application Traces
       │
       ▼
     Tempo
       │
       ├── Blocks
       ├── Live store
       └── WAL
```

Trace storage can grow significantly depending on trace volume, sampling, and retention configuration.

## Host Filesystem

The observability backends are running in the lab environment with their data ultimately consuming host filesystem capacity.

The observed host baseline was:

```text
48 GB total
27 GB used
19 GB available
~60% usage
```

The host filesystem therefore needs to be monitored independently from the individual backend storage measurements.

The distinction is:

```text
Backend storage
      │
      ▼
Application data footprint
      │
      ▼
Host filesystem
      │
      ▼
Available disk capacity
```

A backend may appear healthy while the underlying host filesystem is approaching capacity.

## Storage Monitoring

The storage dashboard is named:

```text
Observability Platform — Storage & Capacity
```

The purpose of the dashboard is to provide visibility into:

- backend storage usage
- storage growth
- filesystem capacity
- major telemetry storage consumers
- capacity-related operational risk

The dashboard complements the self-monitoring dashboard.

Self-monitoring focuses primarily on telemetry pipeline health, while storage monitoring focuses on capacity and data growth.

## Capacity Investigation Workflow

A storage investigation can follow this process:

```text
Storage usage increase
        │
        ▼
Identify affected backend
        │
        ├── Mimir
        ├── Loki
        └── Tempo
        │
        ▼
Inspect backend storage areas
        │
        ▼
Check host filesystem
        │
        ▼
Assess growth and available capacity
```

The investigation should distinguish between:

- application telemetry growth
- backend internal state
- host filesystem consumption

## Retention Considerations

Retention is an important capacity-management concern for observability systems.

The current lab does not document a successfully configured seven-day Mimir retention policy.

An attempted `blocks_retention_period` configuration was not supported by the Mimir 3.2.0 configuration used in the lab and was removed.

Therefore, this project documents the observed storage baseline rather than claiming a specific Mimir retention policy.

A production deployment would need an explicitly validated retention and lifecycle strategy appropriate for its storage architecture and operational requirements.

## Storage Growth

Telemetry storage is workload-dependent.

Growth is influenced by factors such as:

```text
Metrics
  ├── number of active series
  └── scrape frequency

Logs
  ├── log volume
  ├── label cardinality
  └── application verbosity

Traces
  ├── request volume
  ├── span volume
  └── sampling strategy
```

Consequently, the current storage numbers should be treated as a baseline for this lab rather than a prediction of future capacity requirements.

## Capacity Risks

The main capacity risks in the current architecture include:

### Host Disk Exhaustion

```text
Telemetry growth
      ↓
Host filesystem growth
      ↓
Reduced free space
      ↓
Potential backend impact
```

### Trace Storage Growth

Tempo currently represents the largest observed backend footprint in the lab.

Increasing trace volume can therefore have a significant effect on overall storage consumption.

### Log Growth

High application log volume can increase Loki's chunk and WAL usage.

### Metrics Growth

Increasing metric cardinality and series count can increase Mimir's storage requirements.

## Operational Recommendations

For a larger deployment, capacity management should include:

- defined retention policies
- storage growth monitoring
- filesystem alerts
- backend-specific capacity thresholds
- regular capacity reviews
- appropriate storage scaling
- validated backup and recovery procedures

These are operational considerations for extending the lab toward a production-oriented architecture.

## Verification

The storage baseline was measured from the running observability environment.

The observed values were recorded for:

- Mimir
- Loki
- Tempo
- the host root filesystem

The measurements provide a reference point for future capacity observations.

They should be re-measured after significant changes to telemetry volume, retention, storage configuration, or backend architecture.

## Summary

The current storage baseline is approximately:

```text
Mimir  → ~194 MB
Loki   → ~102 MB
Tempo  → ~800 MB
Host   → ~27 GB used / 48 GB total
```

The storage responsibility is distributed across the telemetry backends:

```text
Metrics ──► Mimir
Logs    ──► Loki
Traces  ──► Tempo
              │
              ▼
        Host filesystem
```

Storage monitoring is therefore an important part of operating the observability platform because telemetry growth directly affects backend and host capacity.
