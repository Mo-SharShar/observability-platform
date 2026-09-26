output "namespace_name" {
  description = "Name of the Kubernetes namespace managed by Terraform"
  value       = kubernetes_namespace.terraform_lab.metadata[0].name
}
