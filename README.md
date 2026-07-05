# arch-pulse-kg

> ⚠️ **このリポジトリはアーカイブされました（2026-07、モノレポ化 ADR-028 / building-os-ecosystem#108）。**
> 実装は **[building-os-ecosystem/impl/kg](https://github.com/takashikasuya/building-os-ecosystem/tree/master/impl/kg)** に履歴ごと集約されました。以後の開発・Issue はモノレポ側で行ってください。

> Mono-repo で内包する複数の CS（Constituent System）の実装を保持する。
> 親アーキテクチャ正本: [takashikasuya/building-os-ecosystem](https://github.com/takashikasuya/building-os-ecosystem)
> 関連 ADR: [ADR-009 CS↔Repository N:1 mapping](https://github.com/takashikasuya/building-os-ecosystem/blob/main/docs/adr/ADR-009-cs-repository-realization-mapping.md)

## メタデータ

| | |
|---|---|
| Repository ID | `REPO-ARCH-PULSE-KG` |
| Type | `monorepo` |
| Phase | `1` |
| Primary Language | `mixed` |

## 内包する CS

| CS ID | 名称 | path_in_repo | Container |
|---|---|---|---|
| `CS-KG-STORE` | Knowledge Graph Store（統合 KG・SPARQL endpoint・Dataspace 接続点） | `services/kg-store` | `kg-store` |
| `CS-KG-GEOM` | Geometry Resource Store（PostGIS / オブジェクトストレージ） | `services/kg-geom` | `kg-geom` |
| `CS-KG-BIM-LOADER` | BIM Loader（IFC → BIR Core → KG/Geom 書き込み） | `services/kg-bim-loader` | `kg-bim-loader` |
| `CS-KG-NET-WRITER` | NetworkOverlay（SNMP/LLDP 収集・Jena TDB2 管理・SPARQL 提供） | `services/kg-net-writer` | `kg-net-writer` |
| `CS-AI-GRAPHRAG` | GraphRAG Analytics Engine（CS-KG-STORE への読み手） | `services/graphrag` | `ai-graphrag` |

## ディレクトリ構成

各 CS は `path_in_repo` に従ってサブディレクトリを持つ。
各サブディレクトリ内の構成は単一 CS repo と同じ：

```
<path_in_repo>/
  system-fragment.yaml          # 親 repo への参照・CS 宣言
  requirements/
    upstream-requirements.yaml
    local-requirements.yaml
  interfaces/{provided,consumed}/
  tests/{contract,component}/
  src/
  Dockerfile
  README.md
```

repo ルートには：

```
.
├── README.md（本ファイル）
├── .gitignore
├── .github/workflows/validate.yaml   # mono-repo CI（CS 別 matrix）
├── deploy/
│   ├── docker-compose.yml             # ローカル開発用（全 container）
│   └── k8s/                           # k8s manifests（必要に応じて）
└── tests/integration/                 # mono-repo 全体の統合試験
```

## 開発

```bash
# トレーサビリティ検証（mono-repo 全 CS）
git clone https://github.com/takashikasuya/building-os-ecosystem _architecture
pip install pyyaml
for cs_path in $(find . -name system-fragment.yaml -not -path './_architecture/*' | xargs -n1 dirname); do
  python _architecture/tools/validate_trace.py --parent _architecture --local "$cs_path"
done

# 全 container をローカル起動
docker compose -f deploy/docker-compose.yml up -d

# 統合試験
pytest tests/integration/
```

## トレーサビリティ

各 CS の上位要求・機能・インターフェースは親 repo の YAML 正本にあり、
本 mono-repo 内の `system-fragment.yaml` 経由で参照される。

設計変更は **必ず親 repo を先に更新**し、次に本 mono-repo の対応する
ファイルを更新すること。

---

*この repo は `tools/generate_repo.py --repository REPO-ARCH-PULSE-KG` で生成されたスケルトン。*
