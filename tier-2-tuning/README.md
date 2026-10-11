# Tier 2 — Tuned detections and scoped exceptions

[`rules.yaml`](rules.yaml) detects successful starts of `sh`, `ash`, `bash`, or `dash` in the two demo pods. The only exception is the exact tuple `(falco-demo, falco-maintenance, sh)`. Falco combines the three fields in that tuple; it does not independently allow every listed namespace, pod, or process.

Both tier rules load together in the [cluster guide](../docs/CLUSTER-LAB.md). After setup, run these commands sequentially and examine only alerts in your exercise time window:

```sh
kubectl --context "$LAB_CONTEXT" -n falco-demo exec falco-lab -- /bin/true
kubectl --context "$LAB_CONTEXT" -n falco-demo exec falco-maintenance -- /bin/true
kubectl --context "$LAB_CONTEXT" -n falco-demo exec falco-lab -- /bin/sh -c ':'
kubectl --context "$LAB_CONTEXT" -n falco-demo exec falco-maintenance -- /bin/sh -c ':'
kubectl --context "$LAB_CONTEXT" -n falco-demo exec falco-maintenance -- /bin/ash -c ':'
kubectl --context "$LAB_CONTEXT" -n falco-demo exec falco-maintenance -- /bin/true
kubectl --context "$LAB_CONTEXT" -n falco-system logs daemonset/falco-lab -c falco --since=2m --tail=500
```

`:` is a shell built-in that does nothing. The demo does not read sensitive files, create reverse shells, install packages, or contact a remote endpoint.

| Execution | Expected result |
| --- | --- |
| `true` in either demo pod | Tier 1 marker, confirming the observation path. |
| `sh` in `falco-lab` | `Lab Shell Outside Maintenance Exception`. |
| `sh` in `falco-maintenance` | No Tier 2 alert: exact teaching exception. |
| `ash` in `falco-maintenance` | Tier 2 alert: the exception is specific to `sh`. |
| Final `true` in `falco-maintenance` | Tier 1 marker, confirming the exception did not disable the sensor. |

BusyBox supplies both `/bin/sh` and `/bin/ash`. Confirm the reported `proc.name` in your environment; a different image or launch convention can alter the observed name. Missing positives, a restarted sensor, unavailable metadata, or dropped events invalidate the negative-case result. Zero alerts alone never proves an exception worked.

## Give the exception an owner and an end

For this lab, the owner is the person running the exercise, the reason is to demonstrate tuple matching, the scope is the exact tuple above, and the exception ends when the 30-minute demo is cleaned up. The YAML itself does **not** implement expiry. Delete the lab after the exercise.

In a real change record, require an owner, ticket, explicit scope, business reason, approval date, expiry, review interval, and passing positive/negative examples. An expired exception needs removal or a fresh review; set up that workflow outside Falco. Avoid broad namespace or executable allowlists merely to quiet alerts.

Pod names and process names can be imitated by someone with sufficient access. This exception is a tuning example, not a trust or authorization boundary. Protect workload creation and image promotion, preserve surrounding evidence, and use stronger identity context where available.

Native `--validate` verifies that Falco accepts the syntax and fields, including the exception. The Python suite tests alert routing, **not this condition or exception semantics**. Runtime results must come from the manual matrix or a separately reviewed native event-replay suite with real captures.
