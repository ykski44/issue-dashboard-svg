# Issue Dashboard SVG Generator

プレゼンテーション資料やレポートに貼り付ける、課題・タスク状況のSVGグラフ部品を生成するためのシンプルなサンプルです。

## 目的

JSON形式の集計データから、以下のSVGグラフを生成します。

- ステータス別件数：横棒グラフ
- グループ別 未完了件数（優先度別）：積み上げ横棒グラフ
- 担当区分別内訳：ドーナツチャート

グラフタイトル、優先度キー、優先度の表示名は入力JSONで指定できます。
色、フォント、文字サイズ、余白などの見た目は `config/chart_style.jsonc` で指定できます。

## 最小構成

```text
issue-dashboard-svg/
├─ AGENTS.md
├─ README.md
├─ data/
│  └─ issue_summary.sample.json
├─ config/
│  └─ chart_style.jsonc
├─ docs/
│  └─ component_spec.md
├─ output/
│  └─ .gitkeep
└─ scripts/
   └─ generate_svg.py
```

## 実行方法

Python標準ライブラリのみで動作します。

```bash
python scripts/generate_svg.py --input data/issue_summary.sample.json --output output
```

スタイル設定を明示する場合は以下のように指定します。

```bash
python scripts/generate_svg.py --input data/issue_summary.sample.json --style config/chart_style.jsonc --output output
```

出力されるファイルは以下です。

```text
output/
├─ status_bar_chart.svg
├─ team_priority_stacked_bar.svg
└─ owner_donut_chart.svg
```

## 使い方

1. `data/issue_summary.sample.json` を必要な値に更新する
2. 生成コマンドを実行する
3. `output/*.svg` をプレゼンテーション資料やドキュメントに挿入する
4. 表示崩れがある場合は、SVGをPNG化して貼り付ける

## 拡張候補

- CSVや表計算ファイルからJSONを自動生成する
- SVGをPNGへ自動変換する
- プレゼンテーションテンプレート内の画像差し替えを自動化する
- 優先度×ステータスのヒートマップもSVG化する
- 出力サイズや色の設定項目を増やす
