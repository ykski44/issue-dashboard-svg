#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
課題・タスク状況ダッシュボード用SVGグラフ生成スクリプト。

実行例:
    python scripts/generate_svg.py --input data/issue_summary.sample.json --output output

外部ライブラリなしで動作する最小実装。
"""

from __future__ import annotations

import argparse
import html
import json
import math
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_STYLE_PATH = Path(__file__).resolve().parents[1] / "config" / "chart_style.jsonc"

def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def strip_jsonc_comments(text: str) -> str:
    result = []
    in_string = False
    escape = False
    i = 0
    while i < len(text):
        char = text[i]
        next_char = text[i + 1] if i + 1 < len(text) else ""

        if in_string:
            result.append(char)
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            i += 1
            continue

        if char == '"':
            in_string = True
            result.append(char)
            i += 1
            continue

        if char == "/" and next_char == "/":
            while i < len(text) and text[i] not in "\r\n":
                i += 1
            continue

        result.append(char)
        i += 1

    return "".join(result)


def load_jsonc(path: Path) -> Dict[str, Any]:
    return json.loads(strip_jsonc_comments(path.read_text(encoding="utf-8")))


def style_value(style: Dict[str, Any], path: str, default: Any) -> Any:
    value: Any = style
    for key in path.split("."):
        if not isinstance(value, dict) or key not in value:
            return default
        value = value[key]
    return value


def style_int(style: Dict[str, Any], path: str, default: int) -> int:
    return int(style_value(style, path, default))


def style_float(style: Dict[str, Any], path: str, default: float) -> float:
    return float(style_value(style, path, default))


def style_str(style: Dict[str, Any], path: str, default: str) -> str:
    return str(style_value(style, path, default))


def text_size(style: Dict[str, Any], name: str, default: int) -> int:
    return style_int(style, f"textStyles.{name}.size", default)


def text_weight(style: Dict[str, Any], name: str, default: str) -> str:
    return style_str(style, f"textStyles.{name}.weight", default)


def svg_text(x: float, y: float, text: Any, size: int = 22, weight: str = "400",
             fill: str = "#111827", anchor: str = "start",
             font_family: str = "Yu Gothic, Meiryo, Arial, sans-serif") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="{esc(font_family)}" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">'
        f'{esc(text)}</text>'
    )


def estimated_text_units(text: str) -> float:
    units = 0.0
    for char in text:
        code = ord(char)
        if char in " \t":
            units += 0.35
        elif char in "-/()[]{}.,:;":
            units += 0.45
        elif code < 128:
            units += 0.55
        elif 0xFF61 <= code <= 0xFF9F:
            units += 0.55
        else:
            units += 1.0
    return units


def split_label_line(text: str, max_units: float) -> List[str]:
    text = text.strip()
    if not text or estimated_text_units(text) <= max_units:
        return [text]

    break_chars = " 　・/-／（）()［］[]"
    preferred_suffixes = [
        "グループ",
        "チーム",
        "主担当",
        "副担当",
        "担当",
        "確認待ち",
        "アーカイブ",
        "受付",
        "対応中",
        "対応",
    ]
    candidates = []
    preferred_indexes = set()
    for suffix in preferred_suffixes:
        idx = text.find(suffix)
        if idx > 0:
            preferred_indexes.add(idx)

    for idx in range(1, len(text)):
        left = text[:idx].rstrip()
        right = text[idx:].lstrip()
        if not left or not right:
            continue
        left_units = estimated_text_units(left)
        right_units = estimated_text_units(right)
        if left_units > max_units or right_units > max_units:
            continue
        preferred = idx in preferred_indexes or text[idx - 1] in break_chars or text[idx] in break_chars
        balance = abs(left_units - right_units)
        center_distance = abs(idx - len(text) / 2)
        candidates.append((0 if preferred else 1, balance, center_distance, left, right))

    if candidates:
        _, _, _, left, right = min(candidates)
        return [left, right]

    left = ""
    for idx in range(1, len(text) + 1):
        candidate = text[:idx].rstrip()
        if estimated_text_units(candidate) > max_units:
            break
        left = candidate

    if not left:
        return [text]

    return [left, text[len(left):].lstrip()]


def wrap_label_text(text: Any, max_width: float, size: int, max_lines: int = 2) -> List[str]:
    max_units = max(max_width / max(size, 1), 1)
    lines: List[str] = []
    for raw_line in str(text).splitlines() or [""]:
        for line in split_label_line(raw_line, max_units):
            lines.append(line)

    if len(lines) <= max_lines:
        return lines

    return lines[:max_lines - 1] + ["".join(lines[max_lines - 1:])]


def svg_wrapped_text(x: float, y: float, text: Any, max_width: float,
                     size: int = 22, weight: str = "400",
                     fill: str = "#111827", anchor: str = "start",
                     font_family: str = "Yu Gothic, Meiryo, Arial, sans-serif",
                     line_height: float = 1.1) -> str:
    lines = wrap_label_text(text, max_width, size)
    if len(lines) == 1:
        return svg_text(x, y, lines[0], size=size, weight=weight, fill=fill, anchor=anchor, font_family=font_family)

    line_gap = size * line_height
    first_y = y - line_gap / 2
    tspans = [
        f'<tspan x="{x:.1f}" y="{first_y:.1f}">{esc(lines[0])}</tspan>',
        *[
            f'<tspan x="{x:.1f}" dy="{line_gap:.1f}">{esc(line)}</tspan>'
            for line in lines[1:]
        ],
    ]
    return (
        f'<text font-family="{esc(font_family)}" font-size="{size}" font-weight="{weight}" '
        f'fill="{fill}" text-anchor="{anchor}">'
        f'{"".join(tspans)}</text>'
    )


def svg_header(title: str, width: int, height: int, style: Dict[str, Any], chart_key: str) -> List[str]:
    font_family = style_str(style, "fontFamily", "Yu Gothic, Meiryo, Arial, sans-serif")
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f"<title>{esc(title)}</title>",
        svg_text(
            style_float(style, f"{chart_key}.titleX", 28),
            style_float(style, f"{chart_key}.titleY", 42),
            title,
            size=text_size(style, "title", 22),
            weight=text_weight(style, "title", "700"),
            fill=style_str(style, "colors.heading", "#1E3A8A"),
            font_family=font_family,
        ),
    ]


def svg_footer() -> str:
    return "</svg>\n"


def chart_title(titles: Dict[str, Any], key: str, default: str) -> str:
    return str(titles.get(key, default))


def priority_key(priority: Dict[str, Any], index: int) -> str:
    return str(priority.get("key", f"prior{index + 1}"))


def priority_name(priority: Dict[str, Any], key: str) -> str:
    return str(priority.get("name", key))


def priority_color(priority: Dict[str, Any], index: int, style: Dict[str, Any]) -> str:
    key = priority_key(priority, index)
    default_colors = ["#DC2626", "#F59E0B", "#2563EB"]
    default = default_colors[index] if index < len(default_colors) else "#6B7280"
    return style_str(style, f"colors.priority.{key}", default)


def default_priorities() -> List[Dict[str, Any]]:
    return [
        {"key": "prior1", "name": "高"},
        {"key": "prior2", "name": "中"},
        {"key": "prior3", "name": "低"},
    ]


def axis_ticks(axis_max: int, tick_step: int) -> List[int]:
    ticks = list(range(0, axis_max + 1, tick_step))
    if not ticks or ticks[-1] != axis_max:
        if ticks and axis_max - ticks[-1] < tick_step / 2:
            ticks.pop()
        ticks.append(axis_max)
    return ticks


def chart_tick_step(style: Dict[str, Any], chart_key: str, axis_max: int, default_min_step: int) -> int:
    fixed_step = style_int(style, f"{chart_key}.tickStep", 0)
    if fixed_step > 0:
        return fixed_step
    return max(default_min_step, axis_max // 5)


def generate_status_bar_chart(status_rows: List[Dict[str, Any]], title: str, style: Dict[str, Any], out_path: Path) -> None:
    font_family = style_str(style, "fontFamily", "Yu Gothic, Meiryo, Arial, sans-serif")
    width = style_int(style, "statusChart.width", 1465)
    height = style_int(style, "statusChart.height", 510)
    margin_left = style_int(style, "statusChart.marginLeft", 170)
    margin_right = style_int(style, "statusChart.marginRight", 90)
    chart_top = style_int(style, "statusChart.chartTop", 86)
    row_h = style_int(style, "statusChart.rowHeight", 58)
    bar_h = style_int(style, "statusChart.barHeight", 26)
    bar_radius = style_int(style, "statusChart.barRadius", 13)
    label_x = style_int(style, "statusChart.labelX", 32)
    value_gap = style_int(style, "statusChart.valueGap", 14)
    chart_w = width - margin_left - margin_right
    max_value = max((int(row.get("value", 0)) for row in status_rows), default=1)
    axis_round_step = style_int(style, "statusChart.axisRoundStep", 50)
    axis_max = max(10, math.ceil(max_value / axis_round_step) * axis_round_step)

    parts = svg_header(title, width, height, style, "statusChart")

    tick_step = chart_tick_step(style, "statusChart", axis_max, style_int(style, "statusChart.tickMinStep", 10))
    for tick in axis_ticks(axis_max, tick_step):
        x = margin_left + chart_w * tick / axis_max
        parts.append(f'<line x1="{x:.1f}" y1="{chart_top - style_int(style, "statusChart.gridTopOffset", 20)}" x2="{x:.1f}" y2="{height - style_int(style, "statusChart.gridBottomOffset", 58)}" stroke="{style_str(style, "colors.grid", "#E5E7EB")}" stroke-width="1"/>')
        parts.append(svg_text(x, height - style_int(style, "statusChart.axisLabelBottomOffset", 24), tick, size=text_size(style, "axis", 16), weight=text_weight(style, "axis", "400"), fill=style_str(style, "colors.muted", "#6B7280"), anchor="middle", font_family=font_family))

    for i, row in enumerate(status_rows):
        name = row.get("name", "")
        value = int(row.get("value", 0))
        kind = row.get("kind", "open")
        color = style_str(style, f"colors.status.{kind}", style_str(style, "colors.status.open", "#2563EB"))
        y = chart_top + i * row_h
        bar_w = chart_w * value / axis_max if axis_max else 0

        parts.append(svg_wrapped_text(label_x, y + style_int(style, "statusChart.rowLabelBaselineOffset", 24), name, max_width=margin_left - label_x - style_int(style, "statusChart.labelRightPadding", 12), size=text_size(style, "label", 22), weight=text_weight(style, "label", "600"), fill=style_str(style, "colors.text", "#111827"), font_family=font_family))
        parts.append(f'<rect x="{margin_left}" y="{y}" width="{chart_w}" height="{bar_h}" rx="{bar_radius}" fill="{style_str(style, "colors.track", "#F3F4F6")}"/>')
        parts.append(f'<rect x="{margin_left}" y="{y}" width="{bar_w:.1f}" height="{bar_h}" rx="{bar_radius}" fill="{color}"/>')
        value_x = min(margin_left + bar_w + value_gap, width - style_int(style, "statusChart.valueRightPadding", 48))
        parts.append(svg_text(value_x, y + style_int(style, "statusChart.valueBaselineOffset", 22), value, size=text_size(style, "value", 21), weight=text_weight(style, "value", "700"), fill=style_str(style, "colors.text", "#111827"), font_family=font_family))

    parts.append(svg_footer())
    out_path.write_text("\n".join(parts), encoding="utf-8")


def generate_team_priority_stacked_bar(rows: List[Dict[str, Any]], priorities: List[Dict[str, Any]], title: str, style: Dict[str, Any], out_path: Path) -> None:
    font_family = style_str(style, "fontFamily", "Yu Gothic, Meiryo, Arial, sans-serif")
    width = style_int(style, "teamPriorityChart.width", 1512)
    height = style_int(style, "teamPriorityChart.height", 510)
    margin_left = style_int(style, "teamPriorityChart.marginLeft", 220)
    margin_right = style_int(style, "teamPriorityChart.marginRight", 105)
    chart_top = style_int(style, "teamPriorityChart.chartTop", 114)
    row_h = style_int(style, "teamPriorityChart.rowHeight", 78)
    bar_h = style_int(style, "teamPriorityChart.barHeight", 32)
    bar_radius = style_int(style, "teamPriorityChart.barRadius", 16)
    segment_radius = style_int(style, "teamPriorityChart.segmentRadius", 8)
    label_x = style_int(style, "teamPriorityChart.labelX", 32)
    chart_w = width - margin_left - margin_right
    priorities = priorities or default_priorities()

    totals = [
        sum(int(r.get(priority_key(priority, idx), 0)) for idx, priority in enumerate(priorities))
        for r in rows
    ]
    max_total = max(totals, default=1)
    axis_round_step = style_int(style, "teamPriorityChart.axisRoundStep", 10)
    axis_max = max(10, math.ceil(max_total / axis_round_step) * axis_round_step)

    parts = svg_header(title, width, height, style, "teamPriorityChart")

    legend_x = width - style_int(style, "teamPriorityChart.legendRight", 365)
    legend_y = style_int(style, "teamPriorityChart.legendY", 34)
    legend_step = style_int(style, "teamPriorityChart.legendStep", 105)
    swatch_size = style_int(style, "teamPriorityChart.legendSwatchSize", 22)
    swatch_radius = style_int(style, "teamPriorityChart.legendSwatchRadius", 5)
    for idx, priority in enumerate(priorities):
        key = priority_key(priority, idx)
        label = priority_name(priority, key)
        color = priority_color(priority, idx, style)
        x = legend_x + idx * legend_step
        parts.append(f'<rect x="{x}" y="{legend_y - swatch_size + 3}" width="{swatch_size}" height="{swatch_size}" rx="{swatch_radius}" fill="{color}"/>')
        parts.append(svg_text(x + swatch_size + 10, legend_y, label, size=text_size(style, "legend", 20), weight=text_weight(style, "legend", "600"), fill=style_str(style, "colors.text", "#111827"), font_family=font_family))

    tick_step = chart_tick_step(style, "teamPriorityChart", axis_max, style_int(style, "teamPriorityChart.tickMinStep", 5))
    for tick in axis_ticks(axis_max, tick_step):
        x = margin_left + chart_w * tick / axis_max
        parts.append(f'<line x1="{x:.1f}" y1="{chart_top - style_int(style, "teamPriorityChart.gridTopOffset", 24)}" x2="{x:.1f}" y2="{height - style_int(style, "teamPriorityChart.gridBottomOffset", 50)}" stroke="{style_str(style, "colors.grid", "#E5E7EB")}" stroke-width="1"/>')
        parts.append(svg_text(x, height - style_int(style, "teamPriorityChart.axisLabelBottomOffset", 22), tick, size=text_size(style, "axis", 16), weight=text_weight(style, "axis", "400"), fill=style_str(style, "colors.muted", "#6B7280"), anchor="middle", font_family=font_family))

    for i, row in enumerate(rows):
        team = row.get("team", "")
        values = [
            (priority_key(priority, idx), int(row.get(priority_key(priority, idx), 0)), priority_color(priority, idx, style))
            for idx, priority in enumerate(priorities)
        ]
        total = sum(value for _, value, _ in values)
        y = chart_top + i * row_h

        parts.append(svg_wrapped_text(label_x, y + style_int(style, "teamPriorityChart.rowLabelBaselineOffset", 27), team, max_width=margin_left - label_x - style_int(style, "teamPriorityChart.labelRightPadding", 12), size=text_size(style, "label", 22), weight=text_weight(style, "label", "600"), fill=style_str(style, "colors.text", "#111827"), font_family=font_family))
        x = margin_left
        parts.append(f'<rect x="{margin_left}" y="{y}" width="{chart_w}" height="{bar_h}" rx="{bar_radius}" fill="{style_str(style, "colors.track", "#F3F4F6")}"/>')

        for key, value, color in values:
            seg_w = chart_w * value / axis_max if axis_max else 0
            if seg_w <= 0:
                continue
            parts.append(f'<rect x="{x:.1f}" y="{y}" width="{seg_w:.1f}" height="{bar_h}" rx="{segment_radius}" fill="{color}"/>')
            if seg_w >= style_int(style, "teamPriorityChart.segmentValueMinWidth", 24):
                label_size = text_size(style, "segmentValue", 17)
                if seg_w < style_int(style, "teamPriorityChart.segmentValueNormalWidth", 36):
                    label_size = style_int(style, "textStyles.segmentValue.smallSize", 15)
                parts.append(svg_text(x + seg_w / 2, y + style_int(style, "teamPriorityChart.segmentValueBaselineOffset", 23), value, size=label_size, weight=text_weight(style, "segmentValue", "700"), fill=style_str(style, "colors.white", "#FFFFFF"), anchor="middle", font_family=font_family))
            x += seg_w

        parts.append(svg_text(width - style_int(style, "teamPriorityChart.totalXOffset", 40), y + style_int(style, "teamPriorityChart.totalBaselineOffset", 25), f"{total}件", size=text_size(style, "label", 22), weight=text_weight(style, "value", "700"), fill=style_str(style, "colors.heading", "#1E3A8A"), anchor="end", font_family=font_family))

    parts.append(svg_footer())
    out_path.write_text("\n".join(parts), encoding="utf-8")


def donut_path(cx: float, cy: float, outer_r: float, inner_r: float, start_angle: float, end_angle: float) -> str:
    def point(radius: float, angle: float) -> tuple[float, float]:
        return (cx + radius * math.sin(angle), cy - radius * math.cos(angle))

    large_arc = 1 if end_angle - start_angle > math.pi else 0
    x1, y1 = point(outer_r, start_angle)
    x2, y2 = point(outer_r, end_angle)
    x3, y3 = point(inner_r, end_angle)
    x4, y4 = point(inner_r, start_angle)

    return (
        f"M {x1:.2f} {y1:.2f} "
        f"A {outer_r:.2f} {outer_r:.2f} 0 {large_arc} 1 {x2:.2f} {y2:.2f} "
        f"L {x3:.2f} {y3:.2f} "
        f"A {inner_r:.2f} {inner_r:.2f} 0 {large_arc} 0 {x4:.2f} {y4:.2f} "
        f"Z"
    )


def owner_value(owner: Dict[str, Any], key: str) -> int:
    item = owner.get(key, 0)
    if isinstance(item, dict):
        return int(item.get("value", 0))
    return int(item)


def owner_name(owner: Dict[str, Any], key: str, default: str) -> str:
    item = owner.get(key, {})
    if isinstance(item, dict):
        return str(item.get("name", default))
    return str(owner.get("labels", {}).get(key, default))


def generate_owner_donut_chart(owner: Dict[str, Any], title: str, style: Dict[str, Any], out_path: Path) -> None:
    font_family = style_str(style, "fontFamily", "Yu Gothic, Meiryo, Arial, sans-serif")
    width = style_int(style, "ownerDonutChart.width", 680)
    height = style_int(style, "ownerDonutChart.height", 472)
    primary = owner_value(owner, "primary")
    secondary = owner_value(owner, "secondary")
    primary_name = owner_name(owner, "primary", "担当A")
    secondary_name = owner_name(owner, "secondary", "担当B")
    total = max(primary + secondary, 1)

    parts = svg_header(title, width, height, style, "ownerDonutChart")

    cx = style_float(style, "ownerDonutChart.centerX", 340)
    cy = style_float(style, "ownerDonutChart.centerY", 236)
    outer_r = style_float(style, "ownerDonutChart.outerRadius", 118)
    inner_r = style_float(style, "ownerDonutChart.innerRadius", 72)
    gap = math.radians(style_float(style, "ownerDonutChart.gapDegrees", 2))
    primary_angle = 2 * math.pi * primary / total

    start = 0
    end_primary = max(start, primary_angle - gap)
    start_secondary = primary_angle + gap
    end = 2 * math.pi

    primary_color = style_str(style, "colors.owner.primary", "#2563EB")
    secondary_color = style_str(style, "colors.owner.secondary", "#16A34A")

    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{outer_r}" fill="{style_str(style, "colors.track", "#F3F4F6")}"/>')
    if primary > 0:
        parts.append(f'<path d="{donut_path(cx, cy, outer_r, inner_r, start, end_primary)}" fill="{primary_color}"/>')
    if secondary > 0:
        parts.append(f'<path d="{donut_path(cx, cy, outer_r, inner_r, start_secondary, end)}" fill="{secondary_color}"/>')

    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{inner_r - style_float(style, "ownerDonutChart.innerHoleInset", 1)}" fill="{style_str(style, "colors.white", "#FFFFFF")}"/>')
    parts.append(svg_text(cx, cy + style_float(style, "ownerDonutChart.centerTotalYOffset", -4), total, size=text_size(style, "donutTotal", 34), weight=text_weight(style, "donutTotal", "700"), fill=style_str(style, "colors.text", "#111827"), anchor="middle", font_family=font_family))
    parts.append(svg_text(cx, cy + style_float(style, "ownerDonutChart.centerLabelYOffset", 28), "合計", size=text_size(style, "donutCenterLabel", 18), weight=text_weight(style, "donutCenterLabel", "400"), fill=style_str(style, "colors.muted", "#6B7280"), anchor="middle", font_family=font_family))

    primary_pct = round(primary / total * 100)
    secondary_pct = 100 - primary_pct

    swatch_size = style_int(style, "ownerDonutChart.legendSwatchSize", 18)
    swatch_radius = style_int(style, "ownerDonutChart.legendSwatchRadius", 5)
    owner_y = style_int(style, "ownerDonutChart.ownerY", 166)
    left_x = style_int(style, "ownerDonutChart.primaryX", 44)
    right_x = style_int(style, "ownerDonutChart.secondaryX", 520)

    text_gap = style_int(style, "ownerDonutChart.ownerTextGap", 28)
    label_padding = style_int(style, "ownerDonutChart.labelRightPadding", 4)
    left_label_x = left_x + text_gap
    right_label_x = right_x + text_gap
    owner_label_y = owner_y + style_int(style, "ownerDonutChart.ownerLabelBaselineOffset", 16)
    left_label_max_width = max(cx - outer_r - left_label_x - label_padding, 1)
    right_label_max_width = max(width - right_label_x - label_padding, 1)

    parts.append(f'<rect x="{left_x}" y="{owner_y}" width="{swatch_size}" height="{swatch_size}" rx="{swatch_radius}" fill="{secondary_color}"/>')
    parts.append(svg_wrapped_text(left_label_x, owner_label_y, secondary_name, max_width=left_label_max_width, size=text_size(style, "ownerLabel", 22), weight=text_weight(style, "ownerLabel", "700"), fill=style_str(style, "colors.owner.secondaryText", "#166534"), font_family=font_family))
    parts.append(svg_text(left_x + text_gap, owner_y + style_int(style, "ownerDonutChart.ownerValueBaselineOffset", 54), f"{secondary}件", size=text_size(style, "ownerValue", 32), weight=text_weight(style, "ownerValue", "700"), fill=style_str(style, "colors.text", "#111827"), font_family=font_family))
    parts.append(svg_text(left_x + text_gap, owner_y + style_int(style, "ownerDonutChart.ownerPercentBaselineOffset", 84), f"{secondary_pct}%", size=text_size(style, "ownerPercent", 20), weight=text_weight(style, "ownerPercent", "600"), fill=style_str(style, "colors.muted", "#6B7280"), font_family=font_family))

    parts.append(f'<rect x="{right_x}" y="{owner_y}" width="{swatch_size}" height="{swatch_size}" rx="{swatch_radius}" fill="{primary_color}"/>')
    parts.append(svg_wrapped_text(right_label_x, owner_label_y, primary_name, max_width=right_label_max_width, size=text_size(style, "ownerLabel", 22), weight=text_weight(style, "ownerLabel", "700"), fill=style_str(style, "colors.owner.primaryText", "#1E3A8A"), font_family=font_family))
    parts.append(svg_text(right_x + text_gap, owner_y + style_int(style, "ownerDonutChart.ownerValueBaselineOffset", 54), f"{primary}件", size=text_size(style, "ownerValue", 32), weight=text_weight(style, "ownerValue", "700"), fill=style_str(style, "colors.text", "#111827"), font_family=font_family))
    parts.append(svg_text(right_x + text_gap, owner_y + style_int(style, "ownerDonutChart.ownerPercentBaselineOffset", 84), f"{primary_pct}%", size=text_size(style, "ownerPercent", 20), weight=text_weight(style, "ownerPercent", "600"), fill=style_str(style, "colors.muted", "#6B7280"), font_family=font_family))

    parts.append(svg_footer())
    out_path.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="課題・タスク状況ダッシュボード用SVGを生成します。")
    parser.add_argument("--input", required=True, help="入力JSONファイルパス")
    parser.add_argument("--output", required=True, help="出力ディレクトリ")
    parser.add_argument("--style", default=str(DEFAULT_STYLE_PATH), help="スタイル設定JSONCファイルパス")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)
    style_path = Path(args.style)
    output_dir.mkdir(parents=True, exist_ok=True)

    data = json.loads(input_path.read_text(encoding="utf-8"))
    style = load_jsonc(style_path)
    titles = data.get("titles", {})
    priorities = data.get("priorities", [])

    generate_status_bar_chart(
        data.get("status", []),
        chart_title(titles, "status", "ステータス別件数"),
        style,
        output_dir / "status_bar_chart.svg",
    )
    generate_team_priority_stacked_bar(
        data.get("teamPriority", []),
        priorities,
        chart_title(titles, "teamPriority", "グループ別 未完了件数（優先度別）"),
        style,
        output_dir / "team_priority_stacked_bar.svg",
    )
    generate_owner_donut_chart(
        data.get("owner", {}),
        chart_title(titles, "owner", "担当区分別内訳"),
        style,
        output_dir / "owner_donut_chart.svg",
    )

    print(f"SVG files generated in: {output_dir}")


if __name__ == "__main__":
    main()
