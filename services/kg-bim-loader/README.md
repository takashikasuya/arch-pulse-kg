# CS-KG-BIM-LOADER — BIM Loader（IFC → BIR Core → KG/Geom 書き込み）

        IFC4 / IFC2x3 ファイルを ifcopenshell + rdflib + pyshacl で解析し、 8 ステップ品質パイプライン（IFC品質チェック → Space Boundary 抽出 → Geometry Healing → LOD-G1/G2 生成 → Semantics 補完 → UC 拡張 → SHACL 検証）で BIR Core を生成して CS-KG-STORE（意味）と CS-KG-GEOM（幾何）に書き込む。 BIR 更新時の差分検出・派生モデル再生成トリガーも担当する。 品質ゲート不合格時は派生モデル生成を停止し、レポートを発行する。

        **親アーキテクチャ repo**: [takashikasuya/building-os-ecosystem](https://github.com/takashikasuya/building-os-ecosystem)
                    **所属 mono-repo**: [REPO-ARCH-PULSE-KG](https://github.com/takashikasuya/arch-pulse-kg)
            **mono-repo 内パス**: `services/kg-bim-loader`


        ---

        ## 実装機能

        - FUN-BIR-001
- FUN-BIR-002
- FUN-BIR-003
- FUN-BIR-004

        ## インターフェース

        **Provides:**
        - (なし)

        **Consumes:**
        - IF-KG-001
- IF-KG-002

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
        services/kg-bim-loader/
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
