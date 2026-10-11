#!/bin/sh
set -eu

# Run from the repository root. Source and evidence: docs/VERSIONS.md.
FALCO_IMAGE='public.ecr.aws/falcosecurity/falco:0.45.0@sha256:788f1129c542171813083d4afc61b16730a47dde8c23d9c39370acef996349b6'
test -f tier-1-visibility/rules.yaml
test -f tier-2-tuning/rules.yaml
docker pull "$FALCO_IMAGE"

validate() {
  docker run --rm --network none --read-only --user 65534:65534 \
    --cap-drop ALL --security-opt no-new-privileges \
    --pids-limit 64 --memory 512m --cpus 1 \
    --tmpfs /tmp:rw,noexec,nosuid,size=16m \
    --mount "type=bind,src=$PWD,dst=/workspace,readonly" \
    --entrypoint /usr/bin/falco "$FALCO_IMAGE" \
    -c /workspace/ci/falco.yaml "$@"
}

validate --version
validate -V /workspace/tier-1-visibility/rules.yaml
validate -V /workspace/tier-2-tuning/rules.yaml
validate -V /workspace/tier-1-visibility/rules.yaml -V /workspace/tier-2-tuning/rules.yaml

# A native error is expected; a Docker/permission error alone is not a passing test.
if invalid_output=$(validate -V /workspace/ci/invalid-rule.yaml 2>&1); then
  printf '%s\n' 'ERROR: Falco accepted the deliberate unknown-field rule.' >&2
  exit 1
fi
printf '%s\n' "$invalid_output"
printf '%s\n' "$invalid_output" | grep -F 'lab.definitely_missing_field' >/dev/null
printf '%s\n' 'Native positive rule validation and unknown-field rejection passed.'
