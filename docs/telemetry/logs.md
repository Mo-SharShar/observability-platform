# Logging Pipeline

## Purpose

This document explains how logs from the Payment API move from the Kubernetes workload to Grafana Loki through Grafana Alloy.

The logging pipeline provides:

- Kubernetes pod log collection
- Kubernetes workload discovery
- Label and metadata enrichment
- Structured application logs
- Centralized log storage in Grafana Loki
- Log querying and investigation through Grafana
- TraceID-based correlation with distributed traces

## Architecture

```text
Payment API
    │
    │ stdout / stderr
    ▼
Kubernetes Pod Logs
    │
    │ /var/log/pods
    ▼
Grafana Alloy
    │
    │ discovery + relabeling
    ▼
local.file_match
    │
    ▼
loki.source.file
    │
    ▼
loki.write
    │
    ▼
Grafana Loki
    │
    │ LogQL
    ▼
Grafana
```

The Payment API writes its application logs to `stdout` and `stderr`.

Kubernetes makes the container logs available on the node under the pod log directory.

Grafana Alloy discovers the relevant Kubernetes workloads, applies relabeling, matches the corresponding log files, and forwards the log entries to Loki.

Grafana then queries Loki using LogQL for visualization and investigation.

## Kubernetes Log Collection

The Payment API runs as a Kubernetes workload in the `observability` namespace.

The Kubernetes Alloy DaemonSet has access to the node log directory through a read-only host mount:

```text
/var/log
```

This allows Alloy to read the container log files without requiring the application to communicate directly with Loki.

The collection flow is:

```text
Payment API
     │
     ▼
stdout / stderr
     │
     ▼
Kubernetes node
     │
     ▼
/var/log/pods
     │
     ▼
Grafana Alloy
```

## Grafana Alloy Log Pipeline

The Alloy logging pipeline uses Kubernetes discovery and file-based log collection.

The main stages are:

- Kubernetes service discovery
- Relabeling
- Local file matching
- File-based log source
- Loki write

### 1. Kubernetes Discovery

Alloy discovers Kubernetes pods and their metadata.

The discovered metadata is used to identify the Payment API pods and construct the information required to locate their corresponding log files.

### 2. Relabeling

The discovered Kubernetes metadata is processed through relabeling rules before log collection.

This stage allows useful Kubernetes metadata to be associated with the collected log streams.

The resulting labels can be used later in Grafana and LogQL queries to filter logs by workload, pod, namespace, or other available metadata.

### 3. File Matching

The discovered targets are passed to the local file matching stage.

Conceptually:

```text
Kubernetes metadata
       │
       ▼
Relabeling
       │
       ▼
local.file_match
       │
       ▼
Matching pod log files
```

### 4. Log Source

`loki.source.file` reads the matched Kubernetes log files and converts the entries into Loki log streams.

```text
Matched log files
       │
       ▼
loki.source.file
       │
       ▼
Log entries
```

### 5. Write to Loki

The collected entries are forwarded through `loki.write` to the Loki backend.

The pipeline is therefore:

```text
Kubernetes discovery
        ↓
Relabeling
        ↓
local.file_match
        ↓
loki.source.file
        ↓
loki.write
        ↓
Loki
```

## Structured Application Logs

The Payment API produces structured log records containing identifiers used during request investigation.

Important fields include:

- `request_id`
- `trace_id`
- `span_id`

These fields provide context for individual requests and allow logs to participate in the cross-signal observability workflow.

A simplified example of the structure is:

```json
{
  "request_id": "request-id",
  "trace_id": "trace-id",
  "span_id": "span-id"
}
```

The actual values are generated at runtime and are not stored in the repository as fixed identifiers.

## TraceID Correlation

The `trace_id` field is particularly important because it connects application logs with distributed traces.

Grafana's Loki datasource uses a derived field to extract the `trace_id` from the structured log entry.

Conceptually:

```text
Loki log
    │
    ├── request_id
    ├── trace_id
    └── span_id
          │
          ▼
      Extract trace_id
          │
          ▼
      Tempo trace
```

This allows an engineer viewing a log entry to navigate to the corresponding trace in Tempo.

The correlation path complements the metric exemplar workflow:

```text
Metric
   │
   ▼
Exemplar
   │
   ▼
Tempo Trace
   │
   ▼
Correlated Loki Logs
```

## Log Query Path

Once logs are stored in Loki, Grafana queries them using LogQL.

The complete query path is:

```text
Payment API
     │
     ▼
Kubernetes logs
     │
     ▼
Alloy
     │
     ▼
Loki
     │
     │ LogQL
     ▼
Grafana
```

Grafana can filter the logs using the labels and structured information collected from the Kubernetes workload.

## Why the Application Writes to stdout/stderr

The Payment API does not need to know where logs are ultimately stored.

Instead, it follows the Kubernetes container logging model:

```text
Application
    ↓
stdout / stderr
    ↓
Kubernetes
    ↓
Alloy
    ↓
Loki
```

This separates application logging from the storage and collection backend.

The application produces the logs, while the observability platform controls how those logs are collected, routed, and stored.

## Investigation Workflow

The logging pipeline supports an SRE investigation workflow such as:

```text
Incident / anomaly
       ↓
Grafana dashboard
       ↓
Metric or trace
       ↓
TraceID
       ↓
Loki logs
       ↓
Request context
       ↓
Application investigation
```

This allows logs to be used together with metrics and traces instead of treating each telemetry signal as an isolated data source.

## Summary

The complete logging pipeline is:

```text
Payment API
    │
    │ stdout / stderr
    ▼
Kubernetes pod logs
    │
    │ /var/log/pods
    ▼
Grafana Alloy
    │
    ├── Kubernetes discovery
    ├── Relabeling
    ├── local.file_match
    ├── loki.source.file
    └── loki.write
            │
            ▼
          Loki
            │
            │ LogQL
            ▼
         Grafana
```

The key responsibility boundaries are:

| Component | Responsibility |
|---|---|
| Payment API | Produces structured application logs |
| Kubernetes | Provides the container log files on the node |
| Grafana Alloy | Discovers, reads, enriches, and forwards logs |
| Grafana Loki | Stores and serves the log streams |
| Grafana | Queries, visualizes, and correlates logs with traces |
