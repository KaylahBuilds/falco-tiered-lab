# Security and data boundaries

Use this repository only with synthetic data and a disposable environment you are authorized to inspect. The default local exercises and CI do not deploy a sensor, read Kubernetes credentials, or execute a response.

The optional Falco sensor observes Linux node activity. Filtering a rule to a namespace limits matches; it does not limit the sensor's node access or what the kernel/plugin can observe. Even capability-based modern eBPF deployment is highly privileged in practical terms. Review host mounts, runtime-socket access, RBAC, admission policy, CPU/memory impact, and event loss with the cluster owner before using it elsewhere.

Alerts may contain process arguments, paths, identifiers, customer data, or secrets. The two sample rules do not request command lines, and the offline triage utility omits raw output and command-line fields, but neither constitutes a complete redaction system. Store real evidence in a private, access-controlled location with retention limits. Never commit credentials, kubeconfigs, access tokens, production logs or captures. If a credential is exposed, revoke or rotate it through the owner before attempting to remove copies.

Treat event data as untrusted input. The offline parser bounds bytes/records, rejects duplicate-key or malformed JSON, and never uses alert text as a command. Its identity hash and routing labels provide no authenticity, freshness, authorization, or durable incident tracking. An attacker could fabricate an apparently valid alert. Human review and independently authenticated source evidence are essential before action.

No automatic responder is configured. Do not attach deletion, process killing, quarantine, node cordoning, or credential revocation to a severity label or to this utility's JSON output. Such actions need target verification, explicit authority, evidence preservation, service-impact review, recovery planning, and a tested implementation outside this lab.

For repository defects, share a minimal synthetic reproduction through the repository's private vulnerability-reporting route if available. If no private route is configured, contact the maintainer privately; do not put exploit-sensitive or private environment details in a public issue. Upstream Falco vulnerabilities should follow [Falco's security policy](https://github.com/falcosecurity/falco/security/policy).

