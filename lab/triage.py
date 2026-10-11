"""Summarize synthetic Falco JSON lines for human review; never execute a response."""

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys


MAX_BYTES = 1_048_576
MAX_RECORDS = 200
KNOWN_RULES = {
    "Lab Marker Process Started": "record_demo_observation",
    "Lab Shell Outside Maintenance Exception": "review_shell_activity",
}
SAFE_FIELDS = ("k8s.ns.name", "k8s.pod.name", "container.id", "proc.name", "user.uid")
REQUIRED_FIELDS = SAFE_FIELDS[:-1]


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def read_records(path):
    """Read a bounded local JSONL file and reject the whole batch on invalid JSON."""
    with Path(path).open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("input exceeds 1 MiB")
    records = []
    for line in raw.decode("utf-8-sig").splitlines():
        if not line.strip():
            continue
        if len(records) == MAX_RECORDS:
            raise ValueError("input exceeds 200 records")
        record = json.loads(line, object_pairs_hook=unique_object,
                            parse_constant=lambda _: (_ for _ in ()).throw(ValueError("non-JSON number")))
        if not isinstance(record, dict):
            raise ValueError("each JSON line must be an object")
        records.append(record)
    if not records:
        raise ValueError("input contains no alerts")
    return records


def safe_text(value):
    if (not isinstance(value, str) or not value or len(value) > 256
            or not value.isprintable() or value in ("<NA>", "<NONE>")):
        return None
    return value


def valid_time(value):
    value = safe_text(value)
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return value if parsed.tzinfo is not None else None


def summarize(records):
    """Route reported alerts, not syscalls; Falco already made the detection decision.

    Dedupe requires complete identity metadata. It is batch-local and exact on
    selected identity fields, and does not assert authenticity or freshness.
    """
    summaries = []
    seen = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("each alert must be an object")
        fields = record.get("output_fields")
        fields = fields if isinstance(fields, dict) else {}
        selected = {key: value for key in SAFE_FIELDS
                    if (value := safe_text(fields.get(key))) is not None}
        rule = safe_text(record.get("rule"))
        source = safe_text(record.get("source"))
        timestamp = valid_time(record.get("time"))
        hostname = safe_text(record.get("hostname"))
        missing = [key for key in REQUIRED_FIELDS if key not in selected]
        missing += [key for key, value in (("rule", rule), ("source", source),
                    ("time", timestamp), ("hostname", hostname)) if value is None]
        if missing:
            decision = "manual_review_incomplete"
        elif source != "syscall" or rule not in KNOWN_RULES:
            decision = "manual_review_unknown"
        elif (selected["k8s.ns.name"] != "falco-demo"
              or selected["k8s.pod.name"] not in ("falco-lab", "falco-maintenance")
              or selected["container.id"] == "host"):
            decision = "manual_review_out_of_scope"
        else:
            decision = KNOWN_RULES[rule]
        identity = {"rule": rule, "source": source, "time": timestamp,
                    "hostname": hostname, "fields": selected}
        digest = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        if not missing and digest in seen:
            summaries[seen[digest]]["occurrences"] += 1
            continue
        item = {"case_id": digest[:16], **identity, "decision": decision,
                "occurrences": 1, "missing": missing,
                "response_executed": False, "human_approval_required": True}
        if not missing:
            seen[digest] = len(summaries)
        summaries.append(item)
    return summaries


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="local JSONL file (maximum 1 MiB / 200 alerts)")
    args = parser.parse_args(argv)
    try:
        result = summarize(read_records(args.input))
    except (OSError, ValueError, UnicodeError, RecursionError):
        # Never echo an untrusted payload or sensitive path in an error.
        print("Input rejected: provide a readable, bounded UTF-8 JSONL alert file.", file=sys.stderr)
        return 2
    print(json.dumps({"mode": "offline_human_review", "cases": result}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
