# Tracing Pipeline

## Purpose

This document explains how distributed traces from the Payment API move through Grafana Alloy to Grafana Tempo and how traces participate in the cross-signal observability workflow.

The tracing pipeline provides:

- OpenTelemetry-based distributed tracing
- OTLP ingestion through Grafana Alloy
- Centralized trace storage in Grafana Tempo
- Trace querying through Grafana
- Correlation between traces and logs
- Correlation between metric exemplars and traces

## Architecture

```text
Payment API
    │
    │ OTLP / gRPC
    ▼
Grafana Alloy
    │
    │ OTLP exporter
    ▼
Grafana Tempo
    │
    │ TraceQL
    ▼
Grafana
```

The Payment API generates distributed traces using OpenTelemetry instrumentation.

Trace data is exported using OTLP over gRPC to Grafana Alloy.

Alloy receives the OTLP spans and forwards them to Grafana Tempo.

Grafana uses Tempo as the trace backend and queries the stored traces for investigation and visualization.

## OpenTelemetry in the Payment API

The Payment API uses OpenTelemetry to generate trace information for incoming requests.

The trace context provides identifiers such as:

- `trace_id`
- `span_id`

The `trace_id` identifies the complete distributed trace.

The `span_id` identifies an individual span within that trace.

Conceptually:

```text
Request
   │
   ▼
Trace
   │
   ├── Span
   ├── Span
   └── Span
```

These identifiers are also included in the application's structured logs, allowing traces and logs to be correlated.

## OTLP Export

The Payment API exports trace data using the OpenTelemetry Protocol (OTLP).

The configured tracing path is:

```text
Payment API
     │
     │ OTLP/gRPC
     ▼
Alloy OTLP receiver
     │
     ▼
OTLP spans
```

The application does not send traces directly to Tempo.

Grafana Alloy acts as the telemetry collection and routing layer between the application and the trace backend.

This keeps the application independent from the backend storage implementation.

## Grafana Alloy OTLP Receiver

Grafana Alloy exposes an OTLP gRPC receiver for incoming application traces.

The receiver listens on:

```text
0.0.0.0:4317
```

The tracing flow inside Alloy is conceptually:

```text
OTLP/gRPC
    │
    ▼
otelcol.receiver.otlp
    │
    ▼
OTLP spans
    │
    ▼
OTLP exporter
```

Alloy receives the spans and forwards them to the configured Tempo endpoint.

## Export to Grafana Tempo

Alloy forwards the received spans to Grafana Tempo using OTLP.

The configured backend endpoint follows this pattern:

```text
http://<tempo-lab-host>:4317
```

The project uses an insecure local OTLP connection for the lab environment.

The complete ingestion flow is:

```text
Payment API
     │
     │ OTLP/gRPC
     ▼
Grafana Alloy
     │
     │ OTLP
     ▼
Grafana Tempo
```

Tempo is responsible for storing and serving the trace data.

## Trace Storage

Grafana Tempo acts as the trace backend for the platform.

The application and Alloy are responsible for producing and forwarding trace data, while Tempo provides the backend used to retain and query the traces.

The responsibility boundary is:

```text
Payment API
    │
    │ generate traces
    ▼
Alloy
    │
    │ collect + forward
    ▼
Tempo
    │
    │ store + serve
    ▼
Grafana
    │
    │ query + visualize
```

## Trace Query Path

Once traces are available in Tempo, Grafana can query the trace backend.

The investigation path is:

```text
Grafana
    │
    │ TraceQL / trace query
    ▼
Grafana Tempo
    │
    ▼
Trace data
```

This allows engineers to inspect individual traces, spans, timing information, and trace attributes.

## TraceID and SpanID

The two important identifiers used throughout the observability platform are:

| Identifier | Purpose |
|---|---|
| `trace_id` | Identifies the complete distributed trace |
| `span_id` | Identifies an individual span within the trace |

The `trace_id` is especially important for cross-signal correlation because it is also present in the structured application logs and can be attached to metric samples as an exemplar.

## Trace Correlation with Logs

The Payment API includes the `trace_id` in structured log records.

This creates a correlation path between Loki and Tempo:

```text
Application request
       │
       ├───────────────┐
       │               │
       ▼               ▼
     Trace            Log
       │               │
       │ trace_id      │ trace_id
       │               │
       └───────┬───────┘
               ▼
        Correlated context
```

Grafana can use the `trace_id` extracted from Loki logs to navigate to the corresponding trace in Tempo.

This allows an engineer to move from an application log directly to the distributed trace associated with the request.

## Trace Correlation with Metrics

The Payment API also associates selected HTTP metric samples with a `trace_id` exemplar.

The correlation path is:

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
   ▼
Trace
```

This provides a second entry point into the tracing system.

An engineer can start from a metric anomaly, select an exemplar, and navigate to the trace associated with that metric sample.

## Cross-Signal Investigation

The tracing pipeline is part of the complete observability workflow:

```text
                 ┌──────────────┐
                 │ Payment API  │
                 └──────┬───────┘
                        │
          ┌─────────────┼─────────────┐
          │             │             │
          ▼             ▼             ▼
       Metrics        Logs         Traces
          │             │             │
          ▼             ▼             ▼
        Mimir          Loki         Tempo
          │             │             │
          └─────────────┼─────────────┘
                        ▼
                     Grafana
```

The signals remain stored in their respective backends while Grafana provides the investigation and correlation layer.

## Investigation Workflow

A typical trace-driven investigation can follow this path:

```text
Metric anomaly
     │
     ▼
Metric exemplar
     │
     ▼
TraceID
     │
     ▼
Tempo trace
     │
     ▼
Trace details
     │
     ▼
Correlated Loki logs
```

The reverse direction is also possible:

```text
Loki log
   │
   ▼
trace_id
   │
   ▼
Tempo trace
```

This allows engineers to move between telemetry signals without manually searching for the corresponding request.

## Verification

The tracing pipeline was verified through the running observability environment.

The Payment API successfully generates trace identifiers.

Grafana Alloy receives OTLP traffic and forwards spans to Tempo.

Grafana can retrieve the resulting traces from Tempo.

Metric exemplars were also verified to contain a `trace_id`, providing a direct metric-to-trace correlation path.

The application logs contain the same trace context identifiers, providing the trace-to-log correlation path.

## Summary

The complete tracing pipeline is:

```text
Payment API
    │
    │ OpenTelemetry
    │ OTLP/gRPC
    ▼
Grafana Alloy
    │
    │ OTLP
    ▼
Grafana Tempo
    │
    │ TraceQL / trace query
    ▼
Grafana
```

The key responsibility boundaries are:

| Component | Responsibility |
|---|---|
| Payment API | Generates distributed traces using OpenTelemetry |
| Grafana Alloy | Receives and forwards OTLP spans |
| Grafana Tempo | Stores and serves trace data |
| Grafana | Queries, visualizes, and correlates traces with other telemetry signals |
