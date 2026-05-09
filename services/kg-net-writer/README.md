# CS-KG-NET-WRITER — NetworkOverlay（SNMP/LLDP 収集・Jena TDB2 管理・SPARQL 提供）

        SNMP v2c/v3 と LLDP を用いて物理ネットワークトポロジー（スイッチ・VLAN・ポート・ デバイス接続）を 60 秒間隔で収集し、専用の Jena TDB2 NetworkOverlay ストアに書き込む。 ADR-002 に基づき、ネットワークトポロジーデータは CS-KG-STORE とは別の独立した Jena TDB2 インスタンスに分離して保持する（OT 情報保護のため）。 BACnet デバイス ID を IFC GlobalID（bir_id）に内部マッピングし、 外部 API（IF-NETWORK-002）には bir_id のみ公開する OT 情報保護を実施する。 IF-KG-001 を介して CS-KG-STORE から IFC GlobalID のルックアップを行う。 実装状況：SNMP ポーラーは Phase 2（計画中）。

        **親アーキテクチャ repo**: [takashikasuya/building-os-ecosystem](https://github.com/takashikasuya/building-os-ecosystem)
                    **所属 mono-repo**: [REPO-ARCH-PULSE-KG](https://github.com/takashikasuya/arch-pulse-kg)
            **mono-repo 内パス**: `services/kg-net-writer`


        ---

        ## 実装機能

        - FUN-NETWORK-001

        ## インターフェース

        **Provides:**
        - IF-NETWORK-002

        **Consumes:**
        - IF-NETWORK-001
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
        services/kg-net-writer/
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
