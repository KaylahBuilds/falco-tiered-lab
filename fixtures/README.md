# Synthetic alerts, not engine replay

`alerts.jsonl` is hand-authored teaching data shaped like Falco JSON output. It is not a syscall capture, an actual Falco run, or evidence that any rule matched.

Five input records produce four review cases: a marker observation, a shell review with two occurrences, an unknown-rule manual review, and an incomplete-metadata manual review. The program does not decide whether a rule should have fired. Native Falco compilation and manual runtime exercises validate different boundaries.

The fixtures contain only invented identifiers. Do not replace them with real command lines, credentials, customer data, or production alerts in a public repository.
