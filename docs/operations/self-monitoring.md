# Observability Platform Self-Monitoring

## Purpose

The observability platform monitors its own telemetry collection and forwarding components.

Self-monitoring helps verify that the platform responsible for collecting, routing, and storing telemetry is itself healthy.

The dashboard focuses on Grafana Alloy and the telemetry paths connected to the observability backends.

## Self-Monitoring Architecture

```text
                    Observability Platform
                            │
                            ▼
                     Grafana Alloy
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
           Metrics         Logs         Traces
              │             │             │
              ▼             ▼             ▼
            Mimir          Loki         Tempo
```

Alloy exposes its own operational metrics.

The platform collects these metrics through an Alloy self-scrape pipeline and forwards them to Mimir.

This creates a feedback path where the observability platform can monitor the health of its own telemetry collection layer.

## Alloy Self-Scraping

Alloy exposes an HTTP metrics endpoint on:

```text
127.0.0.1:12345
```

The self-monitoring pipeline uses:

```text
Alloy
  │
  │ /metrics
  ▼
prometheus.scrape.alloy_self
  │
  ▼
prometheus.remote_write.mimir
  │
  ▼
Mimir
```

This allows Alloy's operational metrics to be queried from Mimir like other Prometheus-compatible metrics.

## Key Self-Monitoring Signals

The self-monitoring dashboard tracks several categories of platform health.

### 1. Alloy Component Health

The dashboard tracks the health of Alloy components.

A healthy component connection is represented by:

```text
alloy_component_graph_connection
```

A value of `1` indicates that the monitored component connection is healthy.

This helps identify broken or disconnected stages in the Alloy pipeline.

### 2. Scrape Targets

Alloy's Prometheus scrape pipeline exposes information about discovered and synchronized targets.

The self-monitoring dashboard tracks scrape-target health to identify problems with telemetry collection.

A target synchronization failure can be investigated through metrics such as:

```text
prometheus_target_sync_failed_total
```

A value of zero indicates that no target synchronization failures were observed for the monitored component during the observed period.

### 3. Samples Forwarded

The platform tracks the number of samples forwarded by Alloy.

An important metric is:

```text
prometheus_forwarded_samples_total
```

This provides visibility into whether collected Prometheus-compatible samples are successfully moving through the Alloy pipeline.

The metric is useful when investigating situations where scrape targets appear healthy but data is not reaching the metrics backend.

### 4. Mimir Remote Write

The dashboard tracks the remote-write path from Alloy to Mimir.

Important signals include:

- remote-write rate
- remote-write failures
- pending samples

These signals help identify problems between telemetry collection and the metrics storage backend.

Conceptually:

```text
Alloy
  │
  │ remote write
  ▼
Mimir
```

The monitoring objective is to detect failures or backlog in this path.

### 5. OTLP Spans

The tracing pipeline is monitored through Alloy's OTLP metrics.

The dashboard tracks:

- OTLP spans received
- OTLP spans failed

This provides visibility into the trace ingestion path:

```text
Payment API
     │
     │ OTLP
     ▼
Alloy
     │
     ▼
Tempo
```

A significant increase in failed spans can indicate an issue in the trace ingestion or forwarding pipeline.

### 6. Loki Entries

The logging pipeline is also monitored through Alloy metrics.

The dashboard tracks:

- Loki entries sent
- Loki entries dropped

The logging path is:

```text
Kubernetes logs
      │
      ▼
Alloy
      │
      ▼
Loki
```

Dropped entries can indicate a problem in the logging pipeline and should be investigated when observed.

## Self-Monitoring Dashboard

The dashboard is named:

```text
Observability Platform — Self Monitoring
```

The dashboard contains eleven monitoring panels:

1. Alloy Healthy Components
2. Alloy Scrape Targets
3. Samples Forwarded by Alloy
4. Mimir Remote Write Rate
5. Mimir Remote Write Failures
6. Remote Write Pending Samples
7. OTLP Spans Received
8. OTLP Spans Failed
9. Loki Entries Sent
10. Loki Entries Dropped
11. Alloy Self-Scrape Target

These panels provide a platform-level view of the telemetry collection and forwarding paths.

## Investigation Workflow

Self-monitoring supports an investigation flow such as:

```text
Telemetry problem
       │
       ▼
Self-monitoring dashboard
       │
       ├── Alloy health
       ├── Scrape targets
       ├── Remote write
       ├── OTLP
       └── Loki pipeline
              │
              ▼
       Identify failed stage
              │
              ▼
       Inspect Alloy configuration
              │
              ▼
       Check backend availability
```

This helps distinguish between an application telemetry problem and an observability platform problem.

## Example Failure Interpretation

Different symptoms can point toward different stages of the pipeline.

### Scrape Target Problems

```text
Target unavailable
       ↓
Check Kubernetes discovery
       ↓
Check relabeling
       ↓
Check application endpoint
```

### Remote Write Problems

```text
Remote write failures
       ↓
Check Alloy remote-write component
       ↓
Check Mimir availability
       ↓
Check connectivity
```

### OTLP Problems

```text
Failed spans
       ↓
Check OTLP receiver
       ↓
Check Alloy exporter
       ↓
Check Tempo availability
```

### Loki Problems

```text
Dropped log entries
       ↓
Check log discovery
       ↓
Check file source
       ↓
Check Loki write path
       ↓
Check Loki availability
```

## Why Self-Monitoring Matters

An observability platform is itself a critical dependency.

If telemetry collection fails, application dashboards can become misleading or incomplete.

Self-monitoring therefore provides visibility into the telemetry infrastructure itself.

The principle is:

```text
Monitor the application
        +
Monitor the observability platform
        =
More reliable investigations
```

The goal is to detect telemetry pipeline failures before assuming that missing or incomplete application telemetry represents an application-side problem.

## Verification

The self-monitoring pipeline was verified in the running environment.

The Alloy self-scrape target is active.

Alloy component graph health reports healthy connections for the monitored pipeline.

Forwarded sample metrics are present.

Mimir remote-write health can be monitored through the dashboard.

OTLP received and failed span metrics are available for the trace pipeline.

Loki sent and dropped entry metrics are available for the logging pipeline.

The self-monitoring metrics are stored in Mimir and visualized through Grafana.

## Responsibility Boundaries

| Component | Self-Monitoring Responsibility |
|---|---|
| Grafana Alloy | Exposes operational metrics about telemetry collection and forwarding |
| Mimir | Stores Alloy self-monitoring metrics |
| Grafana | Visualizes platform health and investigation signals |
| Loki | Receives application log telemetry |
| Tempo | Receives application trace telemetry |

## Summary

The self-monitoring flow is:

```text
Grafana Alloy
     │
     │ self metrics
     ▼
Alloy self-scrape
     │
     ▼
Remote write
     │
     ▼
Grafana Mimir
     │
     ▼
Grafana
     │
     ▼
Self-Monitoring Dashboard
```

The dashboard provides visibility into the health of the telemetry collection layer and its connections to the metrics, logs, and traces backends.
