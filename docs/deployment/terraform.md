# Terraform Deployment

## Purpose

This document describes the Terraform lab used to manage Kubernetes infrastructure resources declaratively.

The Terraform configuration is maintained separately from the core observability runtime.

The lab demonstrates:

- Terraform provider configuration
- Kubernetes namespace management
- ConfigMap management
- Deployment management
- Service management
- Variable-driven configuration
- Terraform plan
- Terraform apply
- Drift detection and reconciliation

## Terraform Architecture

```text
Terraform Configuration
        │
        ├── Provider
        ├── Variables
        ├── Resources
        └── Outputs
                │
                ▼
        Kubernetes API
                │
                ▼
        terraform-lab namespace
                │
                ├── ConfigMap
                ├── Nginx Deployment
                └── Nginx Service
```

Terraform acts as the declarative infrastructure management layer for this separate Kubernetes lab.

## Directory Structure

The Terraform configuration is located at:

```text
07-terraform/01-kubernetes
```

The lab contains the Terraform configuration required to create and manage the Kubernetes resources.

The main configuration areas include:

```text
07-terraform/01-kubernetes/
├── provider configuration
├── variables
├── Kubernetes resources
├── outputs
└── terraform.tfvars
```

## Kubernetes Provider

The lab uses the HashiCorp Kubernetes provider.

The provider is configured to use the local Kubernetes configuration:

```hcl
provider "kubernetes" {
  config_path = "~/.kube/config"
}
```

This allows Terraform to communicate with the Kubernetes API using the user's configured cluster credentials.

## Managed Namespace

Terraform manages a dedicated namespace:

```text
terraform-lab
```

The namespace name is provided through a Terraform variable:

```hcl
namespace_name = "terraform-lab"
```

Using a variable keeps the namespace configurable rather than embedding the value throughout the configuration.

## Managed Resources

The Terraform lab manages the following Kubernetes resources:

```text
terraform-lab
    │
    ├── Namespace
    │
    ├── ConfigMap
    │
    ├── Nginx Deployment
    │     └── 2 replicas
    │
    └── Nginx Service
```

The Nginx workload is intentionally separate from the core observability workload.

## ConfigMap

Terraform manages a Kubernetes ConfigMap named:

```text
payment-config
```

The ConfigMap demonstrates declarative management of Kubernetes application configuration.

The important concept is:

```text
Terraform configuration
        │
        ▼
Kubernetes ConfigMap
```

Terraform records the desired state and can detect changes between the declared configuration and the actual Kubernetes resource.

## Nginx Deployment

The Terraform lab creates an Nginx Deployment with:

```text
Replicas: 2
Image:    nginx:1.29
```

The deployment also defines resource requests and limits.

### Resource Requests

```text
CPU:    100m
Memory: 64Mi
```

### Resource Limits

```text
CPU:    500m
Memory: 256Mi
```

Conceptually:

```text
Nginx Deployment
       │
       ├── Pod 1
       └── Pod 2
```

The deployment provides a simple workload for demonstrating Terraform reconciliation.

## Nginx Service

Terraform also manages a Kubernetes ClusterIP Service for the Nginx workload.

The service exposes:

```text
Port: 80
```

Conceptually:

```text
Client
  │
  ▼
Nginx Service
  │
  ├── Nginx Pod 1
  └── Nginx Pod 2
```

The Service provides stable access to the Deployment's pods.

## Terraform Variables

The namespace is controlled through a Terraform variable:

```hcl
variable "namespace_name" {
  type = string
}
```

The current variable value is:

```hcl
namespace_name = "terraform-lab"
```

The variable allows the same configuration to be reused with a different namespace value when required.

## Terraform Plan

`terraform plan` is used to preview the changes Terraform intends to make.

Conceptually:

```text
Terraform configuration
        │
        ▼
terraform plan
        │
        ▼
Desired changes
```

The plan provides an opportunity to review infrastructure changes before they are applied.

## Terraform Apply

`terraform apply` applies the planned changes to the Kubernetes cluster.

The workflow is:

```text
Configuration
     │
     ▼
terraform plan
     │
     ▼
Review
     │
     ▼
terraform apply
     │
     ▼
Kubernetes
```

Terraform then records the resulting infrastructure state in its state management system.

## Drift Detection

A key part of the lab is demonstrating infrastructure drift.

The desired state specifies:

```text
Nginx replicas: 2
```

The deployment was manually scaled outside Terraform from:

```text
2 → 3 replicas
```

This creates a difference between:

```text
Terraform desired state
        │
        ▼
2 replicas

Kubernetes actual state
        │
        ▼
3 replicas
```

Terraform detects this difference during planning.

The resulting plan identifies the required change to reconcile the actual state back to the declared configuration.

## Drift Reconciliation

After drift was detected, Terraform was used to reconcile the Kubernetes deployment.

The reconciliation returned the Deployment to:

```text
Replicas: 2
```

The workflow demonstrates the core Infrastructure as Code reconciliation model:

```text
Desired State
     │
     ▼
Terraform Plan
     │
     ▼
Drift Detected
     │
     ▼
Terraform Apply
     │
     ▼
Actual State
     │
     ▼
Desired State Restored
```

## Variable Replacement Test

The lab also demonstrated how changing an infrastructure identifier can cause Terraform to plan a resource replacement.

A namespace value was changed from the original lab namespace to:

```text
terraform-demo
```

Terraform showed a replacement operation in the plan.

The replacement was inspected but not applied.

This demonstrates the importance of reviewing Terraform plans before applying potentially destructive infrastructure changes.

## Terraform State

Terraform maintains state to track the resources managed by the configuration.

The state allows Terraform to compare:

```text
Configuration
     │
     ├── Desired state
     │
     ▼
Terraform state
     │
     ├── Known resources
     │
     ▼
Kubernetes
     │
     └── Actual state
```

Terraform uses this information to determine whether resources need to be created, changed, replaced, or destroyed.

Terraform state files are excluded from Git because they can contain infrastructure information and should not be committed as project source files.

## Verification

The Terraform lab was verified through:

- successful Terraform initialization
- successful planning
- successful application of the Kubernetes resources
- verification of the created namespace
- verification of the ConfigMap
- verification of the Nginx Deployment
- verification of the Nginx Service
- successful drift detection
- successful drift reconciliation
- inspection of a planned resource replacement without applying it

The final Nginx Deployment state contains:

```text
Desired:    2
Updated:    2
Total:      2
Available:  2
```

The configured Nginx resources are:

```text
Requests:
  CPU:    100m
  Memory: 64Mi

Limits:
  CPU:    500m
  Memory: 256Mi
```

## Terraform vs Helm

Terraform and Helm serve different purposes in this project.

```text
Terraform
    │
    └── Infrastructure / Kubernetes resource management

Helm
    │
    └── Application packaging and release management
```

The Terraform lab demonstrates declarative infrastructure management.

The Helm lab demonstrates Kubernetes application packaging and release lifecycle management.

Neither should be interpreted as the management mechanism for the entire core observability platform.

## Core Observability Boundary

The Terraform configuration does not manage the core:

```text
observability
```

namespace or the main Grafana observability stack.

It is a separate infrastructure-as-code lab used to demonstrate Terraform capabilities against Kubernetes.

This separation keeps the scope of the core observability deployment accurate.

## Operational Workflow

A typical workflow for the Terraform lab is:

```text
Modify Terraform configuration
          │
          ▼
terraform fmt
          │
          ▼
terraform validate
          │
          ▼
terraform plan
          │
          ▼
Review changes
          │
          ▼
terraform apply
          │
          ▼
Verify Kubernetes resources
```

For infrastructure drift:

```text
Actual infrastructure changes
          │
          ▼
terraform plan
          │
          ▼
Drift detected
          │
          ▼
terraform apply
          │
          ▼
Desired state restored
```

## Responsibility Boundaries

| Component | Responsibility |
|---|---|
| Terraform | Declaratively manages the Kubernetes resources in the lab |
| Kubernetes Provider | Connects Terraform to the Kubernetes API |
| Terraform Configuration | Defines the desired infrastructure state |
| Terraform State | Tracks managed resources |
| Kubernetes | Runs the declared infrastructure resources |
| Helm | Handles the separate application packaging/release lab |

## Summary

The Terraform lab demonstrates Infrastructure as Code against Kubernetes:

```text
Terraform
    │
    ▼
Kubernetes Provider
    │
    ▼
Kubernetes API
    │
    ▼
terraform-lab
    │
    ├── ConfigMap
    ├── Nginx Deployment
    └── Nginx Service
```

The lab also demonstrates an important operational capability:

```text
Desired State
      │
      ▼
Drift Detection
      │
      ▼
Reconciliation
      │
      ▼
Desired State Restored
```

The Terraform configuration is intentionally kept separate from the core observability platform so that the repository accurately represents which components are managed by Terraform and which are not.
