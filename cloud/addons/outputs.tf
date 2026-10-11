output "release_name" {
  value       = helm_release.falco.name
  description = "Owned Helm release; not proof of live syscall coverage."
}

output "namespace" {
  value       = kubernetes_namespace_v1.sensor.metadata[0].name
  description = "Dedicated namespace with a Pod Security exception for the sensor."
}
