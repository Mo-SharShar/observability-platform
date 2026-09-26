# Telemetry Correlation

## Purpose

This document explains how metrics, traces, and logs are correlated across the observability platform.

The correlation workflow allows an engineer to move between telemetry signals during an investigation instead of treating metrics, traces, and logs as isolated data sources.

The implemented correlation paths are:

```text
Metric
   │
   │ exemplar
   ▼
Tempo Trace
   │
   │ trace_id
   ▼
Loki Logs
```

The platform also supports direct trace-to-log navigation from Loki through the `trace_id`.

## Correlation Architecture

```text
                         Payment API
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
           Metrics           Logs           Traces
              │               │               │
              ▼               ▼               ▼
            Alloy           Alloy           Alloy
              │               │               │
              ▼               ▼               ▼
            Mimir           Loki           Tempo
              │               │               │
              └───────────────┼───────────────┘
                              │
                              ▼
                           Grafana
```

Each telemetry signal has its own backend:

| Signal | Backend | Query / Access |
|---|---|---|
| Metrics | Grafana Mimir | PromQL |
| Logs | Grafana Loki | LogQL |
| Traces | Grafana Tempo | Trace query / TraceQL |

Grafana provides the visualization and correlation layer between these backends.

## Trace Context

The Payment API generates trace context for requests.

The important identifiers are:

- `trace_id`
- `span_id`

The `trace_id` identifies the complete trace.

The `span_id` identifies an individual span within the trace.

The same trace context is used across the application telemetry generated for the request.

Conceptually:

```text
HTTP Request
     │
     ▼
trace_id
     │
     ├───────────────┐
     │               │
     ▼               ▼
   Metrics          Logs
     │               │
     │ exemplar      │ trace_id
     │               │
     └───────┬───────┘
             ▼
           Trace
```

## Metric → Trace Correlation

The Payment API attaches a `trace_id` to selected HTTP metric samples as an OpenMetrics exemplar.

The correlation path is:

```text
HTTP metric
     │
     ▼
Metric sample
     │
     └── trace_id exemplar
              │
              ▼
             Mimir
              │
              ▼
            Grafana
              │
              ▼
        Tempo trace
```

This allows a metric data point to reference the trace associated with the request that produced the sample.

### Example Investigation

An engineer notices increased request latency:

```text
Latency increase
       │
       ▼
HTTP latency metric
       │
       ▼
Exemplar
       │
       ▼
trace_id
       │
       ▼
Tempo
       │
       ▼
Trace details
```

This reduces the need to manually search the tracing backend for a matching request.

## Trace → Logs Correlation

The Payment API includes `trace_id` in its structured application logs.

The Loki datasource in Grafana uses a derived field to extract the trace identifier from the log content.

The configured derived-field concept is:

```text
Log entry
    │
    ▼
trace_id
    │
    ▼
Tempo
```

The derived field uses the `trace_id` value extracted from the structured log entry and provides a navigation path to the corresponding Tempo trace.

## Loki Derived Field

The Loki datasource uses a derived field named:

```text
TraceID
```

The extraction pattern identifies the `trace_id` value from structured JSON logs.

Conceptually:

```text
JSON log
   │
   ▼
"trace_id": "<trace-id>"
   │
   ▼
Extract trace ID
   │
   ▼
Grafana link
   │
   ▼
Tempo
```

The query value is taken from the extracted trace identifier and used for the Tempo navigation target.

This makes the correlation available directly from the log view.

## Tempo → Loki Correlation

The reverse direction is also configured.

When viewing a trace in Tempo, Grafana can use the trace context to retrieve related logs from Loki.

The trace-to-log configuration uses:

- Loki as the log datasource
- a time window around the trace
- `service.name` mapped to the application label
- trace ID filtering enabled

Conceptually:

```text
Tempo Trace
     │
     ├── trace_id
     ├── service.name
     └── timestamp
             │
             ▼
          Grafana
             │
             ▼
           Loki
             │
             ▼
      Related log entries
```

This allows an engineer investigating a trace to move back to the application logs generated around that trace.

## Complete Correlation Workflow

The implemented cross-signal workflow can be represented as:

```text
                    Metric
                      │
                      │ exemplar
                      ▼
                  trace_id
                      │
                      ▼
                    Tempo
                      │
                      │ trace_id
                      ▼
                    Loki
```

The same workflow can also start from logs:

```text
Loki Log
   │
   │ trace_id
   ▼
Tempo Trace
```

And from a trace:

```text
Tempo Trace
   │
   │ trace context
   ▼
Loki Logs
```

## SRE Investigation Workflow

A typical investigation can start from any available signal.

### Starting from Metrics

```text
Metric anomaly
     ↓
Metric exemplar
     ↓
Trace ID
     ↓
Tempo trace
     ↓
Correlated logs
```

### Starting from Logs

```text
Application error log
     ↓
trace_id
     ↓
Tempo trace
     ↓
Request timeline
```

### Starting from Traces

```text
Slow trace
     ↓
Trace details
     ↓
Trace ID
     ↓
Related Loki logs
     ↓
Application context
```

This provides multiple entry points into the same request context.

## Why Correlation Matters

Metrics answer questions such as:

```text
What is happening?
```

Traces help answer:

```text
Where did the request spend time?
```

Logs help answer:

```text
What happened during the request?
```

Correlation connects these signals:

```text
Metrics
   │
   │ detect
   ▼
Traces
   │
   │ investigate
   ▼
Logs
   │
   │ provide context
   ▼
Root-cause investigation
```

The goal is not to replace one telemetry signal with another.

Instead, each signal provides a different level of investigation context.

## Verification

The correlation workflow was verified in the running observability environment.

Metric exemplars returned by Mimir contained a `trace_id`.

Grafana displayed exemplar points on the relevant metric graph.

Selecting an exemplar provided navigation to the corresponding Tempo trace.

Application logs contained the same trace context identifiers.

The Loki datasource exposed the `trace_id` through the `TraceID` derived field.

Tempo was configured with Loki trace-to-logs correlation using the application service label and trace ID filtering.

These components provide the implemented metric-to-trace and trace-to-log correlation paths.

## Responsibility Boundaries

| Component | Correlation Responsibility |
|---|---|
| Payment API | Generates trace context and exposes trace identifiers in telemetry |
| Grafana Alloy | Collects and routes metrics, logs, and traces |
| Grafana Mimir | Stores metrics and their exemplars |
| Grafana Loki | Stores logs containing trace context |
| Grafana Tempo | Stores distributed traces |
| Grafana | Provides cross-signal navigation and visualization |

## Summary

The observability platform implements correlation across all three major telemetry signals:

```text
                         Grafana
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
            Mimir         Loki          Tempo
              │             │             │
              │             │             │
          Metrics          Logs         Traces
              │             │             │
              └───────┬─────┴──────┬──────┘
                      │             │
                  Exemplars      trace_id
                      │             │
                      └──────┬──────┘
                             ▼
                       Cross-signal
                        correlation
```

The resulting investigation path is:

```text
Metric
  ↓
Exemplar
  ↓
Trace
  ↓
Logs
```

while direct trace-to-log and log-to-trace navigation are also available through the shared `trace_id`.
