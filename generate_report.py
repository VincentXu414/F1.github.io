#!/usr/bin/env python3
"""
F1 Grand Prix Tracker - HTML Report Generator

Generates a styled HTML report with Chart.js visualizations from F1 race data.
Data is sourced from F1.com (standings, race results) and WebSearch (upgrades, weather).

Usage:
    python generate_report.py <input_json> [output_html]

Example:
    python generate_report.py examples/sample_data.json report.html

Input JSON structure: see examples/sample_data.json
"""

import json
import sys
import os
from datetime import datetime


# ---------------------------------------------------------------------------
# Team colors (2026 grid)
# ---------------------------------------------------------------------------
TEAM_COLORS = {
    "Red Bull": "#1E2B5E",
    "Ferrari": "#DC0000",
    "Mercedes": "#00D2BE",
    "McLaren": "#FF8000",
    "Aston Martin": "#006F62",
    "Alpine": "#0090FF",
    "Williams": "#005AFF",
    "Racing Bulls": "#6692FF",
    "RB": "#6692FF",
    "Sauber": "#52E252",
    "Audi": "#C4FF4F",
    "Haas": "#B6BABD",
    "Cadillac": "#1A1A1A",
    "Kick Sauber": "#52E252",
}

# Track characteristic keys → Chinese labels
TRACK_KEY_CN = {
    "type": "类型",
    "length": "长度",
    "laps": "圈数",
    "race_distance": "比赛距离",
    "corners": "弯道",
    "downforce": "下压力",
    "tire_wear": "轮胎磨损",
    "overtaking_difficulty": "超车难度",
    "drs_zones": "DRS区域",
    "banked_corners": "倾斜弯道",
    "lap_record": "圈速纪录",
    "format": "赛制",
}

CONFIDENCE_STYLES = {
    "high": ("#198754", "#d1e7dd"),
    "medium": ("#FFC107", "#fff3cd"),
    "low": ("#DC3545", "#f8d7da"),
}


def get_team_color(team_name: str) -> str:
    """Return brand color for a team (2026 grid). Falls back to gray."""
    for key, color in TEAM_COLORS.items():
        if key.lower() in team_name.lower():
            return color
    return "#6c757d"


def confidence_badge(confidence: str) -> str:
    """Render a colored confidence badge."""
    color, bg = CONFIDENCE_STYLES.get(
        confidence.lower(), ("#6c757d", "#e2e3e5")
    )
    return (
        f'<span class="badge" style="background:{bg};color:{color};'
        f'border:1px solid {color};">{confidence.upper()}</span>'
    )


# ---------------------------------------------------------------------------
# Chart data helpers
# ---------------------------------------------------------------------------
def generate_bar_chart_data(prediction):
    """Extract Chart.js datasets for the prediction comparison chart."""
    labels = [f"{p['position']}. {p['driver']}" for p in prediction[:10]]
    recent = [p["scores"]["recent_form"] for p in prediction[:10]]
    track = [p["scores"]["track_history"] for p in prediction[:10]]
    car = [p["scores"]["car_performance"] for p in prediction[:10]]
    practice = [p["scores"]["practice"] for p in prediction[:10]]
    total = [p["total_score"] for p in prediction[:10]]
    return labels, recent, track, car, practice, total


def generate_points_chart_data(driver_standings):
    """Extract Chart.js datasets for the driver points bar chart."""
    labels = [d["driver"].split()[-1] for d in driver_standings[:10]]
    points = [d["points"] for d in driver_standings[:10]]
    colors = [get_team_color(d["team"]) for d in driver_standings[:10]]
    return labels, points, colors


# ---------------------------------------------------------------------------
# HTML section builders
# ---------------------------------------------------------------------------
def build_race_results_table(last_race):
    rows = ""
    for r in last_race.get("results", []):
        team_color = get_team_color(r.get("team", ""))
        pos_class = "podium" if r["position"] <= 3 else ""
        rows += f"""
                <tr class="{pos_class}">
                    <td class="pos-cell">{r['position']}</td>
                    <td class="driver-cell"><span class="team-bar" style="background:{team_color}"></span>{r['driver']}</td>
                    <td>{r.get('team', '')}</td>
                    <td class="mono">{r.get('time_or_status', '')}</td>
                    <td class="mono">{r.get('points', 0)}</td>
                </tr>"""
    return rows


def build_standings_rows(standings, is_constructor=False):
    rows = ""
    for entry in standings:
        team_color = get_team_color(entry.get("team", ""))
        pos_class = "podium" if entry["position"] <= 3 else ""
        team_cell = ""
        if not is_constructor:
            team_cell = f"<td>{entry.get('team', '')}</td>"
        rows += f"""
                <tr class="{pos_class}">
                    <td class="pos-cell">{entry['position']}</td>
                    <td class="driver-cell"><span class="team-bar" style="background:{team_color}"></span>{entry['driver'] if not is_constructor else entry['team']}</td>
                    {team_cell}
                    <td class="mono points-cell">{entry['points']}</td>
                </tr>"""
    return rows


def build_recent_races_rows(recent_races):
    rows = ""
    for r in recent_races:
        rows += f"""
                <tr>
                    <td class="mono">{r.get('date', '')}</td>
                    <td>{r.get('name', '')}</td>
                    <td class="driver-cell">{r.get('winner', '')}</td>
                    <td class="mono">{r.get('fastest_lap', '')}</td>
                </tr>"""
    return rows


def build_prediction_cards(prediction):
    cards = ""
    for p in prediction[:10]:
        team_color = get_team_color(p.get("team", ""))
        key_factors = "".join(f"<li>{f}</li>" for f in p.get("key_factors", []))
        risk_factors = "".join(f"<li>{f}</li>" for f in p.get("risk_factors", []))
        cards += f"""
            <div class="pred-card">
                <div class="pred-header" style="border-left:4px solid {team_color}">
                    <span class="pred-pos">P{p['position']}</span>
                    <span class="pred-driver">{p['driver']}</span>
                    <span class="pred-team">{p.get('team', '')}</span>
                    {confidence_badge(p.get('confidence', 'medium'))}
                    <span class="pred-score">{p['total_score']:.1f}</span>
                </div>
                <div class="pred-scores">
                    <div class="score-bar"><label>近期状态</label><div class="bar-track"><div class="bar-fill" style="width:{p['scores']['recent_form']}%;background:#0d6efd"></div></div><span>{p['scores']['recent_form']:.0f}</span></div>
                    <div class="score-bar"><label>赛道历史</label><div class="bar-track"><div class="bar-fill" style="width:{p['scores']['track_history']}%;background:#6610f2"></div></div><span>{p['scores']['track_history']:.0f}</span></div>
                    <div class="score-bar"><label>赛车性能</label><div class="bar-track"><div class="bar-fill" style="width:{p['scores']['car_performance']}%;background:#fd7e14"></div></div><span>{p['scores']['car_performance']:.0f}</span></div>
                    <div class="score-bar"><label>练习赛</label><div class="bar-track"><div class="bar-fill" style="width:{p['scores']['practice']}%;background:#20c997"></div></div><span>{p['scores']['practice']:.0f}</span></div>
                </div>
                <div class="pred-details">
                    {"<div class='pred-factors'><strong>有利因素</strong><ul>" + key_factors + "</ul></div>" if key_factors else ""}
                    {"<div class='pred-factors risk'><strong>风险因素</strong><ul>" + risk_factors + "</ul></div>" if risk_factors else ""}
                </div>
            </div>"""
    return cards


def build_upgrade_cards(upgrades):
    cards = ""
    for u in upgrades:
        team_color = get_team_color(u.get("team", ""))
        cards += f"""
            <div class="upgrade-card" style="border-left:4px solid {team_color}">
                <div class="upgrade-header">
                    <span class="upgrade-team">{u.get('team', '')}</span>
                </div>
                <div class="upgrade-desc">{u.get('description', '')}</div>
                <div class="upgrade-impact"><strong>预期影响:</strong> {u.get('expected_impact', '')}</div>
            </div>"""
    return cards


def build_dark_horse(dark_horse):
    if not dark_horse.get("driver"):
        return ""
    return f"""
        <div class="dark-horse-card">
            <h3>Dark Horse - 黑马预测</h3>
            <div class="dh-driver">{dark_horse['driver']}</div>
            <div class="dh-reason">{dark_horse.get('reason', '')}</div>
        </div>"""


def build_track_characteristics(next_race):
    track_chars = next_race.get("track_characteristics", {})
    if not track_chars:
        return ""
    items = "".join(
        f"<div class='track-item'><span class='track-label'>{TRACK_KEY_CN.get(k, k)}</span>"
        f"<span class='track-value'>{v}</span></div>"
        for k, v in track_chars.items()
    )
    return f"<div class='track-grid'>{items}</div>"


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
CSS = """
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; background: #f4f5f7; color: #1a1a1a; line-height: 1.6; }
    .container { max-width: 1100px; margin: 0 auto; padding: 24px; }

    .report-header { text-align: center; padding: 32px 0; border-bottom: 3px solid #e10600; margin-bottom: 32px; }
    .report-header h1 { font-size: 28px; color: #1a1a1a; margin-bottom: 8px; }
    .report-header .subtitle { color: #666; font-size: 15px; }
    .report-header .race-badge { display: inline-block; background: #e10600; color: #fff; padding: 4px 16px; border-radius: 4px; font-size: 13px; margin-top: 8px; font-weight: 600; }

    .offseason-banner { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: #fff; text-align: center; padding: 48px 24px; border-radius: 12px; margin-bottom: 24px; box-shadow: 0 4px 16px rgba(0,0,0,0.15); }
    .offseason-banner .icon { font-size: 48px; display: block; margin-bottom: 12px; }
    .offseason-banner h2 { font-size: 36px; color: #ffd700; margin-bottom: 12px; border: none; padding: 0; display: block; }
    .offseason-banner p { color: #ccc; font-size: 16px; max-width: 500px; margin: 0 auto; }
    .offseason-banner .countdown { margin-top: 16px; font-size: 18px; color: #00D2BE; font-weight: 700; }

    .summerbreak-banner { background: linear-gradient(135deg, #e74c3c 0%, #f39c12 100%); color: #fff; text-align: center; padding: 20px 24px; border-radius: 10px; margin-bottom: 24px; box-shadow: 0 2px 12px rgba(231,76,60,0.2); display: flex; align-items: center; justify-content: center; gap: 12px; flex-wrap: wrap; }
    .summerbreak-banner .sb-icon { font-size: 28px; }
    .summerbreak-banner .sb-text { font-size: 16px; font-weight: 600; }
    .summerbreak-banner .sb-countdown { background: rgba(255,255,255,0.2); padding: 4px 14px; border-radius: 20px; font-size: 14px; font-weight: 700; }

    .section { background: #fff; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
    .section h2 { font-size: 20px; color: #1a1a1a; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 2px solid #f0f0f0; display: flex; align-items: center; gap: 8px; }
    .section h2 .icon { font-size: 22px; }

    table { width: 100%; border-collapse: collapse; font-size: 14px; }
    th { text-align: left; padding: 10px 12px; background: #f8f9fa; color: #555; font-weight: 600; border-bottom: 2px solid #e0e0e0; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
    td { padding: 10px 12px; border-bottom: 1px solid #f0f0f0; }
    tr:hover { background: #f8f9fa; }
    tr.podium td { background: #fff9e6; }
    tr.podium:hover td { background: #fff5d6; }
    .pos-cell { font-weight: 700; font-size: 16px; color: #e10600; width: 50px; text-align: center; }
    .driver-cell { font-weight: 600; display: flex; align-items: center; gap: 8px; }
    .team-bar { display: inline-block; width: 4px; height: 20px; border-radius: 2px; flex-shrink: 0; }
    .mono { font-family: 'Consolas', 'Courier New', monospace; }
    .points-cell { font-weight: 700; font-size: 16px; }

    .info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-bottom: 16px; }
    .info-item { background: #f8f9fa; padding: 12px 16px; border-radius: 8px; }
    .info-item .label { font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }
    .info-item .value { font-size: 15px; font-weight: 600; }

    .track-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 8px; margin-top: 12px; }
    .track-item { background: #f0f4f8; padding: 8px 12px; border-radius: 6px; }
    .track-label { display: block; font-size: 11px; color: #666; margin-bottom: 2px; }
    .track-value { display: block; font-size: 14px; font-weight: 600; }

    .pred-card { border: 1px solid #e8e8e8; border-radius: 10px; padding: 16px; margin-bottom: 12px; transition: box-shadow 0.2s; }
    .pred-card:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.1); }
    .pred-header { display: flex; align-items: center; gap: 12px; padding-left: 12px; margin-bottom: 12px; }
    .pred-pos { font-size: 20px; font-weight: 800; color: #e10600; min-width: 40px; }
    .pred-driver { font-size: 17px; font-weight: 700; }
    .pred-team { color: #666; font-size: 13px; flex-grow: 1; }
    .pred-score { font-size: 20px; font-weight: 800; color: #1a1a1a; }
    .badge { font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 600; }

    .pred-scores { display: grid; grid-template-columns: 1fr 1fr; gap: 8px 24px; margin-bottom: 12px; }
    .score-bar { display: flex; align-items: center; gap: 8px; }
    .score-bar label { font-size: 12px; color: #666; width: 70px; flex-shrink: 0; }
    .bar-track { flex-grow: 1; height: 8px; background: #e9ecef; border-radius: 4px; overflow: hidden; }
    .bar-fill { height: 100%; border-radius: 4px; transition: width 0.3s; }
    .score-bar span { font-size: 13px; font-weight: 600; width: 28px; text-align: right; }

    .pred-details { display: flex; gap: 24px; flex-wrap: wrap; padding-top: 8px; border-top: 1px solid #f0f0f0; }
    .pred-factors { flex: 1; min-width: 200px; }
    .pred-factors ul { margin-left: 16px; margin-top: 4px; }
    .pred-factors li { font-size: 13px; color: #555; margin-bottom: 2px; }
    .pred-factors.risk li { color: #c0392b; }

    .upgrade-card { background: #fafbfc; border: 1px solid #e8e8e8; border-radius: 10px; padding: 16px; margin-bottom: 12px; }
    .upgrade-header { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; flex-wrap: wrap; }
    .upgrade-team { font-size: 16px; font-weight: 700; }
    .upgrade-desc { font-size: 14px; color: #555; margin-bottom: 8px; }
    .upgrade-impact { font-size: 13px; color: #333; background: #fff3cd; padding: 8px 12px; border-radius: 6px; }

    .dark-horse-card { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: #fff; border-radius: 12px; padding: 24px; margin-bottom: 24px; text-align: center; }
    .dark-horse-card h3 { color: #ffd700; margin-bottom: 12px; font-size: 18px; }
    .dh-driver { font-size: 24px; font-weight: 800; color: #fff; margin-bottom: 8px; }
    .dh-reason { font-size: 14px; color: #ccc; }

    .chart-container { position: relative; height: 400px; margin-top: 16px; }
    .chart-container-sm { position: relative; height: 300px; margin-top: 16px; }

    .disclaimer { font-size: 12px; color: #999; text-align: center; padding: 16px; border-top: 1px solid #eee; margin-top: 24px; }

    @media (max-width: 768px) {
        .pred-scores { grid-template-columns: 1fr; }
        .pred-details { flex-direction: column; }
        .info-grid { grid-template-columns: 1fr; }
    }
"""


# ---------------------------------------------------------------------------
# Main HTML template
# ---------------------------------------------------------------------------
def generate_html(data: dict) -> str:
    season = data.get("season", datetime.now().year)
    report_date = data.get("report_date", datetime.now().strftime("%Y-%m-%d"))
    last_race = data.get("last_race", {})
    driver_standings = data.get("driver_standings", [])
    constructor_standings = data.get("constructor_standings", [])
    recent_races = data.get("recent_races", [])
    next_race = data.get("next_race", {})
    prediction = data.get("prediction", [])
    dark_horse = data.get("dark_horse", {})
    weather = data.get("weather_forecast", "N/A")
    upgrades = data.get("upgrades", [])
    notes = data.get("notes", "")
    season_status = data.get("season_status", "in_season")
    offseason_msg = data.get("offseason_message", "")

    # Build sections
    last_race_rows = build_race_results_table(last_race)
    driver_rows = build_standings_rows(driver_standings)
    constructor_rows = build_standings_rows(constructor_standings, is_constructor=True)
    recent_rows = build_recent_races_rows(recent_races)
    pred_cards = build_prediction_cards(prediction)
    upgrade_cards = build_upgrade_cards(upgrades)
    dark_horse_html = build_dark_horse(dark_horse)
    track_html = build_track_characteristics(next_race)

    # Off-season / summer break banner
    offseason_html = ""
    if season_status == "off_season":
        offseason_html = f"""
    <div class="offseason-banner">
        <span class="icon">🏁</span>
        <h2>休赛期</h2>
        <p>{offseason_msg or "当前处于F1休赛期，赛季期间将自动恢复实时更新。"}</p>
    </div>"""
    elif season_status == "summer_break":
        next_race_name = next_race.get("name", "下一场大奖赛")
        next_race_date = next_race.get("date", "")
        offseason_html = f"""
    <div class="summerbreak-banner">
        <span class="sb-icon">🏖️</span>
        <span class="sb-text">夏休期中 — 赛季未结束</span>
        <span class="sb-countdown">{offseason_msg or f"下场比赛: {next_race_name} ({next_race_date})"}</span>
    </div>"""

    pred_labels, pred_recent, pred_track, pred_car, pred_practice, pred_total = \
        generate_bar_chart_data(prediction)
    pts_labels, pts_points, pts_colors = generate_points_chart_data(driver_standings)

    # ---- Build individual section HTML blocks ----
    header_html = f"""
    <div class="report-header">
        <h1>F1 {season} 赛季追踪报告</h1>
        <div class="subtitle">报告生成日期: {report_date}</div>
        {f'<div class="race-badge">最近完赛: {last_race.get("name", "N/A")}</div>' if last_race.get("name") else ""}
    </div>"""

    last_race_html = ""
    if last_race_rows:
        last_race_html = f"""
    <div class="section">
        <h2><span class="icon">🏁</span> {last_race.get("name", "最近一场")} - 比赛结果</h2>
        <div class="info-grid">
            <div class="info-item"><div class="label">赛道</div><div class="value">{last_race.get("circuit", "N/A")}</div></div>
            <div class="info-item"><div class="label">日期</div><div class="value">{last_race.get("date", "N/A")}</div></div>
        </div>
        <table>
            <thead><tr><th>名次</th><th>车手</th><th>车队</th><th>用时/状态</th><th>积分</th></tr></thead>
            <tbody>{last_race_rows}</tbody>
        </table>
    </div>"""

    driver_standings_html = f"""
    <div class="section">
        <h2><span class="icon">🏆</span> 车手积分榜</h2>
        <table>
            <thead><tr><th>名次</th><th>车手</th><th>车队</th><th>积分</th></tr></thead>
            <tbody>{driver_rows}</tbody>
        </table>
        <div class="chart-container-sm">
            <canvas id="driverPointsChart"></canvas>
        </div>
    </div>"""

    constructor_standings_html = f"""
    <div class="section">
        <h2><span class="icon">🏭</span> 车队积分榜</h2>
        <table>
            <thead><tr><th>名次</th><th>车队</th><th>积分</th></tr></thead>
            <tbody>{constructor_rows}</tbody>
        </table>
    </div>"""

    recent_races_html = ""
    if recent_rows:
        recent_races_html = f"""
    <div class="section">
        <h2><span class="icon">📊</span> 近期比赛回顾</h2>
        <table>
            <thead><tr><th>日期</th><th>大奖赛</th><th>冠军</th><th>最快圈速</th></tr></thead>
            <tbody>{recent_rows}</tbody>
        </table>
    </div>"""

    upgrades_html = ""
    if upgrade_cards:
        upgrades_html = f"""
    <div class="section">
        <h2><span class="icon">🔧</span> 车队升级动态</h2>
        {upgrade_cards}
    </div>"""

    prediction_html = ""
    if next_race.get("name"):
        prediction_html = f"""
    <div class="section">
        <h2><span class="icon">🔮</span> 下一场预测: {next_race.get("name", "N/A")}</h2>
        <div class="info-grid">
            <div class="info-item"><div class="label">赛道</div><div class="value">{next_race.get("circuit", "N/A")}</div></div>
            <div class="info-item"><div class="label">日期</div><div class="value">{next_race.get("date", "N/A")}</div></div>
            <div class="info-item"><div class="label">国家</div><div class="value">{next_race.get("country", "N/A")}</div></div>
            <div class="info-item"><div class="label">天气预测</div><div class="value">{weather}</div></div>
        </div>
        {track_html}
        <div class="chart-container">
            <canvas id="predictionChart"></canvas>
        </div>
        {pred_cards}
        {dark_horse_html}
    </div>"""

    notes_html = ""
    if notes:
        notes_html = f"""
    <div class="section">
        <h2><span class="icon">📝</span> 备注</h2>
        <p style="font-size:14px;color:#555;">{notes}</p>
    </div>"""

    disclaimer_html = f"""
    <div class="disclaimer">
        数据来源: F1.com 官方数据 | 报告生成时间: {report_date}<br>
        预测基于历史数据和近期表现，实际结果受众多不可控因素影响 (天气、安全车、事故、策略、可靠性等)<br>
        本报告仅供信息参考，不建议用于赌博或投注决策。
    </div>"""

    # ---- Assemble section order based on season status ----
    if season_status == "summer_break":
        # 夏休期: 预测和车队升级置顶，备注紧跟其后作为背景说明
        body_sections = "\n\n".join(filter(None, [
            offseason_html, header_html,
            prediction_html, upgrades_html, notes_html,
            last_race_html, driver_standings_html,
            constructor_standings_html, recent_races_html,
            disclaimer_html,
        ]))
    elif season_status == "off_season":
        # 休赛期: 积分榜优先，备注紧随其后
        body_sections = "\n\n".join(filter(None, [
            offseason_html, header_html,
            driver_standings_html, constructor_standings_html, notes_html,
            last_race_html, recent_races_html,
            disclaimer_html,
        ]))
    else:
        # 正常赛季: 比赛结果优先，备注作为承上启下过渡
        body_sections = "\n\n".join(filter(None, [
            offseason_html, header_html,
            last_race_html, driver_standings_html,
            constructor_standings_html, recent_races_html, notes_html,
            upgrades_html, prediction_html,
            disclaimer_html,
        ]))

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>F1 {season} 赛季追踪报告 - {report_date}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
{CSS}
</style>
</head>
<body>
<div class="container">

    {body_sections}

</div>

<script>
    // Driver Points Chart
    const ctxPts = document.getElementById('driverPointsChart');
    if (ctxPts) {{
        new Chart(ctxPts, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(pts_labels)},
                datasets: [{{
                    label: '积分',
                    data: {json.dumps(pts_points)},
                    backgroundColor: {json.dumps(pts_colors)},
                    borderRadius: 4,
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{ x: {{ beginAtZero: true, grid: {{ color: '#f0f0f0' }} }} }}
            }}
        }});
    }}

    // Prediction Scores Chart
    const ctxPred = document.getElementById('predictionChart');
    if (ctxPred) {{
        new Chart(ctxPred, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(pred_labels)},
                datasets: [
                    {{ label: '近期状态', data: {json.dumps(pred_recent)}, backgroundColor: '#0d6efd', borderRadius: 3 }},
                    {{ label: '赛道历史', data: {json.dumps(pred_track)}, backgroundColor: '#6610f2', borderRadius: 3 }},
                    {{ label: '赛车性能', data: {json.dumps(pred_car)}, backgroundColor: '#fd7e14', borderRadius: 3 }},
                    {{ label: '练习赛', data: {json.dumps(pred_practice)}, backgroundColor: '#20c997', borderRadius: 3 }},
                    {{ label: '综合评分', data: {json.dumps(pred_total)}, backgroundColor: '#e10600', borderRadius: 3 }},
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ position: 'bottom', labels: {{ boxWidth: 12, font: {{ size: 11 }} }} }},
                }},
                scales: {{
                    y: {{ beginAtZero: true, max: 100, grid: {{ color: '#f0f0f0' }} }},
                    x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }} }} }}
                }}
            }}
        }});
    }}
</script>
</body>
</html>"""
    return html


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("F1 Grand Prix Tracker - HTML Report Generator")
        print()
        print("Usage:")
        print("  python generate_report.py <input_json> [output_html]")
        print()
        print("Example:")
        print("  python generate_report.py examples/sample_data.json report.html")
        print()
        print("Input JSON structure: see examples/sample_data.json")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = (
        sys.argv[2]
        if len(sys.argv) > 2
        else os.path.join(os.getcwd(), "f1_report.html")
    )

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {input_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {input_path}: {e}")
        sys.exit(1)

    html = generate_html(data)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Report generated: {output_path}")


if __name__ == "__main__":
    main()
