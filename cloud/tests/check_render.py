"""Check actual Helm output; this does not prove eBPF or runtime compatibility."""
import argparse
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_rules(text):
    # Falco accepts bare '=' exception operators. PyYAML's SafeLoader assigns
    # these an unsupported YAML-1.1 value tag. Compare the rule structures as
    # strings instead; actual field/operator/type validation belongs to Falco.
    return yaml.load(text, Loader=yaml.BaseLoader)


def check(platform, documents):
    resources = [doc for doc in documents if doc]
    daemonsets = [doc for doc in resources if doc.get("kind") == "DaemonSet"]
    require(len(daemonsets) == 1, "Expected exactly one Falco DaemonSet")
    ds = daemonsets[0]
    require(ds["metadata"]["name"] == "falco-lab", "Unexpected DaemonSet name")
    require(ds["metadata"]["namespace"] == "falco-system", "Unexpected namespace")
    pod = ds["spec"]["template"]["spec"]
    require(pod["nodeSelector"] == {
        "kubernetes.io/os": "linux", "kubernetes.io/arch": "amd64",
        "security-lab": "enabled",
    }, "Sensor must remain limited to reviewed Linux/amd64 lab nodes")
    expressions = pod["affinity"]["nodeAffinity"]["requiredDuringSchedulingIgnoredDuringExecution"]["nodeSelectorTerms"][0]["matchExpressions"]
    expected_key = "kubernetes.azure.com/agentpool" if platform == "aks" else "eks.amazonaws.com/nodegroup"
    require(any(e["key"] == expected_key and e["operator"] == "Exists" for e in expressions), "Cloud node-pool constraint missing")
    require(not pod.get("tolerations"), "Lab must not tolerate arbitrary tainted nodes")
    containers = pod["containers"]
    require(len(containers) == 1 and containers[0]["name"] == "falco", "Unexpected sidecar or sensor container")
    sensor = containers[0]
    require(sensor["image"] == "public.ecr.aws/falcosecurity/falco:0.45.0@sha256:788f1129c542171813083d4afc61b16730a47dde8c23d9c39370acef996349b6", "Falco image digest changed")
    security = sensor["securityContext"]
    require(not security.get("privileged", False), "Fully privileged sensor is outside this example")
    require(set(security["capabilities"]["add"]) == {"BPF", "PERFMON", "SYS_PTRACE", "SYS_RESOURCE"}, "Unexpected sensor capabilities")
    require(not any("driver-loader" in c["name"] for c in pod.get("initContainers", [])), "Modern eBPF must not install a driver")
    volumes = {v["name"]: v for v in pod["volumes"]}
    sockets = [v for name, v in volumes.items() if name.startswith("container-engine-socket-")]
    require(len(sockets) == 1 and sockets[0]["hostPath"]["path"] == "/run/containerd", "Unexpected runtime socket mount")
    require(any(m["name"] == sockets[0]["name"] and m["mountPath"] == "/host/run/containerd" for m in sensor["volumeMounts"]), "Runtime mount mismatch")
    maps = {d["metadata"]["name"]: d["data"] for d in resources if d.get("kind") == "ConfigMap"}
    config = yaml.safe_load(maps["falco-lab"]["falco.yaml"])
    require(config["engine"]["kind"] == "modern_ebpf", "Wrong collection engine")
    require(config["json_output"] and config["stdout_output"]["enabled"], "JSON stdout required")
    require(config["rules_files"] == ["/etc/falco/rules.d"], "Unexpected rules bundle")
    for key in ("http_output", "program_output", "syslog_output"):
        require(not config[key]["enabled"], f"Unexpected forwarding/response: {key}")
    plugin = next(p for p in config["plugins"] if p["name"] == "container")
    engines = plugin["init_config"]["engines"]
    require({k for k, v in engines.items() if v["enabled"]} == {"containerd", "cri"}, "Unexpected runtime engines")
    for engine in ("containerd", "cri"):
        require(engines[engine]["sockets"] == ["/run/containerd/containerd.sock"], "Wrong socket path")
    require(config["load_plugins"] == ["container"], "Unexpected metadata plugin")
    rules = maps["falco-lab-rules"]
    for name, path in (("tier1.yaml", "tier-1-visibility/rules.yaml"), ("tier2.yaml", "tier-2-tuning/rules.yaml")):
        require(read_rules(rules[name]) == read_rules((ROOT / path).read_text()), f"Divergent {name}")
    require(set(rules) == {"tier1.yaml", "tier2.yaml"}, "Unexpected custom rules")
    for resource in resources:
        require(resource.get("kind") != "Ingress", "No public ingress in a sensor example")
        require(not (resource.get("kind") == "Service" and resource["spec"].get("type") in ("LoadBalancer", "NodePort")), "No public sensor service")
        require(not any(x in resource["metadata"]["name"] for x in ("sidekick", "talon", "metacollector")), "Unexpected forwarding or response component")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("platform", choices=["aks", "eks"])
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    check(args.platform, yaml.safe_load_all(args.manifest.read_text()))
    print(f"PASS: {args.platform} Helm render contract (not a live collection test)")
