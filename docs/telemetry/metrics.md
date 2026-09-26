# Metrics Pipeline

## Purpose

This document explains how application metrics move from the Payment API to Grafana through Grafana Alloy and Grafana Mimir.

The pipeline is designed to provide:

- Prometheus/OpenMetrics-compatible application metrics
- Centralized metrics collection through Grafana Alloy
- Remote-write storage in Grafana Mimir
- Visualization and querying through Grafana
- Trace correlation through metric exemplars

## Architecture

```text
Payment API
    │
    │  /metrics
    ▼
Grafana Alloy
    │
    │  prometheus.scrape
    ▼
Metric samples
    │
    │  prometheus.remote_write
    ▼
Grafana Mimir
    │
    │  PromQL
    ▼
Grafana
```

The Payment API exposes its metrics through the `/metrics` endpoint.

Grafana Alloy discovers the Kubernetes workload and scrapes the endpoint using its Prometheus-compatible scraping pipeline.

The collected samples are forwarded to Grafana Mimir using Prometheus remote write.

Grafana then queries Mimir to visualize the stored time-series data.

## Metrics Exposed by the Payment API

The Payment API exposes Prometheus/OpenMetrics-compatible metrics including:

- HTTP request metrics
- HTTP request duration metrics
- Payment business metrics

The metrics endpoint also supports exemplars, allowing selected metric samples to carry a `trace_id`.

This creates a direct correlation path from a metric data point to the distributed trace associated with the request.

## Example Metrics Flow

```text
HTTP request
    │
    ▼
Payment API
    │
    ├── records HTTP metrics
    ├── records request duration
    └── associates trace_id as an exemplar
            │
            ▼
        /metrics
            │
            ▼
       Grafana Alloy
            │
            ▼
        Grafana Mimir
            │
            ▼
          Grafana
```

## Grafana Alloy Metrics Pipeline

Grafana Alloy is responsible for collecting the Payment API metrics from Kubernetes and forwarding them to Mimir.

The metrics pipeline uses two main Alloy components:

- `prometheus.scrape`
- `prometheus.remote_write`

### 1. Target Discovery

Alloy discovers the Payment API workload through Kubernetes service discovery.

The discovered targets are processed through relabeling before being passed to the Prometheus scrape component.

The purpose of this stage is to identify the correct Kubernetes workload and expose its `/metrics` endpoint as a scrape target.

### 2. Prometheus Scraping

The `prometheus.scrape` component periodically requests:

```text
/metrics
```

from the Payment API.

Conceptually:

```text
Kubernetes target
      │
      ▼
prometheus.scrape
      │
      ▼
Payment API /metrics
      │
      ▼
Metric samples
```

The scraped samples remain inside the Alloy pipeline until they are forwarded to the configured remote-write destination.

### 3. Remote Write to Mimir

Alloy forwards the collected samples to Grafana Mimir using Prometheus remote write.

The configured endpoint follows this pattern:

```text
http://<mimir-lab-host>:9009/api/v1/push
```

Conceptually:

```text
Payment API
     │
     ▼
/metrics
     │
     ▼
Alloy prometheus.scrape
     │
     ▼
Metric samples
     │
     ▼
Alloy prometheus.remote_write
     │
     ▼
Mimir
```

Mimir provides the persistent metrics storage layer used by Grafana for querying the collected time-series data.

## Why Remote Write Is Used

The Payment API does not send metrics directly to Mimir.

Instead, Alloy acts as the collection and routing layer:

```text
Application
    ↓
Alloy
    ↓
Mimir
```

This separation allows the application to expose a standard `/metrics` endpoint while the observability platform controls collection, routing, and storage.

It also keeps the application independent from the specific metrics storage backend.

## Metrics Query Path

Once metrics have been stored in Mimir, Grafana queries Mimir using PromQL.

```text
Payment API
     │
     ▼
  /metrics
     │
     ▼
   Alloy
     │
     ▼
   Mimir
     │
     │ PromQL
     ▼
  Grafana
```

This means the application is responsible for exposing telemetry, Alloy is responsible for collecting and forwarding it, Mimir is responsible for storing it, and Grafana is responsible for querying and visualizing it.

## Metric Exemplars

The Payment API exposes OpenMetrics-compatible HTTP metrics with trace exemplars.

An exemplar associates a metric sample with a `trace_id`, creating a correlation path between metrics and distributed traces.

The implemented flow is:

```text
Metric sample
     │
     ├── metric value
     └── trace_id exemplar
              │
              ▼
             Mimir
              │
              ▼
           Grafana
              │
              ▼
        Trace in Tempo
```

### Why Exemplars Matter

Without exemplars, an engineer can identify a metric anomaly but must manually search for the corresponding trace.

With exemplars, the metric data point can contain a reference to the trace associated with the request.

This supports an investigation workflow such as:

```text
Latency spike
     ↓
Metric exemplar
     ↓
Trace ID
     ↓
Tempo trace
     ↓
Trace details
     ↓
Correlated logs
```

### Verification

The exemplar pipeline was verified by querying Mimir for metric exemplars.

The returned HTTP request exemplars contained a `trace_id`, and Grafana displayed exemplar points on the metric graph.

Selecting an exemplar provides a direct navigation path to the corresponding trace in Tempo.

This verifies that the correlation is not only configured at the Grafana UI level; the trace identifier is actually carried with the metric exemplar through the metrics pipeline.

## Summary

The complete metrics pipeline is:

```text
Payment API
    │
    │ /metrics
    ▼
Grafana Alloy
    │
    │ prometheus.scrape
    ▼
Metric samples
    │
    │ prometheus.remote_write
    ▼
Grafana Mimir
    │
    │ PromQL + exemplars
    ▼
Grafana
    │
    │ exemplar → trace
    ▼
Grafana Tempo
```

The key responsibility boundaries are:

| Component | Responsibility |
|---|---|
| Payment API | Exposes application and business metrics |
| Grafana Alloy | Discovers targets, scrapes metrics, and forwards samples |
| Grafana Mimir | Stores and serves the metrics |
| Grafana | Queries, visualizes, and provides metric-to-trace navigation |
| Grafana Tempo | Stores and displays the correlated distributed trace |
