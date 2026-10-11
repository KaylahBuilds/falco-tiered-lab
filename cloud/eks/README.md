# Example: Falco on Amazon EKS

Use **EKS managed EC2 node groups with AL2023 x86_64/containerd nodes**. This path adds Falco to a disposable existing cluster. [Optional Terraform infrastructure](../terraform/README.md) is separately managed and billable. Fargate cannot run this DaemonSet; Auto Mode, Windows, Bottlerocket, ARM and custom AMIs are not validated by this example. EKS-optimized image names do not replace checking the actual kernel/BTF/runtime.

## Authenticate without static AWS keys

Use AWS CLI v2 with your approved SSO/federated role. Ensure the same identity has an EKS access entry/RBAC permitting this dedicated installation; AWS IAM permission to describe a cluster alone does not authorize Kubernetes changes. Run from a host with access to the private Kubernetes API and DNS:

```sh
aws sts get-caller-identity
aws eks describe-cluster --region YOUR_REGION --name YOUR_LAB_CLUSTER \
  --query 'cluster.{name:name,arn:arn,version:version,network:resourcesVpcConfig}'
export LAB_KUBECONFIG='/absolute/private/path/eks-falco-lab-kubeconfig'
aws eks update-kubeconfig --region YOUR_REGION --name YOUR_LAB_CLUSTER \
  --alias falco-eks-lab --kubeconfig "$LAB_KUBECONFIG"
export LAB_CONTEXT='falco-eks-lab'
kubectl --kubeconfig "$LAB_KUBECONFIG" config get-contexts
```

Replace the region/name, verify the account and ARN, and use a new private file. The kubeconfig's exec plugin obtains short-lived credentials through your AWS session. Do not store keys, tokens, or kubeconfig contents in Terraform. If authentication or endpoint access fails, fix the specific identity/network prerequisite instead of opening `0.0.0.0/0` or creating permanent admin keys.

Follow [cloud/README.md](../README.md) in order. Select `platform = "eks"` in `cloud/addons/terraform.tfvars` with the same kubeconfig/context. The profile requires `eks.amazonaws.com/nodegroup`, rejects compute-type `fargate` and `auto`, and selects Linux/amd64 nodes with `security-lab=enabled`. Maintain this label in the managed node-group Terraform configuration so replacements inherit it. The optional foundation supplies the label.

## AWS-specific acceptance criteria

1. Check the node group's AMI type is AL2023 x86_64 and actual nodes use the reviewed kernel/containerd socket. Do not silently fall back to a fully privileged kernel-module sensor on failure.
2. Verify every selected EC2 node has a ready sensor and the demo pods landed on instrumented nodes. Managed control-plane nodes, Fargate workloads and nodes outside the selected group are not covered.
3. Compare marker events, narrow shell exceptions, and sensor-drop health before and after a node-group AMI upgrade or scale operation. Falco startup success is not a guarantee against event loss.
4. Verify the VPC CNI network-policy feature is enabled and suitable for your environment before claiming the demo's deny-all policy isolates traffic. The manifest alone is not proof of enforcement.
5. No IRSA/EKS Pod Identity role is assigned to Falco in this example: local syscall collection and stdout do not require AWS API permissions. CloudTrail, EKS control-plane audit logs, and GuardDuty are distinct sources/services, not automatically enabled by this Helm release.

Use the shared [Tier 1/2/3 validation and cleanup](../README.md#tier-1-establish-node-by-node-visibility). Tear down only infrastructure this lab created, after removing add-ons while the API remains reachable. Existing EKS clusters must not be destroyed as cleanup.

Official references: [EKS optimized AMIs](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami.html), [Fargate constraints](https://docs.aws.amazon.com/eks/latest/userguide/fargate.html), [kubeconfig creation](https://docs.aws.amazon.com/eks/latest/userguide/create-kubeconfig.html), [cluster endpoint access](https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html), and [VPC CNI network policy](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy.html).
