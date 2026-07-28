# F1 Grand Prix Tracker

> 实时追踪 F1 大奖赛车手积分与排名，多维度预测下一站成绩，追踪车队技术升级。

基于 F1.com 官方数据，每场大奖赛后自动更新车手/车队积分榜和比赛结果，结合**近期状态、赛道历史、赛车性能、练习赛数据**四个维度预测下一场排名，并汇总各车队带来的技术升级及影响分析。输出为样式化 HTML 报告（含 Chart.js 图表）。

## 功能特性

- **实时积分榜** — 从 F1.com 拉取最新车手和车队积分排名
- **比赛结果** — 完整的上一场大奖赛完赛名单（含 DNF/罚时状态）
- **多因素预测模型** — 四维加权评分预测下一场排名
  - 近期状态 (35%) — 最近 5 场成绩，时间衰减加权
  - 赛道历史 (20%) — 该赛道过去 3 年成绩
  - 赛车性能 (25%) — 车队积分排名 + 排位赛速度
  - 练习赛数据 (20%) — FP1/FP2/FP3 最快圈速排名
- **车队升级追踪** — 各车队新部件及技术分析（含预期影响）
- **黑马预测** — 识别预测排名远高于积分排名的车手
- **HTML 可视化报告** — Chart.js 积分柱状图 + 多因素评分对比图

## 项目结构

```
f1-grand-prix-tracker/
├── generate_report.py          # HTML 报告生成器（核心脚本）
├── docs/
│   ├── f1_data_sources.md      # F1.com URL 模式、赛道映射、升级术语表
│   └── prediction_model.md     # 预测算法：权重、评分公式、修正因子
├── examples/
│   ├── sample_data.json        # 示例输入数据（2026 匈牙利站后）
│   └── sample_report.html      # 示例 HTML 报告
├── .gitignore
├── LICENSE
└── README.md
```

## 快速开始

### 环境要求

- Python 3.8+（仅使用标准库，无需安装第三方依赖）

### 生成报告

```bash
# 使用示例数据生成报告
python generate_report.py examples/sample_data.json report.html

# 在浏览器中打开
open report.html        # macOS
start report.html       # Windows
xdg-open report.html    # Linux
```

### 使用自己的数据

按以下 JSON 结构准备数据，然后传给脚本：

```json
{
    "season": 2026,
    "report_date": "2026-07-27",
    "last_race": {
        "name": "匈牙利大奖赛",
        "circuit": "匈格罗宁赛道，布达佩斯",
        "date": "2026-07-26",
        "results": [
            {"position": 1, "driver": "Lando Norris", "team": "McLaren", "time_or_status": "1:39:56.180", "points": 25}
        ]
    },
    "driver_standings": [
        {"position": 1, "driver": "Kimi Antonelli", "team": "Mercedes", "points": 219}
    ],
    "constructor_standings": [
        {"position": 1, "team": "Mercedes", "points": 379}
    ],
    "recent_races": [
        {"name": "匈牙利大奖赛", "date": "2026-07-26", "winner": "Lando Norris", "fastest_lap": "Leclerc 1:22.000 (L58)"}
    ],
    "next_race": {
        "name": "荷兰大奖赛",
        "circuit": "赞德沃特赛道",
        "date": "2026-08-23",
        "country": "荷兰",
        "track_characteristics": {
            "type": "永久赛道",
            "length": "4.259 km",
            "laps": 72
        }
    },
    "prediction": [
        {
            "position": 1,
            "driver": "Kimi Antonelli",
            "team": "Mercedes",
            "total_score": 87.9,
            "scores": {"recent_form": 92, "track_history": 70, "car_performance": 95, "practice": 95},
            "confidence": "high",
            "key_factors": ["赛季7胜领跑积分榜"],
            "risk_factors": ["赞德沃特无历史胜绩"]
        }
    ],
    "dark_horse": {"driver": "Fernando Alonso", "reason": "Honda PU 重大升级"},
    "weather_forecast": "气温20-24°C，有降雨可能",
    "upgrades": [
        {"team": "Aston Martin (Honda PU)", "description": "燃烧室+预燃室+润滑系统升级", "expected_impact": "马力可感知提升"}
    ],
    "notes": "备注信息"
}
```

完整字段说明见 [`examples/sample_data.json`](examples/sample_data.json)。

## 预测模型

预测算法详见 [`docs/prediction_model.md`](docs/prediction_model.md)。核心公式：

```
总分 = 近期状态 × 0.35 + 赛道历史 × 0.20 + 赛车性能 × 0.25 + 练习赛 × 0.20
```

权重会根据条件动态调整（街道赛道、冲刺赛周末、赛季初期、雨战等）。

## 数据来源

| 数据 | 来源 | 获取方式 |
|------|------|----------|
| 赛历 | [F1.com/racing](https://www.formula1.com/en/racing/2026) | WebFetch |
| 比赛结果 | F1.com/results | WebFetch |
| 积分榜 | F1.com / WebSearch | WebFetch / WebSearch |
| 车队升级 | F1.com 新闻 / Motorsport.com | WebSearch |
| 天气预测 | 天气网站 | WebSearch |

完整 URL 模式和搜索策略见 [`docs/f1_data_sources.md`](docs/f1_data_sources.md)。

## 报告效果

生成的 HTML 报告包含：

- 上站比赛完整结果表
- 车手积分榜 + Top 10 柱状图
- 车队积分榜
- 近 5 场比赛回顾（含最快圈速）
- 车队升级动态卡片
- 下一场预测：多因素评分条形图 + 详细分析卡片
- 黑马预测卡片
- 赛道特性网格
- 天气预测

## 支持的车队（2026 网格）

Red Bull · Ferrari · Mercedes · McLaren · Aston Martin · Alpine · Williams · Racing Bulls · Audi · Haas · Cadillac

## 许可证

[MIT License](LICENSE)

## 免责声明

本项目数据来源于 F1.com 等公开渠道，仅供信息参考和技术学习。预测基于历史数据和近期表现，实际结果受众多不可控因素影响（天气、安全车、事故、策略、可靠性等）。不建议用于赌博或投注决策。
