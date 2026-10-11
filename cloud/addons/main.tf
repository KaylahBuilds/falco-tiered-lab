locals {
  chart_version = "9.2.0"
  values = [
    file("${path.module}/../../deploy/values.yaml"),
    file("${path.module}/../${var.platform}/values.yaml"),
    yamlencode({
      customRules = {
        "tier1.yaml" = file("${path.module}/../../tier-1-visibility/rules.yaml")
        "tier2.yaml" = file("${path.module}/../../tier-2-tuning/rules.yaml")
      }
    })
  ]
}

# Fresh dedicated namespace only. Never import/adopt a shared namespace for this demo.
resource "kubernetes_namespace_v1" "sensor" {
  metadata {
    name = "falco-system"
    labels = {
      "app.kubernetes.io/part-of"          = "falco-tiered-lab"
      "pod-security.kubernetes.io/enforce" = "privileged"
    }
  }
}

resource "helm_release" "falco" {
  name             = "falco-lab"
  repository       = "https://falcosecurity.github.io/charts"
  chart            = "falco"
  version          = local.chart_version
  namespace        = kubernetes_namespace_v1.sensor.metadata[0].name
  create_namespace = false
  values           = local.values
  atomic           = true
  cleanup_on_fail  = true
  wait             = true
  timeout          = 600
  max_history      = 3
}
