"""Offline source contracts; real Helm output is separately checked in render.sh."""
from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[2]


class CloudSourceContracts(unittest.TestCase):
    def test_profiles_require_dedicated_nodes_and_containerd(self):
        for platform in ("aks", "eks"):
            values = yaml.safe_load((ROOT / "cloud" / platform / "values.yaml").read_text())
            with self.subTest(platform=platform):
                self.assertEqual(values["nodeSelector"], {
                    "kubernetes.io/os": "linux", "kubernetes.io/arch": "amd64", "security-lab": "enabled"})
                self.assertEqual(values["controller"]["kind"], "daemonset")
                self.assertEqual(values["tolerations"], [])
                engines = values["collectors"]["containerEngine"]["engines"]
                self.assertEqual({k for k, v in engines.items() if v["enabled"]}, {"cri", "containerd"})
                self.assertFalse(values["metrics"]["service"]["create"])

    def test_existing_driver_and_forwarding_guards_remain(self):
        values = yaml.safe_load((ROOT / "deploy/values.yaml").read_text())
        self.assertEqual(values["driver"]["kind"], "modern_ebpf")
        self.assertTrue(values["driver"]["modernEbpf"]["leastPrivileged"])
        self.assertFalse(values["driver"]["loader"]["enabled"])
        self.assertFalse(values["falcosidekick"]["enabled"])
        self.assertFalse(values["responseActions"]["enabled"])

    def test_cloud_demo_is_original_demo_with_node_selection_only(self):
        base = list(yaml.safe_load_all((ROOT / "deploy/demo.yaml").read_text()))
        cloud = list(yaml.safe_load_all((ROOT / "cloud/demo.yaml").read_text()))
        for doc in base:
            if doc["kind"] == "Pod":
                doc["spec"]["nodeSelector"] = {
                    "kubernetes.io/os": "linux", "kubernetes.io/arch": "amd64", "security-lab": "enabled"}
        self.assertEqual(base, cloud)

    def test_terraform_reuses_rules_and_values(self):
        source = (ROOT / "cloud/addons/main.tf").read_text()
        for path in ("../../deploy/values.yaml", "../../tier-1-visibility/rules.yaml", "../../tier-2-tuning/rules.yaml"):
            self.assertIn(path, source)
        self.assertIn('"pod-security.kubernetes.io/enforce" = "privileged"', source)


if __name__ == "__main__":
    unittest.main()
