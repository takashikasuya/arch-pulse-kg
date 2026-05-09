# REPO-ARCH-PULSE-KG — k8s manifests
# 親 repo（building-os-ecosystem）の deploy/k8s/ に統合 manifests がある
# 本ディレクトリは mono-repo 固有の Helm chart / Kustomize overlay を置く想定

# 例:
#   helm/repo-arch-pulse-kg/
#     Chart.yaml
#     values.yaml
#     templates/
#       deployment.yaml
#       service.yaml
#       configmap.yaml
