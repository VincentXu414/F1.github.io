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

    /* Quiz */
    .quiz-banner { display: flex; align-items: center; gap: 12px; background: linear-gradient(135deg, #e10600 0%, #b00500 100%); color: #fff; padding: 14px 20px; border-radius: 10px; margin-bottom: 24px; cursor: pointer; transition: opacity 0.2s; }
    .quiz-banner:hover { opacity: 0.92; }
    .quiz-banner .qb-icon { font-size: 22px; }
    .quiz-banner .qb-text { font-size: 16px; font-weight: 600; }
    .quiz-banner .qb-sub { font-size: 13px; opacity: 0.85; flex-grow: 1; }
    .quiz-banner .qb-arrow { font-size: 14px; transition: transform 0.3s; }
    .quiz-banner .qb-arrow.open { transform: rotate(180deg); }
    .quiz-banner .qb-updated { background: #ffd700; color: #1a1a1a; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 700; display: none; animation: fqPulse 1.5s ease-in-out infinite; }
    @keyframes fqPulse {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.6; }} }}
    .quiz-panel { display: none; margin-bottom: 24px; }
    .quiz-tabs { display: flex; gap: 8px; margin-bottom: 16px; }
    .quiz-tab { padding: 8px 20px; border: 1px solid #e0e0e0; border-radius: 8px; background: #fff; font-size: 13px; cursor: pointer; font-weight: 600; color: #666; }
    .quiz-tab.active { background: #e10600; color: #fff; border-color: #e10600; }
    .quiz-card { background: #fff; border-radius: 12px; padding: 24px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
    .quiz-progress { height: 6px; background: #f0f0f0; border-radius: 3px; margin-bottom: 16px; overflow: hidden; }
    .quiz-progress-fill { height: 100%; background: #e10600; border-radius: 3px; transition: width 0.3s; }
    .quiz-q-num { font-size: 12px; color: #999; margin-bottom: 4px; }
    .quiz-q-text { font-size: 15px; font-weight: 600; margin-bottom: 16px; line-height: 1.5; }
    .quiz-opt { display: block; width: 100%; text-align: left; padding: 12px 14px; margin-bottom: 8px; border: 1px solid #e0e0e0; border-radius: 8px; background: #fff; font-size: 14px; cursor: pointer; transition: all 0.15s; }
    .quiz-opt:hover:not(.locked) { border-color: #e10600; background: #fff5f5; }
    .quiz-opt.locked { cursor: default; }
    .quiz-opt.correct { border-color: #198754; background: #d1e7dd; color: #0f5132; }
    .quiz-opt.wrong { border-color: #dc3545; background: #f8d7da; color: #842029; }
    .quiz-opt.dim { opacity: 0.4; }
    .quiz-feedback { font-size: 13px; margin-top: 12px; padding: 10px 14px; border-radius: 8px; display: none; }
    .quiz-feedback.show { display: block; }
    .quiz-feedback.ok { background: #d1e7dd; color: #0f5132; }
    .quiz-feedback.no { background: #f8d7da; color: #842029; }
    .quiz-next-btn { margin-top: 16px; padding: 10px 24px; border: 1px solid #e0e0e0; border-radius: 8px; background: #fff; font-size: 14px; cursor: pointer; display: none; }
    .quiz-next-btn.show { display: inline-block; }
    .quiz-next-btn:hover { border-color: #e10600; background: #fff5f5; }
    .quiz-start-screen { text-align: center; padding: 1.5rem; }
    .quiz-start-screen h3 { font-size: 18px; font-weight: 600; margin-bottom: 8px; }
    .quiz-start-screen p { font-size: 13px; color: #666; margin-bottom: 20px; line-height: 1.6; }
    .quiz-start-btn { padding: 12px 32px; background: #e10600; color: #fff; border: none; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; }
    .quiz-start-btn:hover { background: #c00500; }
    .quiz-result-screen { text-align: center; padding: 1.5rem; }
    .quiz-result-screen .score-big { font-size: 48px; font-weight: 800; color: #e10600; margin: 8px 0; }
    .quiz-result-screen .score-label { font-size: 13px; color: #999; }
    .quiz-result-screen .rating { font-size: 16px; font-weight: 600; margin: 12px 0 20px; }
    .quiz-result-screen .breakdown { text-align: left; margin: 16px 0; }
    .quiz-result-screen .breakdown-item { display: flex; align-items: center; gap: 8px; padding: 8px 0; border-bottom: 1px solid #f0f0f0; font-size: 13px; }
    .quiz-result-screen .breakdown-item:last-child { border: none; }
    .quiz-result-screen .bk-ico { width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; flex-shrink: 0; font-weight: 700; }
    .quiz-result-screen .bk-ok { background: #d1e7dd; color: #0f5132; }
    .quiz-result-screen .bk-no { background: #f8d7da; color: #842029; }
    .quiz-retry-btn { padding: 10px 24px; background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; font-size: 13px; cursor: pointer; }
    .quiz-retry-btn:hover { border-color: #e10600; }

    /* Quiz Leaderboard */
    .quiz-save-row { display: flex; gap: 8px; justify-content: center; margin: 16px 0; flex-wrap: wrap; }
    .quiz-save-row input { padding: 10px 14px; border: 1px solid #e0e0e0; border-radius: 8px; font-size: 14px; width: 160px; }
    .quiz-save-row button { padding: 10px 18px; background: #e10600; color: #fff; border: none; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; }
    .quiz-save-row button:hover { background: #c00500; }
    .quiz-save-msg { font-size: 13px; color: #198754; min-height: 20px; }
    .quiz-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 16px 0; }
    .quiz-stat { background: #f8f9fa; padding: 12px; border-radius: 8px; }
    .quiz-stat .num { font-size: 22px; font-weight: 800; color: #e10600; }
    .quiz-stat .label { font-size: 12px; color: #666; }
    .quiz-lb { margin-top: 20px; text-align: left; }
    .quiz-lb h4 { font-size: 15px; margin-bottom: 10px; display: flex; align-items: center; gap: 6px; }
    .quiz-lb table { font-size: 13px; }
    .quiz-lb th { background: #f8f9fa; }
    .quiz-lb .lb-rank { font-weight: 800; color: #e10600; width: 50px; text-align: center; }
    .quiz-lb .lb-score { font-weight: 700; width: 70px; }
    .quiz-lb .lb-me { background: #fff9e6; }
    .quiz-lb-empty { font-size: 13px; color: #999; text-align: center; padding: 16px; background: #f8f9fa; border-radius: 8px; }
    .lb-tabs { display: flex; gap: 6px; margin-bottom: 10px; }
    .lb-tab { padding: 6px 14px; border: 1px solid #e0e0e0; border-radius: 6px; background: #fff; font-size: 12px; cursor: pointer; }
    .lb-tab.active { background: #1a1a1a; color: #fff; border-color: #1a1a1a; }

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

    quiz_html = """
    <div class="quiz-banner" onclick="fqToggle()">
        <span class="qb-icon">&#127937;</span>
        <span class="qb-text">F1 知识测试</span>
        <span class="qb-sub">两套题库 &#183; 每日更新 &#183; 点击展开挑战自己</span>
        <span class="qb-updated" id="fqUpdated">&#10024; 已更新题库</span>
        <span class="qb-arrow" id="fqArrow">&#9660;</span>
    </div>
    <div class="quiz-panel" id="fqPanel">
        <div class="quiz-tabs">
            <button class="quiz-tab active" id="fqTabA" onclick="fqSwitchSet('A')">入门级</button>
            <button class="quiz-tab" id="fqTabB" onclick="fqSwitchSet('B')">进阶级</button>
        </div>
        <div class="quiz-card">
            <div id="fqStartScreen" class="quiz-start-screen">
                <h3>F1 知识测试</h3>
                <p>10 道题，每题 10 分，满分 100 分<br>选择难度后开始测试</p>
                <button class="quiz-start-btn" onclick="fqStart()">开始测试</button>
            </div>
            <div id="fqMain" style="display:none;">
                <div class="quiz-progress"><div class="quiz-progress-fill" id="fqProgFill" style="width:0%"></div></div>
                <div class="quiz-q-num" id="fqQNum"></div>
                <div class="quiz-q-text" id="fqQText"></div>
                <div id="fqOptions"></div>
                <div class="quiz-feedback" id="fqFeedback"></div>
                <button class="quiz-next-btn" id="fqNextBtn" onclick="fqNext()">下一题</button>
            </div>
            <div id="fqResult" class="quiz-result-screen" style="display:none;">
                <div class="score-label">你的得分</div>
                <div class="score-big" id="fqScore"></div>
                <div class="rating" id="fqRating"></div>
                <div class="breakdown" id="fqBreakdown"></div>
                <div class="quiz-save-row">
                    <input type="text" id="fqName" placeholder="输入昵称" maxlength="12">
                    <button onclick="fqSaveScore()">保存成绩</button>
                </div>
                <div class="quiz-save-msg" id="fqSaveMsg"></div>
                <div class="quiz-stats" id="fqStats"></div>
                <div class="quiz-lb" id="fqLeaderboard"></div>
                <button class="quiz-retry-btn" onclick="fqStart()">再试一次</button>
            </div>
        </div>
    </div>"""

    # ---- Assemble section order based on season status ----
    if season_status == "summer_break":
        # 夏休期: 预测和车队升级置顶，备注紧跟其后作为背景说明
        body_sections = "\n\n".join(filter(None, [
            offseason_html, header_html, quiz_html,
            prediction_html, upgrades_html, notes_html,
            last_race_html, driver_standings_html,
            constructor_standings_html, recent_races_html,
            disclaimer_html,
        ]))
    elif season_status == "off_season":
        # 休赛期: 积分榜优先，备注紧随其后
        body_sections = "\n\n".join(filter(None, [
            offseason_html, header_html, quiz_html,
            driver_standings_html, constructor_standings_html, notes_html,
            last_race_html, recent_races_html,
            disclaimer_html,
        ]))
    else:
        # 正常赛季: 比赛结果优先，备注作为承上启下过渡
        body_sections = "\n\n".join(filter(None, [
            offseason_html, header_html, quiz_html,
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

    // F1 Quiz
    const fqData = {{
        A: {{
            name: '入门级',
            pool: [
                {{ q: 'F1 正赛冠军获得多少积分？', options: ['20分', '25分', '30分', '18分'], answer: 1, explain: 'F1积分系统：冠军25分，亚军18分，季军15分，第4-10名分别为12/10/8/6/4/2/1分。' }},
                {{ q: '2026赛季Mercedes车队的领骑车手是谁？', options: ['George Russell', 'Lewis Hamilton', 'Kimi Antonelli', 'Valtteri Bottas'], answer: 2, explain: 'Kimi Antonelli在2026赛季以219分领跑车手积分榜，Mercedes本赛季11场拿下9胜。' }},
                {{ q: '2026赛季F1有多少支车队、多少辆赛车？', options: ['10队 / 20辆', '11队 / 22辆', '12队 / 24辆', '10队 / 18辆'], answer: 1, explain: '2026赛季有11支车队每队2辆赛车，共22辆赛车。Cadillac作为第11支车队新加入。' }},
                {{ q: 'F1比赛中"Box Box"是什么意思？', options: ['退赛', '进站换胎', '让车', '防守位置'], answer: 1, explain: '"Box"是车队通过无线电通知车手进站(pit stop)换胎或维修的指令。' }},
                {{ q: '2026赛季哪支车队作为全新第11支车队加入F1？', options: ['Audi', 'Cadillac', 'Porsche', 'Lamborghini'], answer: 1, explain: 'Cadillac作为全新第11支车队加入2026赛季F1网格，Audi则接管了原Sauber车队班底。' }},
                {{ q: 'F1赛车轮胎的唯一供应商是谁？', options: ['米其林(Michelin)', '固特异(Goodyear)', '倍耐力(Pirelli)', '普利司通(Bridgestone)'], answer: 2, explain: '倍耐力(Pirelli)自2011年起成为F1唯一轮胎供应商，提供硬(H)、中(M)、软(S)三种干地轮胎。' }},
                {{ q: 'F1中"杆位"(Pole Position)是什么意思？', options: ['最后发车的位置', '排位赛第一名的发车位置', '维修区出口', '领奖台最高位置'], answer: 1, explain: '杆位指排位赛中成绩最快的车手，在正赛中从最前排发车。' }},
                {{ q: '一场F1正赛通常持续多长时间？', options: ['约45分钟', '约1小时', '约1.5-2小时', '约3小时'], answer: 2, explain: 'F1正赛通常持续约1.5-2小时，比赛距离约305公里，设有2小时时间限制。' }},
                {{ q: 'F1比赛中"DNF"代表什么？', options: ['Did Not Finish (未完赛)', 'Did Not Start (未发车)', 'Drive No Faster (减速)', 'Daily News Flash'], answer: 0, explain: 'DNF = Did Not Finish，表示车手因事故、故障或其他原因未能完成比赛。' }},
                {{ q: '2026赛季夏休期后谁以219分领跑车手积分榜？', options: ['Max Verstappen', 'Lando Norris', 'Kimi Antonelli', 'Lewis Hamilton'], answer: 2, explain: 'Kimi Antonelli以219分领跑，Hamilton 169分第二，Russell 160分第三。' }},
                {{ q: 'F1安全车出场时允许超车吗？', options: ['允许，只要在安全车后面', '不允许，必须保持队形', '只在直道允许', '只允许领先车手超车'], answer: 1, explain: '安全车出场后禁止超车，所有赛车必须保持队形跟在安全车后方，直到安全车回维修区。' }},
                {{ q: 'F1排位赛分为几个阶段？', options: ['2个', '3个 (Q1/Q2/Q3)', '4个', '只有1个'], answer: 1, explain: 'F1排位赛分为Q1、Q2、Q3三个阶段，分别淘汰慢车并决定最终发车顺序。' }},
                {{ q: '正赛发车前的暖胎圈英文叫什么？', options: ['Warm-up Lap', 'Formation Lap', 'Installation Lap', 'Flying Lap'], answer: 1, explain: 'Formation Lap（编队圈）是正赛前车手绕场一圈暖胎并到达发车格的圈。' }},
                {{ q: 'F1比赛中蓝旗表示什么？', options: ['前方有危险', '允许超车', '后方快车要套圈，必须让路', '比赛暂停'], answer: 2, explain: '蓝旗表示后方快车即将套圈，被套圈车手必须让路，不让路可能被处罚。' }},
                {{ q: '大奖赛周末通常有几次练习赛？', options: ['1次', '2次', '3次', '4次'], answer: 2, explain: '大奖赛周末通常有3次自由练习赛（FP1、FP2、FP3），排位赛前还有一次。' }},
                {{ q: 'F1中格子旗代表什么？', options: ['比赛开始', '比赛暂停', '比赛结束', '安全车出场'], answer: 2, explain: '黑白格子旗挥动表示比赛正式结束，最先冲过终点线的车手为冠军。' }},
                {{ q: 'F1车手在高速弯道承受的G力约多少？', options: ['约1-2G', '约3-4G', '约5-6G', '约10G'], answer: 2, explain: 'F1车手在高速弯道中可承受约5-6G的横向力，相当于5-6倍体重压在身上。' }},
                {{ q: 'F1比赛中黄旗表示什么？', options: ['赛道畅通', '前方有危险，减速且禁止超车', '比赛取消', '进站信号'], answer: 1, explain: '黄旗表示前方有危险（如事故、碎片），车手必须减速并禁止超车。双黄旗表示更大危险。' }},
                {{ q: 'F1赛车方向盘上大约有多少个按钮和旋钮？', options: ['约5个', '约10个', '约25个以上', '没有按钮'], answer: 2, explain: '现代F1方向盘功能极为复杂，约有25个以上的按钮和旋钮，控制差速器、刹车平衡、能量回收等。' }},
                {{ q: '维修区(Pit Lane)限速通常是多少？', options: ['60km/h', '80km/h', '100km/h', '无限制'], answer: 1, explain: '维修区限速通常为80km/h（部分赛道为60km/h），超速将被罚款或处罚。' }},
                {{ q: 'F1引擎是几缸的？', options: ['4缸直列', '6缸V型 (V6)', '8缸V型 (V8)', '12缸V型 (V12)'], answer: 1, explain: '2014年起F1使用1.6升V6涡轮增压混合动力引擎，取代了之前的2.4升V8自然吸气引擎。' }},
                {{ q: '每支F1车队每赛季有几位正式车手？', options: ['1位', '2位', '3位', '无限制'], answer: 1, explain: '每支F1车队每赛季有2位正式车手，各驾驶一辆赛车参赛。' }},
                {{ q: '遇到大雨时F1正赛通常如何开始？', options: ['正常静止起步', '安全车带领滚动起步', '取消比赛', '延后一周'], answer: 1, explain: '遇到大雨等恶劣天气时，通常会由安全车带领进行滚动起步，等赛道条件改善后再正式开始。' }},
                {{ q: 'F1比赛中红旗表示什么？', options: ['赛道畅通', '减速禁止超车', '比赛暂停，车手回维修区', '比赛结束'], answer: 2, explain: '红旗表示比赛因严重事故或恶劣天气暂停，车手必须减速回到维修区等待重新开始。' }},
                {{ q: 'F1车手头盔最重要的功能是什么？', options: ['通风散热', '保护头部并防火', '减少风阻', '通信'], answer: 1, explain: 'F1头盔必须通过FIA严格认证，核心功能是保护头部并在火灾中提供足够时间的防护。' }}
            ]
        }},
        B: {{
            name: '进阶级',
            pool: [
                {{ q: '2026赛季F1用什么系统取代了DRS？', options: ['KERS能量回收', '主动空气动力学 (Active Aero)', '可变尾翼手动开关', '无任何替代系统'], answer: 1, explain: '2026新规则用主动空气动力学取代DRS。车手可手动切换Z-Mode(低阻直道)和X-Mode(高下压力弯道)，不再限于特定DRS区域。' }},
                {{ q: '2026新规则下动力单元中电力占比目标约为多少？', options: ['约10%', '约30%', '约50%', '约70%'], answer: 2, explain: '2026规则将电力占比提升至约50%，MGU-K功率从120kW大幅增至350kW，接近内燃机功率。' }},
                {{ q: '获得F1超级驾照(Super Licence)需要至少多少积分？', options: ['30分 (3年内)', '40分 (3年内)', '50分 (2年内)', '无需积分'], answer: 1, explain: 'FIA规定车手需在3年内在指定初级赛事中累计至少40个超级驾照积分，且年满18岁方可获得。' }},
                {{ q: 'F1历史上获得世界冠军最多的记录是几次？', options: ['5次', '6次', '7次', '8次'], answer: 2, explain: 'Lewis Hamilton和Michael Schumacher并列最多，各获得7次车手世界冠军。' }},
                {{ q: '正赛最快圈额外1分需要满足什么条件？', options: ['只要跑出最快圈即可', '完赛在前10名', '获得领奖台', '完赛即可'], answer: 1, explain: '2019年规则：跑出最快圈且完赛在前10名才能获得额外1分，否则不予发放。' }},
                {{ q: '2026赛季预算帽(Cost Cap)大约是多少？', options: ['约1亿美元', '约1.35亿美元', '约2亿美元', '无限制'], answer: 1, explain: '2026预算帽约1.35亿美元（按通胀调整），不含车手薪资、市场营销和高层管理薪资。' }},
                {{ q: '赞德沃特赛道两个倾斜弯的角度分别是？', options: ['10度和15度', '18度和19度', '20度和25度', '15度和20度'], answer: 1, explain: 'T3 Hugenholtz弯倾斜18度，T14 Arie Luyendyk弯倾斜19度，是赞德沃特的标志性弯道。' }},
                {{ q: '2026规则中MGU-K功率提升至多少？', options: ['120kW', '200kW', '350kW', '500kW'], answer: 2, explain: '2026规则将MGU-K功率从120kW提升至350kW，使电力输出接近内燃机功率，电力占比达约50%。' }},
                {{ q: 'F1正赛最常用的起步方式是什么？', options: ['滚动起步 (Rolling Start)', '静止起步 (Standing Start)', '安全车后起步', '追逐起步'], answer: 1, explain: 'F1正赛通常使用静止起步，所有赛车在发车格停好后同时起步。滚动起步仅在安全车后重启等特殊情况下使用。' }},
                {{ q: 'Audi在2026赛季接管了哪支车队的班底？', options: ['Haas', 'Williams', 'Sauber', 'Alpine'], answer: 2, explain: 'Audi在2026赛季接管了原Sauber（Kick Sauber）车队的班底和设施，作为厂队参赛。' }},
                {{ q: '地效底盘(Ground Effect)是哪一年回归F1的？', options: ['2019年', '2021年', '2022年', '2026年'], answer: 2, explain: '2022年F1引入全新技术规则，地面效应底盘时隔40年回归，通过底板文丘里管产生下压力。' }},
                {{ q: 'F1刹车盘的工作温度可达多少？', options: ['约200°C', '约500°C', '约700°C', '约1000°C'], answer: 3, explain: 'F1碳纤维刹车盘工作温度可达约1000°C，在高温下才能提供最佳制动力，所以入弯前需要预热。' }},
                {{ q: '"Undercut"策略是什么？', options: ['晚进站用旧胎跑快圈', '提前进站换新胎利用速度差超越前车', '不进站跑完全程', '进站只换前胎'], answer: 1, explain: 'Undercut是提前进站换新胎，利用新胎的速度优势在对手进站时超越对手的经典策略。' }},
                {{ q: 'F1前翼的主要功能是什么？', options: ['仅用于美观', '产生前部下压力并引导气流', '储存燃油', '散热'], answer: 1, explain: '前翼是F1最重要的空气动力学部件之一，产生约25-30%的总下压力，同时引导气流走向影响整车气动效率。' }},
                {{ q: '红旗暂停期间可以换胎吗？', options: ['不可以', '可以（2022年规则更新后允许）', '只能换前胎', '需赛会批准'], answer: 1, explain: '2022年规则更新后，红旗暂停期间允许换胎和维修，但所有车手享有同等权利。' }},
                {{ q: 'F1的三种干地轮胎配方是什么？', options: ['超软、软、中', '硬(H)、中性(M)、软(S)', '雨胎、半雨胎、干胎', '红、黄、白'], answer: 1, explain: '倍耐力提供三种干地配方：硬胎(H/白色)、中性胎(M/黄色)、软胎(S/红色)，颜色越红越软越快但磨损越快。' }},
                {{ q: '正赛第4名获得多少积分？', options: ['10分', '12分', '15分', '18分'], answer: 1, explain: 'F1积分系统：1-10名分别为25/18/15/12/10/8/6/4/2/1分，第4名获得12分。' }},
                {{ q: 'F1车手的最低参赛年龄是多少？', options: ['16岁', '18岁', '21岁', '无限制'], answer: 1, explain: 'FIA规定F1车手最低参赛年龄为18岁，且需持有超级驾照。' }},
                {{ q: '2026规则下内燃机排量是多少？', options: ['1.6升V6', '2.0升V4', '1.5升V6', '3.0升V10'], answer: 0, explain: '2026规则维持1.6升V6涡轮增压内燃机，但取消了MGU-H，将更多电力分配给MGU-K。' }},
                {{ q: 'F1的Halo装置能承受约多少重量？', options: ['约1吨', '约5吨', '约12吨', '约50吨'], answer: 2, explain: 'Halo驾驶舱保护装置能承受约12吨的冲击力，由钛合金制成，2018年起成为F1强制装备。' }},
                {{ q: '"Overcut"策略是什么？', options: ['提前进站换胎', '晚进站用旧胎跑快圈保住位置', '不进站', '退赛'], answer: 1, explain: 'Overcut是晚进站策略，车手用旧胎多跑几圈做出快圈速，出站后仍在对手前面。与Undercut相反。' }},
                {{ q: '地面效应通过什么装置实现？', options: ['前翼', '尾翼', '文丘里管(Venturi隧道)', '扩散器'], answer: 2, explain: '2022规则下地面效应通过底板的文丘里管隧道实现，空气流经收缩-扩张的通道产生低压区，将赛车吸向地面。' }},
                {{ q: 'F1比赛中绿旗表示什么？', options: ['比赛暂停', '前方有危险', '赛道畅通，恢复正常比赛', '比赛结束'], answer: 2, explain: '绿旗表示赛道状况恢复正常，之前黄旗区域的限制解除，可以恢复正常比赛节奏。' }},
                {{ q: '2024赛季F1有多少站大奖赛？', options: ['20站', '22站', '24站', '26站'], answer: 2, explain: '2024赛季F1共设24站大奖赛，是历史上站数最多的赛季，2025赛季同样为24站。' }},
                {{ q: 'F1赛车的HANS系统是什么？', options: ['头盔通风系统', '头颈支撑系统，防止甩鞭伤', '心率监测器', '无线电通信系统'], answer: 1, explain: 'HANS(Head and Neck Support)系统固定在车手肩部连接头盔，在碰撞时限制头部前移，防止致命的头颈甩鞭伤。' }}
            ]
        }}
    }};
    let fqSet = 'A', fqQ = 0, fqScore = 0, fqAns = [], fqFinalScore = 0, fqDailyQs = [];
    const FQ_LB_KEY = 'f1_quiz_scores_v1';
    const FQ_DATE_KEY = 'f1_quiz_last_date';
    function fqDateSeed() {{
        const d = new Date();
        return d.getFullYear() * 10000 + (d.getMonth() + 1) * 100 + d.getDate();
    }}
    function fqSeededShuffle(arr, seed) {{
        const r = [...arr];
        let s = seed;
        for (let i = r.length - 1; i > 0; i--) {{
            s = (s * 9301 + 49297) % 233280;
            const j = Math.floor(s / 233280 * (i + 1));
            const tmp = r[i]; r[i] = r[j]; r[j] = tmp;
        }}
        return r;
    }}
    function fqGetDaily(setKey) {{
        const pool = fqData[setKey].pool;
        const seed = fqDateSeed() + (setKey === 'A' ? 0 : 77777);
        return fqSeededShuffle(pool, seed).slice(0, 10);
    }}
    function fqCheckUpdated() {{
        const today = new Date().toDateString();
        let last = '';
        try {{ last = localStorage.getItem(FQ_DATE_KEY) || ''; }} catch(e) {{}}
        if (last !== today) {{
            const el = document.getElementById('fqUpdated');
            if (el) el.style.display = 'inline-block';
            try {{ localStorage.setItem(FQ_DATE_KEY, today); }} catch(e) {{}}
            setTimeout(function() {{ const e = document.getElementById('fqUpdated'); if (e) e.style.display = 'none'; }}, 10000);
        }}
    }}
    fqCheckUpdated();
    function fqToggle() {{
        const p = document.getElementById('fqPanel');
        const a = document.getElementById('fqArrow');
        if (p.style.display === 'none' || !p.style.display) {{ p.style.display = 'block'; a.classList.add('open'); }}
        else {{ p.style.display = 'none'; a.classList.remove('open'); }}
    }}
    function fqSwitchSet(s) {{
        fqSet = s;
        document.querySelectorAll('.quiz-tab').forEach(t => t.classList.remove('active'));
        document.getElementById('fqTab' + s).classList.add('active');
        fqStart();
    }}
    function fqStart() {{
        fqDailyQs = fqGetDaily(fqSet);
        fqQ = 0; fqScore = 0; fqAns = [];
        document.getElementById('fqStartScreen').style.display = 'none';
        document.getElementById('fqResult').style.display = 'none';
        document.getElementById('fqMain').style.display = 'block';
        fqShow();
    }}
    function fqShow() {{
        const set = fqData[fqSet], q = fqDailyQs[fqQ];
        document.getElementById('fqQNum').textContent = '第 ' + (fqQ + 1) + ' / ' + fqDailyQs.length + ' 题 [' + set.name + ']';
        document.getElementById('fqQText').textContent = q.q;
        document.getElementById('fqProgFill').style.width = (fqQ / fqDailyQs.length * 100) + '%';
        const opts = document.getElementById('fqOptions');
        opts.innerHTML = '';
        q.options.forEach((opt, i) => {{
            const btn = document.createElement('button');
            btn.className = 'quiz-opt'; btn.textContent = opt;
            btn.onclick = function() {{ fqSelect(i, this); }};
            opts.appendChild(btn);
        }});
        document.getElementById('fqFeedback').className = 'quiz-feedback';
        document.getElementById('fqNextBtn').classList.remove('show');
    }}
    function fqSelect(idx, btn) {{
        const set = fqData[fqSet], q = fqDailyQs[fqQ];
        const all = document.querySelectorAll('#fqOptions .quiz-opt');
        all.forEach(b => b.classList.add('locked'));
        if (idx === q.answer) {{
            btn.classList.add('correct'); fqScore++; fqAns.push(true);
            document.getElementById('fqFeedback').textContent = '正确！ ' + q.explain;
            document.getElementById('fqFeedback').className = 'quiz-feedback show ok';
        }} else {{
            btn.classList.add('wrong'); all[q.answer].classList.add('correct');
            all.forEach((b, i) => {{ if (i !== idx && i !== q.answer) b.classList.add('dim'); }});
            fqAns.push(false);
            document.getElementById('fqFeedback').textContent = '不对。 ' + q.explain;
            document.getElementById('fqFeedback').className = 'quiz-feedback show no';
        }}
        document.getElementById('fqNextBtn').classList.add('show');
        document.getElementById('fqNextBtn').textContent = fqQ === fqDailyQs.length - 1 ? '查看结果' : '下一题';
        document.getElementById('fqProgFill').style.width = ((fqQ + 1) / fqDailyQs.length * 100) + '%';
    }}
    function fqNext() {{
        if (fqQ < fqDailyQs.length - 1) {{ fqQ++; fqShow(); }}
        else {{ fqResult(); }}
    }}
    function fqResult() {{
        document.getElementById('fqMain').style.display = 'none';
        document.getElementById('fqResult').style.display = 'block';
        fqFinalScore = fqScore * 10;
        document.getElementById('fqScore').textContent = fqFinalScore + ' / 100';
        document.getElementById('fqSaveMsg').textContent = '';
        let r;
        if (fqFinalScore === 100) r = '完美！你就是F1百科全书';
        else if (fqFinalScore >= 80) r = '资深车迷！知识面很广';
        else if (fqFinalScore >= 60) r = '不错的车迷，还有提升空间';
        else if (fqFinalScore >= 40) r = '继续关注F1，你会越来越懂';
        else r = '刚入门吧？多看几场比赛就熟了';
        document.getElementById('fqRating').textContent = r;
        let bd = '';
        fqDailyQs.forEach((q, i) => {{
            bd += '<div class="breakdown-item"><span class="bk-ico ' + (fqAns[i] ? 'bk-ok' : 'bk-no') + '">' + (fqAns[i] ? '+' : '-') + '</span><span>第' + (i+1) + '题: ' + (fqAns[i] ? '正确' : '错误') + '</span></div>';
        }});
        document.getElementById('fqBreakdown').innerHTML = bd;
        fqRenderLeaderboard();
    }}
    function fqLoadScores() {{
        try {{ return JSON.parse(localStorage.getItem(FQ_LB_KEY) || '[]'); }}
        catch (e) {{ return []; }}
    }}
    function fqSaveScores(list) {{
        try {{ localStorage.setItem(FQ_LB_KEY, JSON.stringify(list)); return true; }}
        catch (e) {{ return false; }}
    }}
    function fqSaveScore() {{
        const nameInput = document.getElementById('fqName');
        const name = (nameInput.value || '匿名车手').trim().slice(0, 12);
        const list = fqLoadScores();
        list.push({{
            name: name,
            score: fqFinalScore,
            quizType: fqSet,
            date: new Date().toLocaleString('zh-CN', {{ month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }}),
            ts: Date.now()
        }});
        if (fqSaveScores(list)) {{
            document.getElementById('fqSaveMsg').textContent = '成绩已保存到本地排名榜';
            nameInput.value = '';
            fqRenderLeaderboard();
        }} else {{
            document.getElementById('fqSaveMsg').textContent = '保存失败，浏览器可能禁用了本地存储';
        }}
    }}
    function fqRenderLeaderboard() {{
        const list = fqLoadScores().filter(s => s.quizType === fqSet).sort((a, b) => b.score - a.score || a.ts - b.ts);
        const statsEl = document.getElementById('fqStats');
        const lbEl = document.getElementById('fqLeaderboard');
        if (list.length === 0) {{
            statsEl.innerHTML = '';
            lbEl.innerHTML = '<div class="quiz-lb-empty">还没有成绩记录，完成测试并保存后就会出现在这里</div>';
            return;
        }}
        const best = Math.max(...list.map(s => s.score));
        const avg = Math.round(list.reduce((a, s) => a + s.score, 0) / list.length);
        statsEl.innerHTML = '<div class="quiz-stat"><div class="num">' + list.length + '</div><div class="label">挑战次数</div></div>' +
            '<div class="quiz-stat"><div class="num">' + best + '</div><div class="label">最佳成绩</div></div>' +
            '<div class="quiz-stat"><div class="num">' + avg + '</div><div class="label">平均分</div></div>';
        let rows = '';
        const newestTs = list.length ? Math.max(...list.map(s => s.ts)) : 0;
        list.slice(0, 10).forEach((s, i) => {{
            const me = s.ts === newestTs ? 'lb-me' : '';
            rows += '<tr class="' + me + '"><td class="lb-rank">#' + (i + 1) + '</td><td>' + s.name + '</td><td class="lb-score">' + s.score + '分</td><td>' + s.date + '</td></tr>';
        }});
        lbEl.innerHTML = '<h4><span>&#127942;</span> 我的 ' + fqData[fqSet].name + ' 排行榜</h4>' +
            '<table><thead><tr><th>排名</th><th>昵称</th><th>分数</th><th>时间</th></tr></thead><tbody>' + rows + '</tbody></table>';
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
