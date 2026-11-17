# WPT-TX-DISPLAY: 表示基板（仮設計）

送電基板 `WPT-01-TRANSMITTER`（`../WPT-TX`）の J2 に挿す表示用の子基板。0.96 型の IPS TFT（80 × 160 画素、ST7735S）を 1 個載せる。3.3 V だけで動く。設計の考え方、重なり方の図、表示器の入手先、確かめていないことは [`docs/stm32-tx/display_shield_study.md`](../../../docs/stm32-tx/display_shield_study.md) にまとめた。

状態（2026-11-17）: 回路図の ERC 0 件、基板の DRC（回路図との照合つき）0 件。実物では組んでいない。

## ファイル

| ファイル | 内容 |
|---|---|
| `WPT-TX-DISPLAY.kicad_sch` / `.kicad_pcb` / `.kicad_pro` | 回路図（1 枚）、基板（2 層、63.4 × 29.8 mm）、プロジェクト（設計ルールは送電基板と同じ） |
| `lib/` | 表示器のシンボルとフットプリント（`WPT_Display`） |
| `tools/build.sh` | 回路図 → ERC → ネットリスト → 基板 → DRC を通して実行する |
| `tools/gen_sch.py`、`tools/schgen.py` | 回路図を書くスクリプトと、その下請け |
| `tools/make_board.py` | ネットリストから基板を作る（外形、配置、配線、ベタ、シルク） |
| `tools/make_footprint.py` | 表示器のフットプリントを作る。フレキの寸法の出どころもここに書いてある |
| `tools/drawings.py` | 文書の図 3 枚を、送電基板とこの基板のファイルから作る |
| `tools/drc_summary.py` | DRC の結果（JSON）の件数を表示する |
| `fab/export.sh`、`fab/bom_extra.csv` | 製造データの出力と、基板データに無い部品（スペーサ、ねじ） |

## 作り直す

KiCad 10（`kicad-cli` と `pcbnew` の Python モジュール）が要る。

```sh
cd hardware/kicad/WPT-TX-DISPLAY
sh tools/build.sh        # 終了コード 0 なら ERC・DRC とも 0 件
sh fab/export.sh         # fab/out/ にガーバー、ドリル、BOM、部品座標、図面
python3 tools/drawings.py ../WPT-TX/WPT-01-TRANSMITTER.kicad_pcb WPT-TX-DISPLAY.kicad_pcb \
    ../../../docs/stm32-tx/img/display_plan.png ../../../docs/stm32-tx/img/display_side.png ../../../docs/stm32-tx/img/display_board.png
```

- 回路図と基板はスクリプトが書く。定数や寸法を変えるときはスクリプトを直して `tools/build.sh` を実行する。KiCad で開いて手で直すこともできるが、スクリプトを再実行すると上書きされる。
- 基板の座標は送電基板と同じにしてある。この基板の点 (x, y) は、送電基板の同じ座標の点の 11 mm 上にある。
- `fab/out/` は git 管理外。

## 発注するとき

- 基板: 2 層、1.6 mm、63.4 × 29.8 mm。最小線幅 / 間隔 0.2 / 0.2 mm、ビア 0.6 / 0.3 mm（Tenting vias = レジストで覆う）。外形の内側の角は R1.0。
- 実装: 裏面だけ。表面実装 5 個（C1、C2、R1、R2、Q1）と、スルーホールのソケット J1（裏面に挿し、表面からはんだ付け）。
- **表示器 DS1 は実装業者に付けさせない**（BOM では LOOSE、部品座標のファイルにも入っていない）。届いてから手で付ける。手順は文書の §6.2。
- ほかに要るもの: M3 × 11 mm の両側めねじスペーサ 1 個（Harwin R30-1001102 など）、M3 × 6 mm のねじ 2 本、ポリイミドテープ、両面テープ。

## ファームウェアから見たピン

| 信号 | MCU のピン | 備考 |
|---|---|---|
| SCK / MOSI | PA5 / PA7（SPI1） | 表示器へは書き込みだけ。MISO（PA6）は使わない |
| CS / DC / RST | PA2 / PA3 / PA4 | いずれも Low で有効（DC は Low がコマンド） |
| バックライト | PB3（TIM2_CH2） | High で点灯。PWM で調光できる。駆動するまでは消灯 |
