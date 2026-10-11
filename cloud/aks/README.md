# Example: Falco on Azure Kubernetes Service

Use **standard AKS with dedicated Ubuntu Linux amd64/containerd nodes**. This is an existing-cluster add-on path; [optional Terraform infrastructure](../terraform/README.md) is separate and costs money. Virtual nodes/ACI, Windows, Automatic, Azure Linux and custom images are outside this example. Check your selected Kubernetes version and actual node image against current AKS and Falco support before provisioning.

## Authenticate without committing a kubeconfig

Install Azure CLI and the AKS `kubelogin` client on an operator machine with private API network/DNS access. Authenticate interactively or through your existing approved workload identity; do not put service-principal secrets in tfvars. Confirm the subscription and cluster before obtaining credentials:

```sh
az account show --query '{subscription:id,name:name,tenant:tenantId}'
az aks show --resource-group YOUR_LAB_RESOURCE_GROUP --name YOUR_LAB_CLUSTER \
  --query '{name:name,private:apiServerAccessProfile.enablePrivateCluster,version:kubernetesVersion,pools:agentPoolProfiles[].{name:name,os:osSKU,labels:nodeLabels}}'
export LAB_KUBECONFIG='/absolute/private/path/aks-falco-lab-kubeconfig'
az aks get-credentials --resource-group YOUR_LAB_RESOURCE_GROUP \
  --name YOUR_LAB_CLUSTER --file "$LAB_KUBECONFIG"
kubelogin convert-kubeconfig --kubeconfig "$LAB_KUBECONFIG" -l azurecli
kubectl --kubeconfig "$LAB_KUBECONFIG" config get-contexts
```

Use your exact values, a new private path, and the cluster's authorized Microsoft Entra identity. Do not add `--admin`, disable Azure RBAC, or overwrite an unrelated kubeconfig to make the example work. Identity permission and network reachability are separate prerequisites.

Set `LAB_CONTEXT` to the verified context, then follow [cloud/README.md](../README.md) in order. In `cloud/addons/terraform.tfvars`, select `platform = "aks"` with the same path/context. The Helm profile requires `kubernetes.azure.com/agentpool` and excludes virtual-kubelet nodes. A managed node pool labeled `security-lab=enabled` is the intended sensor and demo target; maintain the label in the node-pool Terraform configuration so replacement nodes inherit it.

## Azure-specific acceptance criteria

1. Confirm each selected node is Ubuntu/containerd and meets BTF/eBPF requirements, not just `Ready` in AKS.
2. Verify Azure Policy or another admission engine permits only the reviewed sensor exception. Do not exempt every namespace or disable enforcement globally. The `falco-demo` workload retains Restricted Pod Security.
3. Compare the sensor DaemonSet with the selected node pool, including after an AKS node-image upgrade or surge replacement. Repeat the Tier 1 marker and Tier 2 exception checks when nodes change.
4. Confirm the actual CNI/NetworkPolicy configuration before treating the demo deny-all policy as enforcement. Register the AKS resource ID and node name in private operational evidence; do not publish raw logs.
5. Leave forwarding off for this exercise. Falco syscall detection does not supply Azure Activity Logs, Microsoft Entra audit events, or managed control-plane audit coverage.

The acceptance exercises and cleanup are the same [three-tier workflow](../README.md#tier-1-establish-node-by-node-visibility). No Azure deployment is executed by CI.

Official references: [AKS cluster configuration](https://learn.microsoft.com/en-us/azure/aks/cluster-configuration), [AKS kubelogin](https://learn.microsoft.com/en-us/azure/aks/kubelogin-authentication), [private AKS clusters](https://learn.microsoft.com/en-us/azure/aks/private-clusters), and [AKS node labels](https://learn.microsoft.com/en-us/azure/aks/use-labels).
