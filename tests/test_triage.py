import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from lab import triage


ROOT = Path(__file__).resolve().parents[1]


class TriageTests(unittest.TestCase):
    def setUp(self):
        self.records = triage.read_records(ROOT / "fixtures" / "alerts.jsonl")

    def test_fixture_routes_and_duplicate(self):
        cases = triage.summarize(self.records)
        self.assertEqual([x["decision"] for x in cases], [
            "record_demo_observation", "review_shell_activity",
            "manual_review_unknown", "manual_review_incomplete"])
        self.assertEqual(cases[1]["occurrences"], 2)
        self.assertTrue(all(not x["response_executed"] for x in cases))
        self.assertTrue(all(x["human_approval_required"] for x in cases))

    def test_different_time_is_not_duplicate(self):
        event = copy.deepcopy(self.records[1])
        event["time"] = "2026-10-10T12:00:11Z"
        self.assertEqual(len(triage.summarize([self.records[1], event])), 2)

    def test_different_container_is_not_duplicate(self):
        event = copy.deepcopy(self.records[1])
        event["output_fields"]["container.id"] = "different-container"
        self.assertEqual(len(triage.summarize([self.records[1], event])), 2)

    def test_incomplete_events_are_not_deduplicated(self):
        self.assertEqual(len(triage.summarize([self.records[4]] * 2)), 2)

    def test_untrusted_output_and_commandline_are_not_copied(self):
        event = copy.deepcopy(self.records[1])
        event["output"] = "PRIVATE_RAW_OUTPUT"
        event["output_fields"]["proc.cmdline"] = "PRIVATE_COMMANDLINE"
        rendered = json.dumps(triage.summarize([event]))
        self.assertNotIn("PRIVATE", rendered)
        self.assertNotIn("proc.cmdline", rendered)

    def test_unknown_source_needs_review(self):
        event = copy.deepcopy(self.records[1])
        event["source"] = "k8s_audit"
        self.assertEqual(triage.summarize([event])[0]["decision"], "manual_review_unknown")

    def test_namespace_and_pod_and_host_scope(self):
        for key, value in (("k8s.ns.name", "production"),
                           ("k8s.pod.name", "other-pod"), ("container.id", "host")):
            with self.subTest(key=key):
                event = copy.deepcopy(self.records[1])
                event["output_fields"][key] = value
                self.assertEqual(triage.summarize([event])[0]["decision"], "manual_review_out_of_scope")

    def test_missing_and_unsafe_metadata_needs_review(self):
        for value in (None, "", "<NA>", "<NONE>", "bad\ntext", "x" * 257, 1, {}):
            with self.subTest(value=value):
                event = copy.deepcopy(self.records[1])
                event["output_fields"]["container.id"] = value
                self.assertEqual(triage.summarize([event])[0]["decision"], "manual_review_incomplete")

    def test_invalid_or_naive_time_needs_review(self):
        for value in ("invalid", "2026-10-10T12:00:00", None):
            event = copy.deepcopy(self.records[1])
            event["time"] = value
            self.assertEqual(triage.summarize([event])[0]["decision"], "manual_review_incomplete")

    def test_priority_is_not_response_authority(self):
        event = copy.deepcopy(self.records[1])
        event["priority"] = "Emergency"
        result = triage.summarize([event])[0]
        self.assertEqual(result["decision"], "review_shell_activity")
        self.assertFalse(result["response_executed"])

    def test_malformed_fields_object_is_incomplete(self):
        event = copy.deepcopy(self.records[1])
        event["output_fields"] = ["bad"]
        self.assertEqual(triage.summarize([event])[0]["decision"], "manual_review_incomplete")

    def test_cli_success(self):
        output = io.StringIO()
        with redirect_stdout(output):
            result = triage.main([str(ROOT / "fixtures" / "alerts.jsonl")])
        self.assertEqual(result, 0)
        self.assertEqual(json.loads(output.getvalue())["mode"], "offline_human_review")


class InputTests(unittest.TestCase):
    def setUp(self):
        # Keep test files in the repository's ignored scratch area, not a system temp ACL.
        scratch = ROOT / ".test-tmp"
        scratch.mkdir(exist_ok=True)
        self.directory = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "input.jsonl"

    def reject(self, data):
        self.path.write_bytes(data)
        with self.assertRaises((ValueError, UnicodeError)):
            triage.read_records(self.path)

    def test_duplicate_keys(self):
        self.reject(b'{"rule":"a","rule":"b"}')

    def test_nested_duplicate_keys(self):
        self.reject(b'{"output_fields":{"proc.name":"a","proc.name":"b"}}')

    def test_invalid_json(self):
        self.reject(b'{bad json}')

    def test_json_array(self):
        self.reject(b'[]')

    def test_nan(self):
        self.reject(b'{"value":NaN}')

    def test_empty(self):
        self.reject(b'\n \n')

    def test_invalid_utf8(self):
        self.reject(b'\xff')

    def test_byte_limit(self):
        self.reject(b' ' * (triage.MAX_BYTES + 1))

    def test_record_limit(self):
        self.reject(b'{}\n' * (triage.MAX_RECORDS + 1))

    def test_error_does_not_echo_payload(self):
        self.path.write_text('PRIVATE_NOT_JSON', encoding='utf-8')
        errors = io.StringIO()
        with redirect_stderr(errors):
            result = triage.main([str(self.path)])
        self.assertEqual(result, 2)
        self.assertNotIn("PRIVATE", errors.getvalue())

    def test_missing_file_is_reported(self):
        with redirect_stderr(io.StringIO()):
            self.assertEqual(triage.main([str(self.path)]), 2)


if __name__ == "__main__":
    unittest.main()
