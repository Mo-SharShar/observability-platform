# Helm Deployment

## Purpose

This document describes the Helm lab used to package and manage the Payment API as a Kubernetes application.

The Helm configuration is maintained separately from the core observability runtime.

The lab demonstrates:

- Helm chart structure
- Configurable deployment values
- Kubernetes resource templating
- Release installation
- Release upgrades
- Release rollback
- Environment-specific values
- Chart validation and packaging

## Helm Architecture

```text
Helm Chart
    │
    ├── Chart.yaml
    ├── values.yaml
    ├── values-prod.yaml
    └── templates/
          │
          ▼
    Kubernetes Manifests
          │
          ▼
    Helm Release
          │
          ▼
    Kubernetes
```

Helm provides the packaging and release-management layer for the Payment API deployment used in this lab.

## Chart Structure

The chart is located at:

```text
06-helm/payment-api
```

The main files are:

```text
06-helm/payment-api/
├── Chart.yaml
├── values.yaml
├── values-prod.yaml
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    └── ...
```

The chart intentionally contains only the resources required for the Payment API Helm lab.

## Chart Metadata

The chart is defined as an application chart:

```yaml
apiVersion: v2
name: payment-api
description: Helm chart for the Payment API
type: application
version: 0.1.0
appVersion: "3.2"
```

The important distinction is:

```text
version
    → Helm chart version

appVersion
    → Application version represented by the chart
```

The current chart version is:

```text
0.1.0
```

and the application version is:

```text
3.2
```

## Configurable Values

The default chart values include:

```yaml
replicaCount: 2

image:
  repository: payment-api
  pullPolicy: IfNotPresent
  tag: "3.2"

containerPort: 5000
```

The values file also defines:

- application environment variables
- service configuration
- liveness probe
- readiness probe
- resource configuration
- termination grace period

This allows the Kubernetes manifests to be generated from reusable configuration instead of hard-coded values.

## Production Values

The chart also includes:

```text
values-prod.yaml
```

The production-oriented values override selected defaults.

The configured resource requests are:

```text
CPU:    100m
Memory: 128Mi
```

The configured limits are:

```text
CPU:    500m
Memory: 512Mi
```

The production values keep the Payment API at two replicas and use image tag `3.2`.

Conceptually:

```text
values.yaml
      │
      ├── default configuration
      │
      ▼
values-prod.yaml
      │
      └── environment-specific overrides
```

## Helm Templating

Helm templates generate Kubernetes manifests from the configured values.

Conceptually:

```text
values.yaml
     │
     ├── replica count
     ├── image
     ├── ports
     ├── probes
     └── resources
          │
          ▼
    Helm templates
          │
          ▼
 Kubernetes manifests
```

This separates application configuration from the Kubernetes resource definitions.

## Chart Validation

The chart was validated using:

```bash
helm lint .
```

`helm lint` checks the chart structure and identifies common chart issues before installation.

The chart passed lint validation.

## Rendering Kubernetes Manifests

The chart can be rendered without installing it using:

```bash
helm template .
```

This generates the Kubernetes manifests that Helm would submit to the cluster.

This is useful for reviewing the rendered resources before deployment.

The workflow is:

```text
Helm chart
    │
    ▼
helm template
    │
    ▼
Rendered Kubernetes YAML
```

## Installation

The chart was installed into a dedicated Kubernetes namespace:

```text
helm-lab
```

The release name is:

```text
payment-api
```

The installation creates a Helm release that tracks the deployed resources.

Conceptually:

```text
Helm
 │
 ▼
payment-api release
 │
 ▼
helm-lab namespace
 │
 ├── Deployment
 └── Service
```

## Helm Release Management

Helm tracks releases and their revisions.

The Payment API release was used to demonstrate:

- initial installation
- upgrade
- rollback
- subsequent upgrade with environment-specific values

This provides a controlled way to manage changes to the Kubernetes application.

## Upgrade

The release was upgraded from two replicas to three replicas as a release-management test.

Conceptually:

```text
Revision 1
    │
    │ upgrade
    ▼
Revision 2
    │
    └── replicas: 3
```

The upgrade creates a new Helm release revision.

## Rollback

The release was then rolled back to the previous revision.

Conceptually:

```text
Revision 2
    │
    │ rollback
    ▼
Revision 1
```

Rollback demonstrates the ability to return the release to a previously known configuration.

The release was subsequently upgraded again as part of the lab workflow.

## Environment-Specific Configuration

The `values-prod.yaml` file was used during a Helm upgrade to apply resource requests and limits.

This demonstrates how environment-specific configuration can be layered on top of the chart defaults.

The resulting deployment included:

```text
Requests:
  CPU:    100m
  Memory: 128Mi

Limits:
  CPU:    500m
  Memory: 512Mi
```

## Packaging

The chart can be packaged into a versioned Helm archive:

```text
payment-api-0.1.0.tgz
```

The generated package is excluded from Git because it is a build artifact.

The packaged chart was also validated with Helm lint.

## Helm vs Kubernetes Runtime

The Helm lab and the core Kubernetes observability runtime have different responsibilities.

```text
Core Kubernetes Runtime
    │
    └── Runs the current observability workload

Helm Lab
    │
    └── Demonstrates application packaging and release management
```

The Helm chart should therefore not be interpreted as proof that the current core `observability` namespace is managed by this Helm release.

The Helm lab is a separate deployment-management exercise for the Payment API.

## Operational Workflow

A typical Helm workflow used in this project is:

```text
Modify chart
    │
    ▼
helm lint
    │
    ▼
helm template
    │
    ▼
helm install / helm upgrade
    │
    ▼
Verify Kubernetes resources
    │
    ├── deployment
    ├── pods
    └── service
    │
    ▼
helm history
    │
    ▼
Rollback if required
```

This workflow provides validation before deployment and a release history for controlled changes.

## Verification

The Helm lab was verified through:

- successful chart linting
- successful manifest rendering
- successful release installation
- successful release upgrade
- successful rollback
- successful subsequent upgrade using `values-prod.yaml`
- verification of resulting Kubernetes resources
- successful chart packaging

The release history records the changes performed during the lab.

## Responsibility Boundaries

| Component | Responsibility |
|---|---|
| Helm Chart | Defines reusable application deployment templates |
| `values.yaml` | Provides default configuration |
| `values-prod.yaml` | Provides environment-specific overrides |
| Helm | Packages and manages application releases |
| Kubernetes | Runs the rendered application resources |
| Helm Release | Tracks deployed revisions and release history |

## Summary

The Helm lab demonstrates application packaging and release management for the Payment API:

```text
Chart
  │
  ▼
Values
  │
  ▼
Templates
  │
  ▼
Kubernetes manifests
  │
  ▼
Helm Release
  │
  ├── Upgrade
  ├── Rollback
  └── Environment-specific configuration
```

The lab demonstrates how Helm can provide repeatable Kubernetes application deployment and controlled release management without coupling the Helm lab to the core observability namespace.
