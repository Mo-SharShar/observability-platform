# Troubleshooting Runbook

## Purpose

This document provides a practical troubleshooting workflow for the observability platform.

The runbook focuses on the telemetry paths implemented in the lab:

- Metrics
- Logs
- Traces
- Metric exemplars
- Cross-signal correlation
- Grafana Alloy
- Mimir
- Loki
- Tempo
- Kubernetes runtime

The objective is to identify which stage of the telemetry pipeline is failing before changing configuration.

## General Investigation Model

When telemetry is missing or incomplete, start from the signal and move through its pipeline.

```text
Application
    │
    ▼
Collection
    │
    ▼
Routing
    │
    ▼
Backend
    │
    ▼
Grafana
```

For the Payment API:

```text
Payment API
    │
    ├── Metrics ──► Alloy ──► Mimir
    │
    ├── Logs ─────► Alloy ──► Loki
    │
    └── Traces ───► Alloy ──► Tempo
```

The first troubleshooting question should be:

```text
Which stage stopped receiving or forwarding data?
```

## First-Level Checks

Start with the Kubernetes workload.

Check the Payment API pods:

```bash
kubectl get pods -n observability
```

This verifies whether the application pods are running.

Check the Payment API Deployment:

```bash
kubectl get deployment payment-api -n observability
```

This verifies the desired and available replica state.

Check the Payment API Service:

```bash
kubectl get service payment-api -n observability
```

This verifies that the Kubernetes Service exists and exposes the expected application port.

Check the Alloy pod:

```bash
kubectl get pods -n observability -l app.kubernetes.io/name=alloy
```

The exact selector can vary with the deployed labels, so the general objective is to confirm that the Kubernetes Alloy pod is running.

## Metrics Troubleshooting

The metrics path is:

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
Alloy prometheus.remote_write
    │
    ▼
Mimir
    │
    ▼
Grafana
```

### Step 1 — Check the Application Metrics Endpoint

Verify that the Payment API exposes its metrics endpoint.

From inside the cluster, the target should respond to:

```text
/metrics
```

The objective is to determine whether the problem exists at the application endpoint or later in the collection pipeline.

### Step 2 — Check Alloy Scrape Targets

Inspect Alloy's operational metrics and self-monitoring dashboard.

Useful signals include:

```text
prometheus_target_sync_failed_total
```

and the Alloy scrape-target panels.

If target discovery or synchronization is failing, investigate:

```text
Kubernetes discovery
        ↓
Relabeling
        ↓
Scrape target
```

### Step 3 — Check Forwarded Samples

Inspect:

```text
prometheus_forwarded_samples_total
```

This helps determine whether samples collected by Alloy are moving through the pipeline.

The distinction is:

```text
Target discovered
       ≠
Samples successfully forwarded
```

### Step 4 — Check Mimir Remote Write

Inspect the self-monitoring panels for:

- remote-write rate
- remote-write failures
- pending samples

If remote-write failures increase, investigate the connection between Alloy and Mimir.

### Step 5 — Query Mimir

If Alloy appears healthy but Grafana does not show application metrics, query Mimir directly.

The objective is to distinguish between:

```text
Data not stored
        vs
Data stored but not visualized
```

## Logs Troubleshooting

The logging path is:

```text
Payment API
    │
    ▼
stdout/stderr
    │
    ▼
Kubernetes pod logs
    │
    ▼
Alloy
    │
    ├── discovery
    ├── relabeling
    ├── local.file_match
    ├── loki.source.file
    └── loki.write
            │
            ▼
           Loki
            │
            ▼
         Grafana
```

### Step 1 — Check Application Logs

Inspect the Payment API pod logs:

```bash
kubectl logs -n observability deployment/payment-api
```

This verifies whether the application is actually producing log output.

### Step 2 — Check Kubernetes Log Files

Alloy reads Kubernetes container log files from the node's log directory.

The expected collection path includes:

```text
/var/log/pods
```

If application logs exist but are not visible in Loki, investigate the Alloy file-collection path.

### Step 3 — Check Alloy Log Pipeline

Verify:

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
```

The self-monitoring dashboard provides useful signals for the Loki pipeline.

Important signals include:

```text
Loki Entries Sent
Loki Entries Dropped
```

### Step 4 — Check Loki

If Alloy appears to be sending entries but Grafana shows no logs, investigate Loki availability and query behavior.

The investigation should distinguish:

```text
Logs not collected
        vs
Logs collected but not stored
        vs
Logs stored but query not matching
```

## Tracing Troubleshooting

The tracing path is:

```text
Payment API
    │
    │ OTLP/gRPC
    ▼
Alloy OTLP receiver
    │
    ▼
Alloy OTLP exporter
    │
    ▼
Tempo
    │
    ▼
Grafana
```

### Step 1 — Check Application Trace Generation

Verify that application requests produce trace context.

The important identifiers are:

```text
trace_id
span_id
```

These identifiers should also appear in the structured application logs.

### Step 2 — Check Alloy OTLP Receiver

Alloy receives OTLP/gRPC traffic on:

```text
4317
```

If the application reports an OTLP connection problem, verify:

```text
Application
    ↓
Alloy service
    ↓
OTLP receiver
```

### Step 3 — Check OTLP Self-Monitoring Metrics

The self-monitoring dashboard tracks:

```text
OTLP Spans Received
OTLP Spans Failed
```

These metrics help determine whether Alloy is receiving spans and whether failures are occurring in the trace pipeline.

### Step 4 — Check Tempo

If Alloy receives spans but Grafana cannot display traces, investigate the Alloy-to-Tempo path and Tempo availability.

The distinction is:

```text
Spans received by Alloy
        ≠
Spans successfully available in Tempo
```

## OTLP `UNAVAILABLE` Error

During development, the Payment API produced an error similar to:

```text
Transient error StatusCode.UNAVAILABLE encountered while exporting traces
```

This indicates that the application could not successfully communicate with the configured OTLP destination at that moment.

The investigation path is:

```text
Payment API
    │
    ▼
OTLP endpoint
    │
    ▼
Alloy receiver
```

Check:

1. The Alloy pod is running.
2. The Alloy Service exists.
3. Port `4317` is exposed.
4. The configured OTLP endpoint points to the correct Kubernetes service.
5. The Alloy OTLP receiver is listening.
6. Network connectivity exists between the Payment API and Alloy.

The error should not automatically be treated as an application tracing instrumentation problem.

The first objective is to verify connectivity to the telemetry collector.

## Mimir `503 Service Unavailable`

During the lab, a connectivity test to the Mimir readiness endpoint returned:

```text
HTTP/1.1 503 Service Unavailable
```

A readiness failure means the backend should be investigated before assuming that Alloy's remote-write configuration is incorrect.

The investigation path is:

```text
Alloy
    │
    ▼
Mimir
    │
    ▼
Readiness
```

Check:

- Mimir container status
- Mimir logs
- Mimir readiness endpoint
- Mimir configuration
- network connectivity
- storage/backend dependencies

The key distinction is:

```text
Mimir unavailable
        vs
Alloy unable to reach Mimir
```

Both sides should be checked before changing the remote-write configuration.

## Port Conflicts

Port conflicts occurred during development when multiple services attempted to use the same host port.

A common example was:

```text
port 5000 already allocated
```

The troubleshooting workflow is:

```text
Port conflict
     │
     ▼
Identify process/container using port
     │
     ▼
Check Docker containers
     │
     ▼
Check Kubernetes port-forward processes
     │
     ▼
Stop or reconfigure the conflicting process
```

Avoid changing application ports unnecessarily when the conflict is caused by a temporary test or port-forward process.

## Kubernetes Port-Forward Problems

Port-forwarding can fail when the requested local port is already in use.

The investigation should distinguish:

```text
Application unavailable
        vs
Local port unavailable
```

If the Kubernetes Service and pods are healthy but port-forwarding fails, inspect the local process using the selected port before modifying Kubernetes resources.

## Alloy Troubleshooting

When multiple telemetry signals fail at the same time, Alloy is an important common dependency.

The investigation path is:

```text
Metrics
Logs
Traces
   │
   ▼
Grafana Alloy
```

Check:

```bash
kubectl get pods -n observability
```

Then inspect the Alloy pod logs:

```bash
kubectl logs -n observability <alloy-pod-name>
```

The exact pod name should be obtained from the current cluster state.

Also inspect the self-monitoring dashboard for:

- component health
- scrape targets
- forwarded samples
- remote-write failures
- OTLP failures
- Loki dropped entries

This provides a platform-level view before changing the Alloy configuration.

## Correlation Troubleshooting

Correlation depends on shared trace context.

The expected flow is:

```text
Metric exemplar
      │
      ▼
trace_id
      │
      ▼
Tempo
      │
      ▼
Loki
```

If metric-to-trace navigation fails:

1. Verify that the metric contains an exemplar.
2. Verify that the exemplar contains `trace_id`.
3. Verify that the corresponding trace exists in Tempo.
4. Verify the Grafana exemplar link configuration.

If trace-to-log navigation fails:

1. Verify that application logs contain `trace_id`.
2. Verify the Loki `TraceID` derived field.
3. Verify the extracted trace ID.
4. Verify that the trace exists in Tempo.

If Tempo trace-to-log correlation fails:

1. Verify the Loki datasource configuration.
2. Verify the `service.name` to application-label mapping.
3. Verify trace ID filtering.
4. Verify the configured time window.

## Investigation Decision Tree

A practical high-level decision tree is:

```text
Telemetry missing
       │
       ▼
Is the application healthy?
       │
       ├── No ──► Investigate application
       │
       └── Yes
             │
             ▼
       Is Alloy healthy?
             │
             ├── No ──► Investigate Alloy
             │
             └── Yes
                   │
                   ▼
             Is data being forwarded?
                   │
                   ├── No ──► Investigate collection/routing
                   │
                   └── Yes
                         │
                         ▼
                   Is backend healthy?
                         │
                         ├── No ──► Investigate backend
                         │
                         └── Yes
                               │
                               ▼
                         Check Grafana query
                         and datasource configuration
```

## Useful Verification Commands

### Kubernetes Workloads

```bash
kubectl get pods -n observability
```

Shows the current pod status.

```bash
kubectl get deployment -n observability
```

Shows deployment replica state.

```bash
kubectl get svc -n observability
```

Shows Kubernetes Services.

### Application Logs

```bash
kubectl logs -n observability deployment/payment-api
```

Shows recent logs from the Payment API Deployment.

### Alloy Logs

```bash
kubectl logs -n observability <alloy-pod-name>
```

Shows Alloy runtime logs.

### Resource Details

```bash
kubectl describe pod -n observability <pod-name>
```

Provides detailed pod state, events, mounts, and configuration information.

## Troubleshooting Principles

The main troubleshooting principles used in this project are:

### Follow the Data

Do not immediately change configuration.

First determine where the data stops:

```text
Generate
   ↓
Collect
   ↓
Forward
   ↓
Store
   ↓
Query
   ↓
Visualize
```

### Separate Signals

Metrics, logs, and traces have different pipelines.

A problem in one signal does not automatically mean that the entire observability platform is broken.

### Check Dependencies

When a collector reports an error, verify the destination backend as well.

For example:

```text
Remote write failure
        ↓
Check Alloy
        +
Check Mimir
```

### Use Self-Monitoring

The observability platform's own metrics should be checked before assuming that missing telemetry represents an application failure.

### Change One Layer at a Time

Avoid changing application, collector, backend, and Grafana configuration simultaneously.

Isolating one layer makes the resulting behavior easier to interpret.

## Summary

The troubleshooting workflow used by the project is:

```text
Identify missing signal
        │
        ▼
Check application
        │
        ▼
Check Alloy collection
        │
        ▼
Check forwarding
        │
        ▼
Check backend
        │
        ▼
Check Grafana query
        │
        ▼
Correlate signals
        │
        ▼
Investigate root cause
```

The runbook is designed to support systematic investigation of the implemented observability pipelines without treating a single component as the default source of every failure.
