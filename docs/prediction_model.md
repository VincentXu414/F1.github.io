# 预测模型参考

本文档定义下一场大奖赛排名预测的方法论和权重体系。

## 1. 预测因素与权重

| 因素 | 权重 | 数据来源 | 说明 |
|------|------|----------|------|
| 近期状态 | 35% | 最近 5 场比赛结果 | 车手当前竞技状态，近期趋势最重要 |
| 赛道历史 | 20% | 该赛道过去 3 年结果 | 某些车手在特定赛道有历史优势 |
| 赛车性能 | 25% | 车队积分、排位赛速度 | 赛车基础竞争力 |
| 练习赛数据 | 20% | FP1/FP2/FP3 结果 | 正赛周末实际表现 |

### 权重调整规则

权重非固定，以下情况需动态调整:

| 条件 | 调整 |
|------|------|
| 赛季前 3 场 | 近期状态权重降至 25%，赛车性能升至 30% (样本量小) |
| 练习赛遇雨或中断 | 练习赛权重降至 10%，差额加到排位赛(如有)/赛车性能 |
| 街道赛道 (摩纳哥/新加坡/吉达) | 赛道历史升至 30%，超车难，排位极重要 |
| 车手换队或新秀 | 赛道历史权重降至 10% (历史数据参考价值低) |
| 冲刺赛周末 | 练习赛只有 1 场 FP1，权重降至 10%，排位赛升至更高 |

## 2. 评分算法

### 2.1 近期状态评分 (满分 100)

对每位车手的最近 5 场比赛:
```
score = Σ (max(0, 26 - finishing_position) * recency_weight) / Σ(recency_weight)
```

其中 recency_weight (时间衰减权重):
- 最近 1 场: 5
- 最近 2 场: 4
- 最近 3 场: 3
- 最近 4 场: 2
- 最近 5 场: 1

退赛 (DNF) 计为 20 名。
未参赛不计入。

### 2.2 赛道历史评分 (满分 100)

对每位车手在该赛道过去 3 年的完赛结果:
```
score = Σ (max(0, 26 - finishing_position) * year_weight) / Σ(year_weight)
```

year_weight:
- 去年: 3
- 前年: 2
- 大前年: 1

DNF 计为 20 名。
未参加该赛道比赛的车手: 使用车队队友的平均成绩作为代理值，打 80% 折扣。

### 2.3 赛车性能评分 (满分 100)

基于车队积分榜排名和排位赛平均名次:
```
constructor_score = (21 - constructor_rank) * 4 + (constructor_points / leader_points) * 16
qualifying_score = (21 - avg_qualifying_position_last_3_races) * 5
car_score = constructor_score * 0.5 + qualifying_score * 0.5
```

如有排位赛数据可用 (下一站已完成排位):
```
car_score = car_score * 0.6 + (21 - next_race_qualifying_pos) * 4 * 0.4
```

### 2.4 练习赛评分 (满分 100)

基于 FP1/FP2/FP3 的最快圈速排名:
```
fp_score = avg(FP1_position_score, FP2_position_score, FP3_position_score)
```
其中 position_score = (21 - position) * 5

如果只有 FP1 和 FP2:
```
fp_score = avg(FP1_position_score, FP2_position_score)
```

如果练习赛未进行 (赛前预测):
```
fp_score = car_score  # 回退到赛车性能评分
权重自动转移 (见权重调整规则)
```

### 2.5 综合评分

```
total_score = recent_form * 0.35 + track_history * 0.20 + car_performance * 0.25 + practice * 0.20
```

根据权重调整规则动态修改系数后:
```
total_score = recent_form * w1 + track_history * w2 + car_performance * w3 + practice * w4
```
其中 w1 + w2 + w3 + w4 = 1.0

## 3. 附加修正因子

在基础评分之上，应用以下修正:

### 3.1 发车位修正
- Pole position: +5
- 前 3 名发车: +3
- 后 10 名发车: -5
- 末位发车: -8
- 维修区发车: -10

### 3.2 引擎/动力单元惩罚
- 超过配额: -3 per penalty (主要影响发车位)

### 3.3 天气修正
- 雨战: 随机性增加，前 5 名车手评分方差扩大 1.5x
- 如果有"雨战大师"车手 (如历史雨战胜率高): +5

### 3.4 车队指令/策略
- 检查是否有已知车队指令 (如二号车手让车): 一号车手 +3, 二号车手 -3
- 该信息通过 WebSearch 获取赛前新闻

## 4. 预测输出格式

预测结果应包含:

```json
{
  "race_name": "大奖赛名称",
  "circuit": "赛道名称",
  "date": "比赛日期",
  "prediction": [
    {
      "position": 1,
      "driver": "车手姓名",
      "team": "车队",
      "total_score": 92.5,
      "scores": {
        "recent_form": 88,
        "track_history": 95,
        "car_performance": 90,
        "practice": 97
      },
      "confidence": "high|medium|low",
      "key_factors": ["近3场全领奖台", "该赛道去年冠军", "排位赛P2"],
      "risk_factors": ["轮胎管理问题", "雨战不确定性"]
    }
  ],
  "dark_horse": {
    "driver": "黑马车手",
    "reason": "预测排名远高于积分排名的原因"
  },
  "weather_forecast": "天气预测",
  "notes": "其他重要备注"
}
```

## 5. 置信度判定

| 等级 | 条件 |
|------|------|
| High | Top 3 车手评分差距 < 3 分，且赛季已过 5 场以上 |
| Medium | 正常情况，评分有合理差距 |
| Low | 赛季前 3 场，或雨战，或多名车手评分差距 < 2 分 |

## 6. 预测局限性声明

预测报告中必须包含:
- 数据截止时间
- 数据来源
- 声明: "预测基于历史数据和近期表现，实际结果受众多不可控因素影响 (天气、安全车、事故、策略、可靠性等)"
- 不建议用于赌博或投注决策
