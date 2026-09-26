terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
}

provider "kubernetes" {
  config_path = "~/.kube/config"
}
resource "kubernetes_namespace" "terraform_lab" {
  metadata {
    name = var.namespace_name
    labels = {
      environment = "lab"
    }
  }
}
resource "kubernetes_config_map" "payment_config" {
  metadata {
    name      = "payment-config"
    namespace = kubernetes_namespace.terraform_lab.metadata[0].name
  }

  data = {
    ENVIRONMENT = "lab"
    LOG_LEVEL   = "info"
  }
}
resource "kubernetes_deployment" "nginx" {
  metadata {
    name      = "nginx"
    namespace = kubernetes_namespace.terraform_lab.metadata[0].name
  }

  spec {
    replicas = 2

    selector {
      match_labels = {
        app = "nginx"
      }
    }

    template {
      metadata {
        labels = {
          app = "nginx"
        }
      }

      spec {
        container {
          name  = "nginx"
          image = "nginx:1.29"

          port {
            container_port = 80
          }
          resources {
            requests = {
            cpu    = "100m"
            memory = "64Mi"
  }

          limits = {
            cpu    = "500m"
            memory = "256Mi"
           }
          }
        }
      }
    }
  }
}
resource "kubernetes_service" "nginx" {
  metadata {
    name      = "nginx"
    namespace = kubernetes_namespace.terraform_lab.metadata[0].name
  }

  spec {
    selector = {
      app = "nginx"
    }

    port {
      port        = 80
      target_port = 80
      protocol    = "TCP"
    }

    type = "ClusterIP"
  }
}
