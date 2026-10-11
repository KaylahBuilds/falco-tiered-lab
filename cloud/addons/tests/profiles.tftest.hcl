mock_provider "helm" {}
mock_provider "kubernetes" {}

variables {
  platform                = "aks"
  kubeconfig_path         = "/nonexistent/mock-only-kubeconfig"
  kube_context            = "mock-only-no-cluster"
  acknowledge_node_access = true
}

run "aks_profile" {
  command = plan
  assert {
    condition     = helm_release.falco.version == "9.2.0" && helm_release.falco.atomic && !helm_release.falco.create_namespace
    error_message = "The release must stay pinned, atomic, and use the owned namespace."
  }
  assert {
    condition     = yamldecode(helm_release.falco.values[1]).nodeSelector["security-lab"] == "enabled"
    error_message = "Only reviewed lab nodes may receive the sensor."
  }
  assert {
    condition     = kubernetes_namespace_v1.sensor.metadata[0].labels["pod-security.kubernetes.io/enforce"] == "privileged"
    error_message = "The dedicated sensor namespace needs an explicit, scoped admission exception."
  }
  assert {
    condition     = yamldecode(helm_release.falco.values[2]).customRules["tier1.yaml"] == file("../../tier-1-visibility/rules.yaml")
    error_message = "Reuse the actual Tier 1 teaching rule, not a divergent copy."
  }
}

run "eks_profile" {
  command = plan
  variables {
    platform = "eks"
  }
  assert {
    condition     = yamldecode(helm_release.falco.values[1]).affinity.nodeAffinity.requiredDuringSchedulingIgnoredDuringExecution.nodeSelectorTerms[0].matchExpressions[0].key == "eks.amazonaws.com/nodegroup"
    error_message = "EKS must target managed node groups, not serverless or Auto Mode nodes."
  }
  assert {
    condition     = yamldecode(helm_release.falco.values[2]).customRules["tier2.yaml"] == file("../../tier-2-tuning/rules.yaml")
    error_message = "Reuse the actual Tier 2 teaching rule."
  }
}

run "node_access_requires_review" {
  command = plan
  variables {
    acknowledge_node_access = false
  }
  expect_failures = [var.acknowledge_node_access]
}

run "reject_unknown_platform" {
  command = plan
  variables {
    platform = "fargate"
  }
  expect_failures = [var.platform]
}

run "reject_empty_context" {
  command = plan
  variables {
    kube_context = ""
  }
  expect_failures = [var.kube_context]
}
