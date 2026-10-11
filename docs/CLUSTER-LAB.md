# Manual lab on a disposable Linux Kubernetes cluster

These commands are an optional exercise, not an installation performed by this repository or CI. Use an existing **single-node disposable Linux cluster** with no real workloads or data, modern eBPF/BTF support, a supported container runtime, `kubectl`, and Helm 3+. Windows Kubernetes nodes and serverless nodes that prohibit node instrumentation are outside scope. A Windows or macOS client can operate a Linux cluster; that does not make the local host a supported Falco sensor target.

The examples below use a POSIX shell. Run from the repository root. Use official [Falco kernel requirements](https://falco.org/docs/concepts/event-sources/kernel/) and [chart documentation](https://github.com/falcosecurity/charts/tree/falco-9.2.0/charts/falco) to check your node before proceeding. Do not work around admission-policy denials by loosening a shared cluster's policy.

## 1. Review the target and privileges

Set the context explicitly to the disposable cluster you reviewed:

```sh
LAB_CONTEXT='REPLACE_WITH_YOUR_DISPOSABLE_CONTEXT'
test "$LAB_CONTEXT" != 'REPLACE_WITH_YOUR_DISPOSABLE_CONTEXT'
kubectl --context "$LAB_CONTEXT" cluster-info
kubectl --context "$LAB_CONTEXT" get nodes -o wide
kubectl --context "$LAB_CONTEXT" get namespace falco-system falco-demo
helm list --kube-context "$LAB_CONTEXT" --all-namespaces
```

The two namespaces should be absent (`NotFound` is expected for that command). **Stop if either namespace or the release `falco-lab` already exists**; these names must be reserved for this fresh exercise. Verify exactly one Linux node and the intended account/context. Never paste a kubeconfig into an issue or this repository.

The sensor DaemonSet can inspect node activity outside `falco-demo`. `driver.modernEbpf.leastPrivileged: true` removes the chart's fully privileged-container default, but still grants powerful `BPF`, `PERFMON`, `SYS_PTRACE`, and `SYS_RESOURCE` capabilities and host access. Runtime sockets and host paths are sensitive. The demo pods themselves have no such permissions. No sensor option turns a shared production node into a safe playground.

The namespace's deny-all NetworkPolicy is effective only when the cluster's CNI enforces NetworkPolicy. The demo commands do not require network access. Image/plugin/chart pulls require registry connectivity from the appropriate host/node; the sensor does not forward alerts externally.

## 2. Render and inspect the exact chart

```sh
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm repo update falcosecurity
helm template falco-lab falcosecurity/falco --version 9.2.0 \
  --namespace falco-system \
  -f deploy/values.yaml \
  --set-file 'customRules.tier1\.yaml=tier-1-visibility/rules.yaml' \
  --set-file 'customRules.tier2\.yaml=tier-2-tuning/rules.yaml'
```

Review the rendered DaemonSet security context, host mounts, service account/RBAC, and images. The chart loads the container plugin for `container.*` and `k8s.*` enrichment. The optional Kubernetes metacollector is disabled; these specific pod/namespace fields come from container-runtime metadata. The plugin is version-tagged `0.7.4`, artifact-following is disabled, and no upstream detection bundle is loaded: only the two teaching rules are active. This is intentionally inadequate as a production ruleset.

The Falco image is digest-pinned; the chart, helper image, plugin, and demo image remain version-tagged. The [version record](VERSIONS.md) lists the limits of these pins. Do not assume rendering proves kernel compatibility or successful live collection.

## 3. Install the sensor, then the two demo pods

Only continue after reviewing the rendered resources and the node access they request:

```sh
helm install falco-lab falcosecurity/falco --version 9.2.0 \
  --kube-context "$LAB_CONTEXT" \
  --namespace falco-system --create-namespace \
  -f deploy/values.yaml \
  --set-file 'customRules.tier1\.yaml=tier-1-visibility/rules.yaml' \
  --set-file 'customRules.tier2\.yaml=tier-2-tuning/rules.yaml' \
  --wait --timeout 5m
kubectl --context "$LAB_CONTEXT" -n falco-system rollout status daemonset/falco-lab --timeout=180s
kubectl --context "$LAB_CONTEXT" -n falco-system logs daemonset/falco-lab -c falco --tail=100
kubectl --context "$LAB_CONTEXT" apply -f deploy/demo.yaml
kubectl --context "$LAB_CONTEXT" -n falco-demo wait --for=condition=Ready pod/falco-lab pod/falco-maintenance --timeout=120s
```

Check startup logs for both custom rules, the modern eBPF engine, container-plugin initialization, and configuration/load errors. Stop on errors and investigate before generating events. The chart may fetch its container plugin through the `falcoctl-artifact-install` init container; inspect that container's log if startup stalls. A failed install can leave resources behind; use the cleanup procedure after verifying the target.

The pods run only `sleep 1800`, with CPU/memory limits and a 30-minute active deadline. They cannot restart themselves. After the deadline, delete/recreate this lab's resources through the documented cleanup/setup sequence if you need another session.

## 4. Exercise and record evidence

Follow [Tier 1](../tier-1-visibility/README.md) and [Tier 2](../tier-2-tuning/README.md). Note your UTC start time and compare rule name, pod, process, and time for each expected alert. Let output flush before interpreting a negative result. Confirm known positive events both before and after testing the exception.

Check the same sensor's health and operational drop notices. No alert can mean no matching behavior, a broken sensor/output path, missing metadata, or lost events. If positives fail, do not call the negative case a pass. Real events in a disposable cluster are still distinct from [synthetic Tier 3 fixtures](../fixtures/README.md).

## Cleanup

First confirm `LAB_CONTEXT` still points to the same disposable cluster and **both `falco-demo` and `falco-system` contain only this lab's resources**. The demo manifest includes the `falco-demo` Namespace object: deleting that manifest deletes the entire namespace, not just its two pods. The commands below delete **all resources in both namespaces**, including any unrelated objects someone added. Stop if either namespace is shared or ownership is unclear. The inspection commands show pods and the Helm release; they are not a complete inventory of every resource type, so confirm ownership with the cluster owner as well. Namespace deletion is not recoverable from this repository; only do this for the dedicated namespaces established in Step 1.

```sh
kubectl --context "$LAB_CONTEXT" get nodes -o wide
kubectl --context "$LAB_CONTEXT" -n falco-demo get pods
kubectl --context "$LAB_CONTEXT" -n falco-system get pods
helm list --kube-context "$LAB_CONTEXT" -n falco-system
kubectl --context "$LAB_CONTEXT" delete -f deploy/demo.yaml --ignore-not-found --wait=true --timeout=120s
helm uninstall falco-lab --kube-context "$LAB_CONTEXT" --namespace falco-system --wait --timeout 3m
kubectl --context "$LAB_CONTEXT" delete namespace falco-system --ignore-not-found --wait=true --timeout=120s
kubectl --context "$LAB_CONTEXT" get namespace falco-demo falco-system
```

`NotFound` for both namespaces is the expected final result. If the Helm release never installed, `helm uninstall` may report it absent; inspect the namespace before deleting it. Falco's modern eBPF programs are expected to detach when the sensor process exits; this guide does not install a kernel module or host package. Discard the disposable cluster according to the tool that created it after reviewing any private evidence you need to retain. Do not force-delete namespaces or remove finalizers as an automatic cleanup shortcut.
