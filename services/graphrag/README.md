# CS-AI-GRAPHRAG — GraphRAG Analytics Engine（CS-KG-STORE への読み手）

        CS-KG-STORE（統合 SPARQL エンドポイント）に対して GraphRAG 経路探索を実行する分析エンジン。 時系列 DB（CS-IN-TS-DB）と KG を結合した因果分析で、 引用ノード（Grain状態参照ID・期間・モデル版）を機械可読メタデータとして 経路ごとに付与し、未引用ノードからの推論を抑制する。 抽出経路は CS-AI-LLM-LOCAL / CS-AI-LLM-CLOUD に証拠ペイロードとして渡され、 ロール別レポート生成時の幻覚を抑制する。 KG ストアそのものは内包しない（CS-KG-STORE の読み手に純化）。

        **親アーキテクチャ repo**: [takashikasuya/building-os-ecosystem](https://github.com/takashikasuya/building-os-ecosystem)
                    **所属 mono-repo**: [REPO-ARCH-PULSE-KG](https://github.com/takashikasuya/arch-pulse-kg)
            **mono-repo 内パス**: `services/graphrag`


        ---

        ## 実装機能

        - FUN-ENERGY-002
- FUN-ENERGY-003

        ## インターフェース

        **Provides:**
        - (なし)

        **Consumes:**
        - IF-GOVERN-002
- IF-AI-002
- IF-INFRA-001
- IF-INFRA-002
- IF-KG-001

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
        services/graphrag/
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
