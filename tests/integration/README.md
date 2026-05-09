# REPO-ARCH-PULSE-KG — mono-repo 統合試験

## 目的

複数 CS にまたがる統合試験を本ディレクトリに置く。
単一 CS のテストは各 CS の `tests/component/` 配下に置く。

## 親 repo の TC-INT との関係

親 repo（building-os-ecosystem）の `tests/integration/test-cases.yaml` で
定義された TC-INT-* のうち、本 mono-repo 内で完結するものはここで実行する。
複数 mono-repo を跨ぐ TC-INT は親 repo の docker-compose.full.yml で実行する。

## 実行

```bash
# 全 container を起動
docker compose -f ../deploy/docker-compose.yml up -d

# 統合試験を実行
pytest .
```
