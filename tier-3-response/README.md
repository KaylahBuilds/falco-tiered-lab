# Tier 3 — Triage and human-controlled response

An alert is evidence to review, not authority to delete a workload. This tier turns a small batch of already-produced alerts into review cases. It has no Kubernetes client, network delivery, shell execution, or automatic containment.

```sh
python -m lab.triage fixtures/alerts.jsonl
python -m unittest discover -s tests -v
```

The [fixtures](../fixtures/README.md) are synthetic. `lab.triage` is a JSON consumer, not a Falco rule simulator. It bounds input to 1 MiB and 200 records, rejects malformed or duplicate-key JSON, selects a small field set, groups complete identical identities within the batch, and routes unknown sources/rules, out-of-scope workloads, and incomplete metadata to manual review.

| Fixture | Expected decision |
| --- | --- |
| Known marker | `record_demo_observation` |
| Known shell, repeated twice | `review_shell_activity`, `occurrences: 2` |
| Unknown rule | `manual_review_unknown` |
| Missing container and pod metadata | `manual_review_incomplete` |

The tool intentionally omits raw `output` and `proc.cmdline`. It is **not a general redactor**: allowlisted namespace, pod, host, and process values can themselves be sensitive. Review any output before sharing. The case ID is a local grouping aid, not a signature or authenticated incident ID. Grouping is neither persistent nor fuzzy; differing timestamps remain separate. Incomplete alerts are kept separate rather than silently merged.

## Response checklist

1. Confirm the source and delivery channel. A plausible JSON payload is not authenticated evidence. Correlate the event time with sensor health, dropped-event indicators, workload UID/container ID, image digest, deployment revision, and audit/change records.
2. Contact the workload owner through your approved incident process. Determine whether the shell was expected and whether the exception still has a valid reason. Preserve the original evidence in an access-controlled system with a retention policy.
3. Select a proportionate response with an authorized incident lead. Identify the exact target, business impact, evidence to preserve, rollback, and a recovery owner before modifying a running service.
4. Execute only through your organization's reviewed response process. Verify the result and recovery, then update the rule or runbook with new positive and negative cases.

This repository supplies no automatic delete, kill, quarantine, cordon, or credential-revocation command. The `human_approval_required` field is documentation of intent; it is not an enforceable authorization mechanism. Do not wire this JSON output directly to a responder. Falco Talon and forwarding integrations are disabled in the lab Helm values.

Production adoption needs authenticated ingestion, access controls, clock/freshness policy, delivery retries and durable storage, alert-volume limits, on-call ownership, incident identifiers, and separate response authorization. None is established by running this small offline program.
