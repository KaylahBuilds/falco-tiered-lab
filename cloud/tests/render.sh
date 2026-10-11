#!/bin/sh
# Network downloads only: no kubeconfig, cluster calls, credentials or deployment.
set -eu
cd "$(dirname "$0")/../.."
render_dir=$(mktemp -d)
trap 'rm -f "$render_dir/aks.yaml" "$render_dir/eks.yaml"; rmdir "$render_dir"' EXIT
for platform in aks eks; do
  helm template falco-lab falco \
    --repo https://falcosecurity.github.io/charts --version 9.2.0 \
    --namespace falco-system \
    -f deploy/values.yaml -f "cloud/$platform/values.yaml" \
    --set-file 'customRules.tier1\.yaml=tier-1-visibility/rules.yaml' \
    --set-file 'customRules.tier2\.yaml=tier-2-tuning/rules.yaml' \
    > "$render_dir/$platform.yaml"
  python cloud/tests/check_render.py "$platform" "$render_dir/$platform.yaml"
done
