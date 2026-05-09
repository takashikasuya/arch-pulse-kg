# CS-KG-GEOM — Geometry Resource Store（PostGIS / オブジェクトストレージ）

LOD-G1 Surface[] ポリゴン・LOD-G2 NavGraph ノード/エッジ・ LOD-G3 OccupancyGrid・LOD-G4 Detailed Surface のジオメトリペイロードを保持する。 アドレッシングは urn:bir:geometry:{uuid} で、CS-KG-STORE の bir:hasGeometry 参照解決時に HTTP / URI dereference で取得される。 PostGIS の空間関数（ST_Contains / ST_Distance 等）を活用した幾何クエリと、 ファイルストレージのバルクダウンロードの双方をサポートする。

**親アーキテクチャ repo**: [takashikasuya/building-os-ecosystem](https://github.com/takashikasuya/building-os-ecosystem)
            **所属 mono-repo**: [REPO-ARCH-PULSE-KG](https://github.com/takashikasuya/arch-pulse-kg)
    **mono-repo 内パス**: `services/kg-geom`


---

## 実装機能

- (なし)

## インターフェース

**Provides:**
- IF-KG-002

**Consumes:**
- (なし)

---

## 開発

```bash
# トレーサビリティ検証
git clone https://github.com/takashikasuya/building-os-ecosystem _architecture
pip install pyyaml
python _architecture/tools/validate_trace.py --parent _architecture --local .

# テスト
pytest tests/contract/
pytest tests/component/
```

## ディレクトリ構成

```
services/kg-geom/
  system-fragment.yaml          # 親 repo への参照・CS 宣言
  requirements/
    upstream-requirements.yaml   # 親 repo 由来（編集不可）
    local-requirements.yaml      # この CS 固有の詳細要求
  interfaces/
    provided/                    # 提供インターフェース仕様
    consumed/                    # 利用インターフェース仕様
  tests/
    contract/                    # インターフェース適合性
    component/                   # 機能・要求検証
  src/                           # 実装コード
  Dockerfile
```
