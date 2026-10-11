# Falco on AKS and EKS: Terraform examples, real coverage checks

Use the same three tiers on two managed Kubernetes platforms. The rules do not change; **node support, installation access, and the evidence needed to trust an alert do**. These are lab examples, not a production rollout or a cloud certification.

| Route | Intended nodes | Not covered by this example |
| --- | --- | --- |
| [Azure Kubernetes Service](aks/README.md) | Standard AKS, Ubuntu Linux, amd64, containerd | Windows, virtual nodes/ACI, AKS Automatic, Azure Linux, confidential/sandboxed or custom node images |
| [Amazon EKS](eks/README.md) | Managed EC2 node groups, AL2023 x86_64, containerd | Fargate, EKS Auto Mode, Windows, Bottlerocket, custom AMIs, ARM |

Exclusion means **not validated by this example**, not necessarily unsupported by Falco in every configuration. Fargate specifically cannot run the node DaemonSet used here. Falco cannot inspect managed control-plane hosts. Collect AWS/Azure control-plane and cloud audit logs separately.

## Separate infrastructure from installation

- Already have a disposable cluster? Start at the appropriate platform guide. Do **not** apply a foundation to adopt or replace it.
- Need a fresh lab? Review [the optional Terraform foundations](terraform/README.md), cost, access, quotas, supported Kubernetes version, and teardown first.
- `cloud/addons/` is a **separate Terraform root/state**. It installs one pinned Helm release and one dedicated sensor namespace on an existing, reachable cluster. It does not create the cluster, IAM identities, public endpoints, alert forwarding, or response automation.

Do not combine cluster creation and Helm installation in one apply. Keep add-on state per cluster; never point an existing state at another context or switch `platform` in place. Use an encrypted, access-controlled backend for shared work. Plans/state can contain sensitive metadata even though these examples accept no token/password variables. Keep kubeconfigs, state, plan files, local tfvars, and live logs out of Git. An init-created dependency lock file contains checksums, not secrets; review and retain it for your deployment.

## Before installation: prove the target is appropriate

Commands use a POSIX shell from the repository root, with Terraform 1.9.8+, Helm 3, kubectl, the relevant cloud CLI, and its login helper. `init` downloads providers; rendering downloads a chart. They are not fully offline commands.

Obtain a private kubeconfig using the platform guide, then set both its path and the exact context:

```sh
export LAB_KUBECONFIG='/absolute/private/path/falco-lab-kubeconfig'
export LAB_CONTEXT='REPLACE_WITH_VERIFIED_LAB_CONTEXT'
test "$LAB_CONTEXT" != 'REPLACE_WITH_VERIFIED_LAB_CONTEXT'
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" cluster-info
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" get nodes -o wide
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" get nodes -l security-lab=enabled --show-labels
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" get namespace falco-system falco-demo
helm list --kubeconfig "$LAB_KUBECONFIG" --kube-context "$LAB_CONTEXT" --all-namespaces
```

The namespaces and release `falco-lab` must be absent. Stop if names are occupied, a cluster identity is unclear, or unrelated workloads share the selected nodes. Never import an existing shared namespace into this lab's state. The optional foundations set `security-lab=enabled`; for an existing cluster, add that label through the reviewed dedicated node-pool/node-group configuration, not to arbitrary nodes. The profiles also require Linux/amd64 and the appropriate managed node-pool label. There are no blanket taint tolerations.

Before approving node access, verify all of the following:

- The operator can reach the Kubernetes API. These foundations use **private APIs**; public GitHub-hosted runners and a laptop without the private network route/DNS cannot install the add-on. Never open the API to the world just to run a demo.
- Every selected node has a Falco-compatible modern eBPF kernel, BTF, required BPF facilities, and `/run/containerd/containerd.sock`. Node OS names alone are not proof. Through an already approved node-console/debug procedure, inspect `uname -r`, `test -r /sys/kernel/btf/vmlinux`, and `test -S /run/containerd/containerd.sock`. Follow [Falco kernel requirements](https://falco.org/docs/concepts/event-sources/kernel/). Do not automatically create a privileged debug pod or weaken a shared admission policy.
- Registry access is available for the sensor, helper, plugin, and demo image. Private API does not imply air-gapped networking. The container plugin is fetched during initialization.
- Your admission controls allow the reviewed sensor in **only `falco-system`**. Terraform labels that dedicated namespace `pod-security.kubernetes.io/enforce=privileged`; the actual sensor container uses the chart's capability-limited mode, not `privileged: true`. Namespace exemption is not workload isolation.
- You accept node-wide observation: BPF, PERFMON, SYS_PTRACE, SYS_RESOURCE, AppArmor relaxation generated by the chart, host mounts, and the containerd socket directory. The socket mount is powerful and not made safe by an alert rule's namespace filter. The demo namespace stays Restricted.
- The CNI enforces NetworkPolicy before treating the demo's deny-all policy as an isolation guarantee. EKS VPC CNI network policy requires its own configuration. If enforcement is absent, record that limitation; do not claim network isolation.

## Render, review, then install with Terraform

First render both supported profiles without contacting a cluster:

```sh
python -m pip install -r requirements-cloud.txt
python -m unittest discover -s cloud/tests -v
sh cloud/tests/render.sh
terraform -chdir=cloud/addons init -backend=false
terraform -chdir=cloud/addons validate
terraform -chdir=cloud/addons test
```

The five Terraform test runs mock Helm/Kubernetes; they do not authenticate, create namespaces, or prove runtime collection. The render checks inspect the **actual chart output**, not only input YAML: DaemonSet, node selectors, modern eBPF, restricted capability set, containerd mount, both rules, JSON output, and no public endpoint/sidekick/Talon. The original native Falco rule validation is a separate CI check.

To inspect all manifests manually, substitute either `aks` or `eks`:

```sh
helm template falco-lab falco --repo https://falcosecurity.github.io/charts \
  --version 9.2.0 --namespace falco-system \
  -f deploy/values.yaml -f cloud/aks/values.yaml \
  --set-file 'customRules.tier1\.yaml=tier-1-visibility/rules.yaml' \
  --set-file 'customRules.tier2\.yaml=tier-2-tuning/rules.yaml'
```

For installation, initialize the backend you have reviewed (the example defaults to ignored local state), copy `cloud/addons/terraform.tfvars.example` to ignored `terraform.tfvars` in that directory, replace the platform/path/context, and set `acknowledge_node_access = true` **only after completing the review**. Terraform must see an existing authenticated kubeconfig; no admin credentials are embedded. Execute against the same verified context:

```sh
terraform -chdir=cloud/addons plan -out=reviewed.tfplan
# Read the entire plan: only one namespace and one Helm release are expected.
terraform -chdir=cloud/addons apply reviewed.tfplan
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" -n falco-system rollout status daemonset/falco-lab --timeout=300s
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" -n falco-system get daemonset falco-lab
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" -n falco-system get pods -o wide
```

Use the same chart/provider pins for both clouds: Falco 0.45.0, chart 9.2.0, Helm provider 3.1.1 and Kubernetes provider 2.38.0. Chart/helper/plugin/workload tags are not all immutable digests. The cloud profile changes only placement, runtime socket selection, and metrics-service exposure; it reuses the repository's actual Tier 1/2 rules. It deliberately does not install a production detection bundle.

## Tier 1: establish node-by-node visibility

Inspect logs for **each sensor pod**, not only `kubectl logs daemonset/...`, which may select one pod. Compare the selected node list to DaemonSet desired/current/ready counts and pod placement. A ready sensor on one node does not prove coverage elsewhere. Verify initialization of modern eBPF and the container plugin; inspect the `falcoctl-artifact-install` init-container log if startup fails. Record image, kernel, runtime, node name, event/drop health, and UTC test time.

Apply the bounded nonroot workload only after the sensor is healthy:

```sh
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" apply -f cloud/demo.yaml
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" -n falco-demo wait --for=condition=Ready pod/falco-lab pod/falco-maintenance --timeout=120s
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" -n falco-demo get pods -o wide
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" -n falco-demo exec falco-lab -- /bin/true
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" -n falco-system logs -l app.kubernetes.io/instance=falco-lab -c falco --since=5m --prefix=true --max-log-requests=10
```

Expect `Lab Marker Process Started` with process `true`, namespace `falco-demo`, and pod `falco-lab` on the sensor responsible for that pod's node. Both demo pods must be on nodes with ready sensors. Record which nodes actually produced test events: two pods do not exercise every node in a three-node cluster. To prove collection on each node, repeat with the same bounded demo pods recreated using a reviewed, temporary node-placement manifest; keep their exact names and security controls, and never claim marker coverage for an unexercised node. For more than ten sensor pods, inspect them individually instead of raising concurrency blindly. The pods expire after 30 minutes; they do not simulate a sustained attack or production scale.

## Tier 2: prove the exception stays narrow

Run these **only in the two lab pods**:

```sh
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" -n falco-demo exec falco-lab -- /bin/sh -c ':'
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" -n falco-demo exec falco-maintenance -- /bin/sh -c ':'
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" -n falco-demo exec falco-maintenance -- /bin/ash -c ':'
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" -n falco-demo exec falco-maintenance -- /bin/true
```

Expected shell rule: first alerts; exact maintenance `sh` does not; maintenance `ash` alerts. The final marker must still alert. Verify the process names actually observed and repeat known positives around the negative. Missing events, absent Kubernetes metadata, failed startup, or event drops make a negative **inconclusive**, not a passing suppression test. See [the full Tier 2 matrix](../tier-2-tuning/README.md).

## Tier 3: triage without automatic cloud authority

Run `python -m lab.triage fixtures/alerts.jsonl` and [the response checklist](../tier-3-response/README.md). The fixtures are invented; the tool does not interpret Falco rules, talk to Azure/AWS, cordon nodes, or terminate pods. Keep real command lines and event evidence private and sanitized. The prefixed diagnostic log command above is for human review, **not** a JSONL input file for the strict triage parser. Assign a human owner, verify the impacted node/workload, preserve approved evidence, and obtain authority before any containment.

## Cleanup: add-ons first, infrastructure last

Confirm the same account, private kubeconfig, context, state, and namespace ownership. `cloud/demo.yaml` includes a Namespace object: deleting it removes **everything in `falco-demo`**. Terraform destroy also deletes the entire owned sensor namespace. Stop if either contains unrelated resources, or another team has reused a name. There is no recoverable user data in this intended disposable lab.

```sh
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" -n falco-demo get pods
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" -n falco-system get pods
terraform -chdir=cloud/addons state list
# After ownership is confirmed:
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" delete -f cloud/demo.yaml --ignore-not-found --timeout=120s
terraform -chdir=cloud/addons plan -destroy -out=reviewed-destroy.tfplan
# Read the plan, then remove this add-on's resources only.
terraform -chdir=cloud/addons apply reviewed-destroy.tfplan
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" get namespace falco-system falco-demo
```

`NotFound` is expected. Do not force-delete namespaces or automatically remove finalizers. Only destroy a foundation if **this lab created it**, after add-on cleanup while the API is still reachable. An existing cluster must never be destroyed as add-on cleanup. Account for remaining billable infrastructure using the foundation guide.

## Upstream contracts checked

- [Falco 9.2.0 chart values](https://github.com/falcosecurity/charts/blob/falco-9.2.0/charts/falco/values.yaml) and [rendering templates](https://github.com/falcosecurity/charts/tree/falco-9.2.0/charts/falco/templates)
- [Falco Kubernetes installation](https://falco.org/docs/setup/kubernetes/) and [kernel requirements](https://falco.org/docs/concepts/event-sources/kernel/)
- [Helm provider 3.1.1 authentication/schema](https://github.com/hashicorp/terraform-provider-helm/blob/v3.1.1/docs/index.md)
- [Kubernetes namespace provider resource](https://registry.terraform.io/providers/hashicorp/kubernetes/2.38.0/docs/resources/namespace_v1)

Local syntax, mock plans, native rule validation, and Helm rendering are useful gates, not evidence that a sensor has run on AKS or EKS. No cloud resources are created by repository CI.
