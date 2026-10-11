# Falco runtime security: three practical tiers

**Observe a known event. Tune with evidence. Respond with a human in control.**

Companion to [the Falco runtime security field note](https://kaylahbuilds.io/#/blog/falco-runtime-security-tiers) by Kaylah Builds.

This lab pairs actual Falco rules with a small Kubernetes exercise and an offline alert-triage program. These are **our adoption tiers**, not official Falco maturity levels, certifications, or evidence of production coverage.

| Tier | Question | Working example | Evidence boundary |
| --- | --- | --- | --- |
| [1 — Runtime visibility](tier-1-visibility/README.md) | Can a known event travel from this node to an alert? | Successful marker process executions in two named demo pods. | A rule compiling does not prove the sensor collected or delivered an event. |
| [2 — Tuned detections](tier-2-tuning/README.md) | Does a narrow exception leave nearby activity visible? | Shell-start rule with an exact namespace, pod, and process tuple; positive and negative exercises. | Matching pod/process names is not authenticated authorization. |
| [3 — Triage and response](tier-3-response/README.md) | Can a person interpret and safely act on the alert? | Bounded JSONL parsing, duplicate grouping, unknown/incomplete routing, and a response checklist. | Synthetic JSON is not syscall replay; no response is executed. |

Higher tiers retain earlier checks. Falco observes events and evaluates rules; it does not make this application secure, prevent every attack, or replace admission policy, audit logs, patching, and ownership.

## Start without a cluster

Requires Python 3.11+ and its standard library. From the repository root:

```sh
python -m unittest discover -s tests -v
python -m lab.triage fixtures/alerts.jsonl
```

Use `python3` or `py -3` if appropriate. Five invented alert records become four review cases. The duplicate shell record has `occurrences: 2`; unknown and incomplete alerts require manual review. Every case has `response_executed: false`. These commands use no credentials, network, third-party Python packages, or Kubernetes access.

## Validate with the actual Falco engine

On a Linux Docker host, the optional command below pulls the pinned official Falco 0.45.0 image and compiles both rules. It also verifies that an intentionally invalid field is rejected:

```sh
sh ci/validate-rules.sh
```

The container runs as a nonroot user, without added capabilities, with no network, read-only files, and no host PID namespace or runtime socket. It loads the bundled container plugin to register fields, with every runtime-engine connector disabled. `--validate` exits after compilation; it does not attach an eBPF program, install a host sensor, or replay events. The image pull itself requires network access. See [the version and digest evidence](docs/VERSIONS.md).

The active GitHub workflow runs these native checks and the offline Python suite with `contents: read`, no persisted checkout credentials, no secrets, and no publishing/deployment steps. [VALIDATION.md](VALIDATION.md) distinguishes executed checks from proposed runtime exercises.

## Optional runtime exercise

Follow [the disposable-cluster guide](docs/CLUSTER-LAB.md) only on a Linux cluster you own and may discard. The two demo pods are nonroot, have no service-account token, drop all capabilities, and terminate after 30 minutes. **The Falco node sensor has substantially greater access:** BPF, performance, ptrace, resource capabilities, host paths and runtime sockets. Its visibility is node-wide even though the rules filter to a demo namespace. Namespace scoping does not isolate the sensor.

No cluster is installed or modified by the offline examples or CI. The runtime guide is manual, and Falcosidekick forwarding and Falco Talon response actions are disabled. Current reviewed versions are Falco **0.45.0** and Helm chart **9.2.0**, checked on 2026-10-10. The optional BusyBox workload and container plugin use version tags; those tags are mutable. This repository does not claim a fully digest-locked deployment.

## Layout

```text
tier-1-visibility/       Marker rule and visibility acceptance checks
tier-2-tuning/           Shell rule, exact exception, and regression matrix
tier-3-response/         Offline triage exercise and human response runbook
deploy/                 Manual-only Helm values and bounded demo pods
ci/                     Native Falco validation without collection privileges
lab/                    Standard-library alert-routing utility
fixtures/               Explicitly synthetic Falco-shaped JSON records
tests/                  Input-handling and routing tests, not a rule interpreter
docs/                   Manual cluster guide and upstream version evidence
.github/workflows/      Read-only native validation and offline tests
```

Start with [SECURITY.md](SECURITY.md) before handling real event data. Do not commit kubeconfigs, tokens, command lines containing secrets, unsanitized logs, or production captures.

## Official references

- [Falco concepts](https://falco.org/docs/concepts/)
- [Rule exceptions](https://falco.org/docs/concepts/rules/exceptions/)
- [Falco command-line arguments](https://falco.org/docs/reference/daemon/cli-arguments/)
- [Container plugin and Kubernetes metadata](https://github.com/falcosecurity/plugins/tree/main/plugins/container)
- [Falco Helm chart](https://github.com/falcosecurity/charts/tree/falco-9.2.0/charts/falco)

