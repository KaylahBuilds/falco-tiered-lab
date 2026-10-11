# Tier 1 — Runtime visibility

The first acceptance test is a harmless event with an expected observable result. A running DaemonSet alone is insufficient: the driver, metadata, rule, and output path must all work.

[`rules.yaml`](rules.yaml) matches a **successful process start** of `true` or `false` in `falco-demo`, limited to pods `falco-lab` and `falco-maintenance`. The `evt.failed = false` check describes the `execve` syscall, not the program's eventual exit status: `/bin/false` still starts successfully, even though the program exits with status 1. The rule is self-contained and does not depend on upstream macros.

Run the [manual cluster setup](../docs/CLUSTER-LAB.md), then use the same `LAB_CONTEXT`:

```sh
kubectl --context "$LAB_CONTEXT" -n falco-demo exec falco-lab -- /bin/true
kubectl --context "$LAB_CONTEXT" -n falco-demo exec falco-maintenance -- /bin/true
kubectl --context "$LAB_CONTEXT" -n falco-demo exec falco-lab -- /bin/sleep 1
kubectl --context "$LAB_CONTEXT" -n falco-system logs daemonset/falco-lab -c falco --since=2m --tail=500
```

Expect `Lab Marker Process Started` for each `true` execution with the correct pod and namespace, and no marker alert for the `sleep` execution. Match the timestamp and `proc.name` as well as the rule name. Startup and drop notices are separate operational evidence; do not count them as marker matches.

If either positive marker is missing, the negative case is **inconclusive**. Check sensor health, driver compatibility, container plugin/runtime-socket availability, namespace/pod enrichment, output buffering, and event-drop notices. A metadata lookup delay can make a correctly scoped rule miss the first process. Repeat a known marker after the pod and sensor are ready, and document the delay instead of broadening the rule.

Keep a private exercise record with context, node/kernel/runtime, UTC time, Falco/chart version, rule revision, expected/actual results, sensor health, and drop counters. Do not copy real logs into this public repository. See [cleanup](../docs/CLUSTER-LAB.md#cleanup).

This intentionally small rule is an observability probe. It is not a malicious-behavior detector or an inventory of everything running on the node.
