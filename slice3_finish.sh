#!/usr/bin/env bash
# Slice 3 仕上げスクリプト — コンポーネントテスト実行 + 証拠生成 + git commit
# Usage: bash slice3_finish.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KG_STORE_DIR="$REPO_ROOT/services/kg-store"
VENV="/tmp/kg-store-venv"

echo "=== [1/3] Python venv セットアップ ==="
if [[ ! -d "$VENV" ]]; then
  python3 -m venv "$VENV"
fi
"$VENV/bin/pip" install --quiet -e "$KG_STORE_DIR[dev]"

echo ""
echo "=== [2/3] コンポーネントテスト実行 + 証拠生成 ==="
cd "$KG_STORE_DIR"
"$VENV/bin/pytest" tests/component/ -v --tb=short
echo ""
echo "証拠ファイル: $KG_STORE_DIR/evidence/TC-COMP-KG-STORE-002.json"

echo ""
echo "=== [3/3] git commit ==="
cd "$REPO_ROOT"
git add \
  services/kg-store/system-fragment.yaml \
  services/kg-store/Dockerfile \
  services/kg-store/pyproject.toml \
  services/kg-store/run_component_tests.sh \
  services/kg-store/src/ \
  services/kg-store/tests/ \
  services/kg-store/evidence/ \
  deploy/docker-compose.yml \
  .github/workflows/validate.yaml \
  tests/integration/test_tc_int_026_027_028.py

git commit -m "$(cat <<'EOF'
feat(kg-store): Slice 3 — CS-KG-STORE Python/FastAPI 実装

- system-fragment.yaml: stack→python, IF-COLD-CATALOG/FUN-COLD-005 追加 (#3)
- CS-KG-STORE 本体: FastAPI + Oxigraph HTTP + hexagonal ports/adapters (#4)
  - TriplestoreRepository / ChangeEventPublisher port 抽象化
  - OxigraphHttpRepository (HTTP adapter, prod)
  - PyoxigraphMemRepository (in-memory adapter, tests)
  - NatsJetStreamPublisher (CloudEvents 1.0 envelope, IF-INFRA-001)
  - NullPublisher (テスト用 no-op)
- SHACL validation gate: pyshacl + bir_shapes.ttl (#5)
  - bir_id IRI pattern + status + external-ref cardinality
  - POST /bir/entities で 422 返却
- NATS event publication: bldg.{tid}.event.bir-updated.{bir_id} (#6)
- IF-KG-001 SPARQL proxy: GET/POST /sparql, POST /sparql-update
- IF-COLD-CATALOG: POST/GET /catalog/datasets
- Dockerfile: Java → Python 3.11-slim + uvicorn
- docker-compose: Oxigraph コンテナ + NATS JetStream 追加
- CI: test-kg-store ジョブ追加 (証拠アーティファクト保存)
- コンポーネントテスト: TC-INT-026/028 相当のカバレッジ
- 統合テスト: tests/integration/test_tc_int_026_027_028.py

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"

echo ""
echo "完了。次は統合テスト (docker compose up 後) を実施してください。"
