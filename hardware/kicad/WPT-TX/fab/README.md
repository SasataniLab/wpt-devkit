# 発注用データの出力

`fab/export.sh` を実行すると、`fab/out/` に製造・実装用のデータ一式が出力される（KiCad 10 の `kicad-cli` が必要、`fab/out/` は git 管理外）。

```sh
sh hardware/kicad/WPT-TX/fab/export.sh
```

## 出力内容

| フォルダ | 内容 |
|---|---|
| `out/gerber/` | 4 層分の銅箔（F / In1 / In2 / B）、レジスト、ペースト、シルク、外形のガーバーと、Excellon ドリル（PTH / NPTH 別ファイル）、ドリルマップ |
| `out/assembly/Legacy/` | Legacy 構成の BOM（`bom_Legacy.csv`）と部品座標（`placement_Legacy.csv`） |
| `out/assembly/HRTIM/` | HRTIM 構成の BOM と部品座標 |
| `out/doc/` | 回路図 PDF、表面・裏面の実装図（DNP 部品は × 印） |

- BOM は「同じ値・フットプリント・型番」で 1 行にまとめ、DNP の部品は含めない。列は Designator / Qty / Value / Footprint / Manufacturer / Mfg Part #。
- 部品座標は mm 単位、表裏両面、DNP を除外。
- Legacy / HRTIM の違いは LM5113 入力まわりの 12 点だけ（設計まとめ §21.1）。**両方を同時に実装しないこと。**

## 発注時に確認すること

以下は基板側の事実で、実装業者の仕様との照合はまだ行っていない。

- 4 層、外形 70 × 65 mm。最小配線幅 / 間隔 0.2 mm / 0.2 mm、ビア 0.6 mm / 穴 0.3 mm、銅箔–基板端 0.3 mm 以上。
- 両面実装。裏面にも 0402 を中心に部品がある。
- EPC2007C（バンプ実装の GaN FET）と LM5113-Q1（WSON）はリフロー必須。
- スルーホール部品: ピンヘッダ J1〜J4 / J301、エンコーダ SW1、スライドスイッチ SW2、既存の電源コネクタ類。
- 型番が空欄の部品（ピンヘッダ、テストポイント）は BOM 上で手配対象から外すか、支給品にする。
- 捨て基板とフィデューシャルは基板データに含めていない。必要なら実装業者側で付けてもらう。
