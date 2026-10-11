variable "platform" {
  description = "Select the reviewed AKS Ubuntu or EKS AL2023 managed-EC2 profile."
  type        = string
  validation {
    condition     = contains(["aks", "eks"], var.platform)
    error_message = "platform must be aks or eks."
  }
}

variable "kubeconfig_path" {
  description = "Path to an existing private kubeconfig outside this repository; not its contents."
  type        = string
  validation {
    condition     = length(trimspace(var.kubeconfig_path)) > 0
    error_message = "Set an explicit kubeconfig path."
  }
}

variable "kube_context" {
  description = "Exact context verified against the intended disposable cluster. No current-context fallback."
  type        = string
  validation {
    condition     = length(trimspace(var.kube_context)) > 0
    error_message = "Set an explicit kubeconfig context."
  }
}

variable "acknowledge_node_access" {
  description = "Must be true only after approving node-wide BPF, ptrace, host-path and runtime-socket access."
  type        = bool
  default     = false
  validation {
    condition     = var.acknowledge_node_access
    error_message = "Read cloud/README.md and approve dedicated-node instrumentation before proceeding."
  }
}
