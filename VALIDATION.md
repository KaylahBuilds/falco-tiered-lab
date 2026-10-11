# Validation: evidence and limits

Authoring checks performed on 2026-10-10. These results concern this small teaching lab, not production coverage or a certification.

## Executed

- **23 offline Python tests passed** on the authoring host. They cover expected routing, duplicate grouping, distinct event identities, incomplete metadata, scope checks, malformed/oversized/duplicate-key JSON, invalid UTF-8/timestamps, omission of raw output/command lines, and generic error reporting.
- `python -m lab.triage fixtures/alerts.jsonl` succeeded: five invented records produced four review cases, including two occurrences for the shell example. Every case reported `response_executed: false`.
- The [first GitHub-hosted CI run](https://github.com/KaylahBuilds/falco-tiered-lab/actions/runs/38109861630) passed on commit `f246af67651cecec91846062d4503d269200092c`. It ran the offline tests, fixture CLI, and **native Falco 0.45.0** validation for each rule file individually and both together, and rejected the deliberate unknown-field rule.
- That initial run reported deprecated `evt.dir` conditions. The authoring revision removes those redundant predicates; see [later workflow runs](https://github.com/KaylahBuilds/falco-tiered-lab/actions/workflows/checks.yml) for commit-specific validation of subsequent changes. A passing earlier run does not validate a later commit.
- Falco/chart versions, the container field provider, and the official image digest were checked against upstream source/release evidence. See [VERSIONS.md](docs/VERSIONS.md).

## What each check proves

The native Falco `--validate` invocation checks the actual rule parser/compiler and available fields. The container plugin is registered with runtime-engine connectors disabled. The process uses `nodriver`, no host mounts other than read-only repository source, no runtime socket, no network, no added capabilities, and a nonroot user. It does not collect syscalls or exercise matching against runtime events.

The Python tests verify the behavior of an offline alert consumer. They **do not** duplicate Falco's condition evaluator, validate exception matching, replay syscalls, or prove alert delivery. The JSON fixtures are hand-authored, not recorded Falco output.

## Not executed or claimed

- No Kubernetes cluster, Helm install, privileged/capability-bearing node sensor, live rule match, live exception exercise, eBPF attachment, or cleanup run was executed during authoring.
- Local Docker, Helm, kubectl and POSIX-shell execution were not available in the authoring environment. Native container validation ran on GitHub-hosted Linux CI instead. The chart commands and Kubernetes resources have been source-reviewed, but no Helm render or Kubernetes API validation is claimed here.
- No production alert ingestion, SIEM delivery, authenticated alert channel, persistent deduplication, response integration, or automatic remediation was activated.
- No image signature/attestation was independently verified. The Falco image digest is documented from official publication evidence; remaining manual-deployment dependencies use mutable version tags.
- No admission policies, branch protection, required reviews, organization settings, or production incident procedures were configured by these examples.

For runtime acceptance, record the exact node/kernel/runtime, image digests, chart and rule revision, health and event-loss indicators, and the actual Tier 1/Tier 2 matrix results. Require positive events around negative tests. Preserve evidence privately, then clean up the exact disposable resources.
