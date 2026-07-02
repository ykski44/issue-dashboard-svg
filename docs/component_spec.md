# コンポーネント仕様

## 前提

資料やドキュメント側で、枠・見出し・説明文を作成する。  
このプロジェクトでは、動的に更新したいグラフ部品のみをSVGとして生成する。

## 出力コンポーネント

### 1. ステータス別件数

出力ファイル：

```text
output/status_bar_chart.svg
```

用途：

- ステータスごとの件数を横棒グラフで表示する。

推奨貼付サイズ：

```text
幅：15.5cm
高さ：5.4cm
```

推奨SVGサイズ：

```text
1465px × 510px
```

### 2. グループ別 未完了件数（優先度別）

出力ファイル：

```text
output/team_priority_stacked_bar.svg
```

用途：

- グループごとに、未完了課題を優先度別に表示する。
- 高・中・低の積み上げ横棒グラフとする。

推奨貼付サイズ：

```text
幅：16.0cm
高さ：5.4cm
```

推奨SVGサイズ：

```text
1512px × 510px
```

### 3. 担当区分別内訳

出力ファイル：

```text
output/owner_donut_chart.svg
```

用途：

- 担当区分ごとの比率をドーナツチャートで表示する。

推奨貼付サイズ：

```text
幅：7.2cm
高さ：5.0cm
```

推奨SVGサイズ：

```text
680px × 472px
```

## 入力データ構造

入力ファイル：

```text
data/issue_summary.sample.json
```

### titles

```json
{
  "status": "ステータス別件数",
  "teamPriority": "グループ別 未完了件数（優先度別）",
  "owner": "担当区分別内訳"
}
```

各SVG内に表示する小さなタイトルとして使われる。

### priorities

```json
[
  { "key": "prior1", "name": "高" },
  { "key": "prior2", "name": "中" },
  { "key": "prior3", "name": "低" }
]
```

`key` は `teamPriority` の件数キー、`name` は凡例の表示名として使われる。
色は `config/chart_style.jsonc` の `colors.priority` で定義する。

## スタイル設定

スタイル設定ファイル：

```text
config/chart_style.jsonc
```

標準ライブラリのみで動作させるため、`//` コメントを取り除いてJSONとして読み込む。
このファイルでは、色、フォント、文字サイズ、SVGサイズ、余白、棒の太さ、角丸、ドーナツ半径などを定義する。

### status

```json
[
  { "name": "新規", "value": 18 },
  { "name": "対応中", "value": 52 }
]
```

### teamPriority

```json
[
  { "team": "グループA", "prior1": 2, "prior2": 18, "prior3": 10 }
]
```

`team` がグループ別グラフの表示名として使われる。
`prior1`、`prior2`、`prior3` などのキーは `priorities[].key` と一致させる。

### owner

```json
{
  "primary": { "name": "担当A", "value": 61 },
  "secondary": { "name": "担当B", "value": 42 }
}
```

`primary.name` と `secondary.name` がドーナツチャートの表示名として使われる。
既存の `{ "primary": 61, "secondary": 42 }` 形式も読み取り可能だが、表示名を変えたい場合は上記形式を使う。

## 色の基本ルール

| 区分 | 色 |
|---|---|
| prior1 | 赤系 |
| prior2 | 橙・黄系 |
| prior3 | 青系 |
| 完了 | 緑系 |
| アーカイブ | グレー系 |
| 担当B | 緑系 |
| 担当A | 青系 |

## 運用上の注意

- SVGのまま貼って崩れる場合はPNGに変換して貼り付ける。
- 外部共有時に元データを埋め込みたくない場合は、PNG貼付も選択肢とする。
- 貼付先の枠サイズを正とし、SVG出力サイズをそれに合わせる。
- グラフタイトルは貼付先で持つ前提。ただし単体確認しやすいよう、SVG内にも小さなタイトルを入れてよい。
- 貼付先のパネル枠と干渉しないよう、SVG自体には外枠やカード背景を描かない。
- 積み上げ棒グラフは、`priorities` で定義した凡例、棒内の値ラベル、下部の目盛りをSVG内に含める。
