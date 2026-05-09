# CS-KG-STORE — Knowledge Graph Store（統合 KG・SPARQL endpoint・Dataspace 接続点）

        Oxigraph（ADR-002 で暫定採用）をベースとした RDF ストア。 建物意味モデルは ADR-008 で確定された SBCO LinkML スキーマ（rec/brick/gutp 統合）を 正本とし、bir 補完オントロジ（ジオメトリ参照・制御記述・モデル成果物・ シミュレーション実行記録・プロベナンス・監査）と共存させる。 bir_id を発行する正本として機能する。 ODRL ポリシー記述・DCAT カタログ・bir:hasGeometry 参照（urn:bir:geometry:*）を 含む SPARQL 1.1 / SPARQL-star エンドポイントを提供し、 Eclipse Dataspace Connector / IDS Connector への接続点として機能する。 ジオメトリペイロードは内包せず、URI 参照経由で CS-KG-GEOM へ委譲する。 起動時に SBCO LinkML を SHACL/OWL/JSON Schema にコンパイルしてバリデーション層に組み込む。

        **親アーキテクチャ repo**: [takashikasuya/building-os-ecosystem](https://github.com/takashikasuya/building-os-ecosystem)
                    **所属 mono-repo**: [REPO-ARCH-PULSE-KG](https://github.com/takashikasuya/arch-pulse-kg)
            **mono-repo 内パス**: `services/kg-store`


        ---

        ## 実装機能

        - FUN-BIR-003
- FUN-KG-001
- FUN-KG-002
- FUN-BIR-004

        ## インターフェース

        **Provides:**
        - IF-KG-001

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
        services/kg-store/
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
