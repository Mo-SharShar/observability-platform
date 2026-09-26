# Kubernetes Deployment

## Purpose

This document describes the Kubernetes runtime used by the observability lab and the workloads deployed inside the cluster.

The Kubernetes environment hosts the Payment API and the Kubernetes Grafana Alloy collector.

The core namespace used by the application observability workload is:

```text
observability
```

## Runtime Overview

The current lab runs on a single-node K3s cluster.

The runtime can be represented as:

```text
K3s / Kubernetes
      │
      └── observability namespace
              │
              ├── Payment API
              │     ├── Deployment
              │     ├── 2 replicas
              │     └── ClusterIP Service
              │
              └── Grafana Alloy
                    ├── DaemonSet
                    ├── ConfigMap
                    ├── RBAC
                    └── host log / data mounts
```

The cluster provides the runtime environment for the Kubernetes portion of the observability pipeline.

## Observability Namespace

The application and Kubernetes Alloy resources are deployed in:

```text
observability
```

Using a dedicated namespace separates the observability workload from unrelated Kubernetes resources in the lab.

The namespace contains the core Kubernetes-side resources required for the Payment API telemetry path.

## Payment API Deployment

The Payment API is deployed as a Kubernetes Deployment.

The current deployment uses:

```text
Replicas: 2
Image:    payment-api:3.2
```

The two replicas provide pod-level redundancy within the Kubernetes workload.

Conceptually:

```text
Payment API Deployment
        │
        ├── Pod 1
        │
        └── Pod 2
```

The replicas run on the current Kubernetes node.

## Payment API Service

The Payment API is exposed internally through a Kubernetes ClusterIP Service.

The service provides a stable Kubernetes endpoint for accessing the application while allowing the underlying pods to be replaced independently.

The service configuration maps:

```text
Service port: 80
Target port: 5000
```

Conceptually:

```text
Client inside cluster
        │
        ▼
Payment API Service
        │
        ├── Pod 1 :5000
        │
        └── Pod 2 :5000
```

The Service therefore provides stable discovery and load distribution across the Payment API replicas.

## Health Probes

The Payment API deployment uses Kubernetes health probes.

### Liveness Probe

The liveness probe uses:

```text
/health
```

on port:

```text
5000
```

The liveness probe allows Kubernetes to determine whether the application container is still alive.

Conceptually:

```text
Kubernetes
    │
    │ liveness check
    ▼
/health
    │
    ▼
Payment API
```

### Readiness Probe

The readiness probe uses:

```text
/ready
```

on port:

```text
5000
```

The readiness probe determines whether the application should receive traffic through the Kubernetes Service.

Conceptually:

```text
Kubernetes
    │
    │ readiness check
    ▼
/ready
    │
    ▼
Payment API
```

The distinction is:

```text
Liveness  → Is the container alive?
Readiness → Is the application ready to receive traffic?
```

## Grafana Alloy DaemonSet

Grafana Alloy runs inside Kubernetes as a DaemonSet.

The DaemonSet model ensures that an Alloy pod is scheduled for each Kubernetes node.

The current cluster contains one node, so the current environment has one Kubernetes Alloy pod.

Conceptually:

```text
Kubernetes Nodes
      │
      └── Node 1
            │
            └── Alloy Pod
```

If additional nodes were added, the DaemonSet model would schedule an Alloy instance on each node.

## Alloy Configuration

The Kubernetes Alloy pod loads its configuration from a ConfigMap.

The configuration is mounted into the container at:

```text
/etc/alloy/config.alloy
```

The Alloy process runs the configuration file using:

```text
run /etc/alloy/config.alloy
```

The Alloy HTTP server listens on:

```text
0.0.0.0:12345
```

and the Alloy storage path is:

```text
/var/lib/alloy/data
```

These settings support the collection and self-monitoring functions of the Kubernetes Alloy deployment.

## Alloy Host Log Access

The Kubernetes Alloy DaemonSet mounts the host's log directory:

```text
/var/log
```

as read-only storage.

This allows Alloy to read Kubernetes container log files without modifying the host log directory.

The logging path is:

```text
Application
    │
    ▼
Container stdout/stderr
    │
    ▼
Kubernetes node
    │
    ▼
/var/log/pods
    │
    ▼
Alloy
```

The read-only mount supports the log collection pipeline while limiting Alloy's access to the host filesystem.

## Alloy Persistent Data Path

The Alloy DaemonSet also mounts a host-backed path for Alloy data:

```text
/var/lib/alloy/data
```

This path is used as the Alloy storage path configured for the running process.

The separation is:

```text
/var/log
    → Kubernetes log collection

/var/lib/alloy/data
    → Alloy internal storage
```

## Kubernetes RBAC

The Kubernetes Alloy workload requires permissions to discover Kubernetes resources.

The configured RBAC permissions allow Alloy to:

- get pods
- list pods
- watch pods
- get nodes
- list nodes
- watch nodes

These permissions support Kubernetes discovery and metadata collection.

Conceptually:

```text
Alloy
  │
  ├── Pods: get/list/watch
  │
  └── Nodes: get/list/watch
```

The permissions are scoped to the resources required by the discovery configuration.

## Telemetry Runtime Flow

The Kubernetes runtime supports all three application telemetry signals.

### Metrics

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
```

### Logs

```text
Payment API
    │
    ▼
stdout/stderr
    │
    ▼
Kubernetes node logs
    │
    ▼
Alloy
    │
    ▼
Loki
```

### Traces

```text
Payment API
    │
    │ OTLP/gRPC
    ▼
Alloy
    │
    ▼
Tempo
```

The Kubernetes layer therefore provides the runtime and collection point for the application telemetry path.

## Deployment Verification

The Kubernetes deployment can be verified through the workload and pod status.

The Payment API deployment should report two desired replicas with the corresponding pods running and ready.

The Alloy DaemonSet should have one running pod for the current single-node cluster.

The Payment API Service should have endpoints associated with the active application pods.

Health probes provide additional runtime validation of the application state.

## High Availability Consideration

The current Kubernetes environment is a single-node lab cluster.

The Payment API has two replicas, but both replicas run on the same node.

Therefore:

```text
Pod-level redundancy
        ✓

Node-level redundancy
        ✗
```

A failure of the single Kubernetes node can affect both Payment API replicas and the Kubernetes Alloy instance.

This limitation is documented as part of the current lab architecture rather than being treated as production-grade Kubernetes high availability.

## Responsibility Boundaries

| Component | Responsibility |
|---|---|
| K3s / Kubernetes | Provides the application runtime and workload orchestration |
| Payment API Deployment | Manages the application replicas |
| Payment API Service | Provides stable internal application access |
| Liveness Probe | Detects whether the application container is alive |
| Readiness Probe | Controls whether the application receives traffic |
| Alloy DaemonSet | Runs the Kubernetes telemetry collector |
| Alloy ConfigMap | Provides the Alloy runtime configuration |
| Kubernetes RBAC | Provides Alloy with discovery permissions |

## Summary

The Kubernetes deployment model is:

```text
                 K3s / Kubernetes
                       │
              observability namespace
                       │
          ┌────────────┴────────────┐
          │                         │
          ▼                         ▼
    Payment API                 Grafana Alloy
     Deployment                 DaemonSet
       │                             │
    2 replicas                 1 pod / node
       │                             │
       ▼                             ├── Kubernetes discovery
   ClusterIP Service                ├── Log collection
       │                            ├── Metrics collection
       ▼                            └── OTLP reception
   Application
```

The current implementation provides pod-level redundancy for the Payment API while remaining a single-node Kubernetes lab environment.
