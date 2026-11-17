# 発注用の製造データ（2026-11-17 出力）

`fab/out/` は git 管理外なので、発注にそのまま使える一式をここに置いてある。作り直すときは各プロジェクトで `sh fab/export.sh` を実行する（内容と PCBWay への指定は各 `fab/README.md`）。

| ファイル | 中身 |
|---|---|
| `WPT-01-TRANSMITTER_rev7_HRTIM.zip` | 送電基板 改訂 7、HRTIM 構成。`gerber/`（4 層のガーバー、ドリル）、`assembly/HRTIM/`（`bom_HRTIM_pcbway.csv` が送る BOM、`placement_HRTIM.csv` が部品座標）、`doc/`（回路図、実装図） |
| `WPT-TX-DISPLAY_v0.2.zip` | 表示基板 v0.2（仮設計）。`gerber/`（2 層）、`assembly/`（`bom_pcbway.csv`、`placement.csv`）、`doc/` |

- 送電基板: 回路図の ERC 0 件、基板の DRC（回路図との照合つき）で新しい指摘 0 件。発注前の確認事項は `docs/stm32-tx/preorder_review.md`。
- 表示基板: ERC 0 件、DRC 0 件。表示器 DS1 は実装業者に付けさせない（BOM では LOOSE）。
- この zip は基板ファイルを変えたら古くなる。変えたら出力し直して置き換える。
