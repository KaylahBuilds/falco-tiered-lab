# Version and digest review

Reviewed 2026-10-10 using official upstream sources. Pins make changes reviewable; they do not prove the pinned software is safe or current forever.

| Component | Reviewed selection | Evidence |
| --- | --- | --- |
| Falco | `0.45.0`, released 2026-09-21 | [Official release](https://github.com/falcosecurity/falco/releases/tag/0.45.0) |
| Helm chart | `9.2.0`, `appVersion: 0.45.0` | [Tagged Chart.yaml](https://github.com/falcosecurity/charts/blob/falco-9.2.0/charts/falco/Chart.yaml) |
| Official Falco image index | `sha256:788f1129c542171813083d4afc61b16730a47dde8c23d9c39370acef996349b6` | [Upstream publish job](https://github.com/falcosecurity/falco/actions/runs/35599278127/job/106342983866) |
| Container plugin | `0.7.4`, bundled with Falco 0.45.0; chart selects this tag | [Tagged values](https://github.com/falcosecurity/charts/blob/falco-9.2.0/charts/falco/values.yaml) |
| Chart helper falcoctl | `0.14.2`, chart default | [Tagged values](https://github.com/falcosecurity/charts/blob/falco-9.2.0/charts/falco/values.yaml) |
| Demo workload | `docker.io/library/busybox:1.37.0` | [Official image tag catalog](https://github.com/docker-library/official-images/blob/master/library/busybox) |
| Actions checkout/setup-python | Full commit pins for v6 | [checkout commit](https://github.com/actions/checkout/commit/d23441a48e516b6c34aea4fa41551a30e30af803), [setup-python commit](https://github.com/actions/setup-python/commit/ece7cb06caefa5fff74198d8649806c4678c61a1) |

The Falco image digest was read from the official release job's published-image output. At `2026-09-21T13:07:01Z`, the job associates `public.ecr.aws/falcosecurity/falco:0.45.0` with that manifest-index digest. The same job records the Docker Hub promotion and an attestation subject with the same digest, tied to release commit `05d5b3e363d5196c68c8ccea842ca57a2ef05562`. This review checked upstream evidence; it did not independently verify the image signature or attestation. CI subsequently pulls by digest and runs the actual binary.

The image contains the native executable and container plugin. [`ci/falco.yaml`](../ci/falco.yaml) registers the plugin fields while disabling every container-runtime engine connector. The validator's Docker process has no capabilities, host runtime sockets, host PID namespace, or network. This is separate from the powerful node sensor in the manual chart example.

`deploy/values.yaml` uses `0.45.0@sha256:...` in the chart's image tag field because this chart constructs `registry/repository:tag`. The rendered image reference is a valid tag-plus-digest reference. The chart itself and its helper/plugin/demo dependencies are version-tagged, not all digest-locked. Automatic rule/plugin following is disabled, but the registry could move a tag. Record resolved `imageID` values when running a real exercise and review any upgrade.

For an update, review release notes and chart schema together, establish the official image digest, update the pin and this record, run native positive/negative validation, and rerun the manual positive/negative exercise on the intended kernel/runtime. Falco, driver capabilities, plugins, rules and Kubernetes metadata behavior are separate compatibility boundaries.

