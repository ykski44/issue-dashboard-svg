# 出力SVG確認用テストケース

`data/test_cases/` 配下のJSONは、出力SVGの表示崩れや数値表現を確認するための入力データです。
いずれも `data/issue_summary.sample.json` と同じ構造で、生成スクリプトの変更なしに利用できます。

## 実行方法

各ケースを個別の出力先に生成します。

```bash
python scripts/generate_svg.py --input data/test_cases/01_standard_mix.json --output output/test_cases/01_standard_mix
python scripts/generate_svg.py --input data/test_cases/02_small_and_zero_values.json --output output/test_cases/02_small_and_zero_values
python scripts/generate_svg.py --input data/test_cases/03_large_values.json --output output/test_cases/03_large_values
python scripts/generate_svg.py --input data/test_cases/04_long_labels.json --output output/test_cases/04_long_labels
python scripts/generate_svg.py --input data/test_cases/05_priority_skew.json --output output/test_cases/05_priority_skew
```

各出力先には以下の3ファイルが生成されます。

```text
status_bar_chart.svg
team_priority_stacked_bar.svg
owner_donut_chart.svg
```

## 共通確認項目

- 3種類のSVGが生成され、ブラウザや資料貼り付け先で表示できること。
- タイトル、凡例、行ラベル、値ラベルが文字化けしていないこと。
- グラフの数値と入力JSONの値が一致していること。
- 棒、積み上げセグメント、ドーナツの色が凡例や意味と一致していること。
- 値ラベルやタイトルがSVGの外にはみ出さないこと。
- 長いラベルは、必要に応じて2行に分割され、棒やドーナツに重ならないこと。
- 完了、アーカイブなど管理完了系の色が緑またはグレー系であること。

## ケース別確認項目

### 01_standard_mix.json

通常運用に近い分布です。

- ステータス別横棒グラフで、最大値に合わせて軸と棒の長さが自然に見えること。
- 優先度別積み上げ横棒グラフで、凡例の順序とセグメントの色が一致すること。
- ドーナツチャートで、主担当と副担当の比率がおおむね 61:42 に見えること。

### 02_small_and_zero_values.json

0件と小さい値を含むケースです。

- 0件のステータスや優先度セグメントが不要に描画されないこと。
- 1件、2件の小さい値でも棒や値ラベルの表示が破綻しないこと。
- 全優先度が0件のグループでも、行ラベルと合計値が確認できること。
- ドーナツチャートで片方が小さい場合でも、凡例の値と比率が読めること。

### 03_large_values.json

大きい値を含むケースです。

- ステータス別横棒グラフで軸目盛りが最大値に合わせて拡張されること。
- 最大値の棒に付く値ラベルが右端からはみ出さないこと。
- 積み上げ横棒グラフで大きい合計値でも合計ラベルが読めること。
- ドーナツチャート中央の合計値が大きくても収まること。

### 04_long_labels.json

長い日本語ラベルを含むケースです。

- ステータス名とグループ名が棒グラフの描画領域に重ならないこと。
- 長いタイトルが上部で不自然に欠けないこと。
- 優先度名が長い場合でも凡例が読めること。
- 担当名が長い場合でもドーナツ左右のラベルが2行に分割され、ドーナツやSVG右端と重ならないこと。

### 05_priority_skew.json

優先度や担当区分が大きく偏るケースです。

- 積み上げ横棒グラフで、高・中・低のセグメント順が一定であること。
- 非常に小さいセグメントの値ラベルが無理に表示されず、見た目が崩れないこと。
- 同数の優先度を持つ行で、3色の幅が同程度に見えること。
- ドーナツチャートで 95:5 の大きな偏りが視覚的に表現されること。
