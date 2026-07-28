# F1 数据源参考

本文档记录 F1 大奖赛追踪所需的所有数据来源、URL 模式和数据结构。

## 1. F1.com 官方页面

### 赛历/赛程 (已验证可用)
- URL: `https://www.formula1.com/en/racing/{year}`
- 数据: 每站大奖赛名称、日期、赛道名称、国家、每站前三名
- 提取方式: WebFetch，提示词 "Extract the full race calendar with round number, grand prix name, date, circuit name, and country. Also identify the podium for each completed race."

### 单站比赛页面 (已验证可用)
- URL: `https://www.formula1.com/en/racing/{year}/{race_slug}`
- 数据: 该站完整赛程时间表、赛道信息（长度/圈数/首届年份等）、比赛结果摘要（前5名）、排位赛/练习赛结果链接
- race_slug 示例: `australia`, `china`, `japan`, `miami`, `canada`, `monaco`, `barcelona-catalunya`, `austria`, `great-britain`, `belgium`, `hungary`, `netherlands`, `italy`, `spain`, `azerbaijan`, `singapore`, `united-states`, `mexico`, `brazil`, `las-vegas`, `qatar`, `united-arab-emirates`

### 单场比赛完整结果 (已验证可用)
- URL: `https://www.formula1.com/en/results/{year}/races/{race_id}/{race_slug}/race-result`
- 注意: F1.com 2026年URL格式已变更，需要 race_id（数字ID，如匈牙利站为1291）
- 获取 race_id 方法: 先访问单站比赛页面(racing/{year}/{race_slug})，其中包含结果链接(含race_id)
- 数据: 所有车手完赛名次、车手、车队、圈数、用时/退赛状态、积分
- 提取方式: WebFetch，提示词 "Extract the complete race results table with position, driver, team, laps, time/retired status, and points for ALL classified finishers"

### 排位赛结果 (已验证可用)
- URL: `https://www.formula1.com/en/results/{year}/races/{race_id}/{race_slug}/qualifying`
- 数据: 排位名次、车手、车队、Q1/Q2/Q3 最快圈速
- 提取方式: WebFetch，提示词 "Extract qualifying results with position, driver, team, and Q1/Q2/Q3 lap times"

### 练习赛结果
- URL: `https://www.formula1.com/en/results/{year}/races/{race_id}/{race_slug}/practice/1` (FP1)
- URL: `https://www.formula1.com/en/results/{year}/races/{race_id}/{race_slug}/practice/2` (FP2)
- URL: `https://www.formula1.com/en/results/{year}/races/{race_id}/{race_slug}/practice/3` (FP3)
- 数据: 练习赛名次、车手、车队、最快圈速、圈数
- 提取方式: WebFetch，提示词 "Extract practice session results with position, driver, team, best lap time, and gap"

## 1b. 积分榜获取策略 (F1.com 积分页面 URL 格式已变更)

F1.com 的积分榜页面 URL 格式已变更，旧格式 `/en/results.html/{year}/drivers` 可能返回 404。

### 策略 (按优先级排列)
1. **WebSearch 搜索**: `F1 {year} driver standings championship points after {last_race} Grand Prix`
   - 来源: pitdebrief.com, crash.net, gpblog.com 等通常在赛后数小时内发布完整积分榜
   - 提取: 搜索结果中通常包含完整的车手和车队积分数据
2. **F1.com 单站比赛页面**: 从 `racing/{year}/{race_slug}` 页面可获取前5名结果摘要
3. **自行计算**: 如果无法直接获取积分榜，根据赛季所有比赛结果手动累加积分

## 2. Ergast/Jolpi F1 API (备选，2026赛季可能不可用)

当 F1.com 页面抓取不稳定时，使用 API 作为备选数据源:

- 基础 URL: `https://api.jolpi.ca/f1/`
- 车手积分榜: `https://api.jolpi.ca/f1/{season}/driverStandings.json`
- 车队积分榜: `https://api.jolpi.ca/f1/{season}/constructorStandings.json`
- 最近结果: `https://api.jolpi.ca/f1/{season}/{round}/results.json`
- 赛历: `https://api.jolpi.ca/f1/{season}.json`

注意: 此 API 对2026赛季可能返回404（尚未更新或已停用）。优先使用 F1.com 页面和 WebSearch。

## 3. 赛道特性数据

以下赛道特性影响预测，需通过 WebSearch 获取或从知识库中调用:

| 特性 | 说明 | 影响因素 |
|------|------|----------|
| 赛道类型 | 街道赛/永久赛道 | 街道赛超车难，排位更重要 |
| 平均速度 | 高速/中速/低速 | 高速赛道考验引擎功率和直线速度 |
| 下压力需求 | 高/中/低 | 高下压力赛道考验空气动力学效率 |
| 轮胎磨损 | 高/中/低 | 高磨损赛道策略和轮胎管理关键 |
| 超车难度 | 容易/中等/困难 | 影响排位赛权重 |
| DRS 区域数 | 1-3 | DRS 区多则超车机会多 |
| 赛道长度 | 公里 | 影响圈数和策略 |
| 历年优势车队 | 过去3年该赛道获胜车队 | 历史趋势参考 |

常见赛道 slug 映射:
```
australia → 阿尔伯特公园 (墨尔本)
saudi-arabia → 吉达滨海
japan → 铃鹿
china → 上海国际
miami → 迈阿密国际
monaco → 摩纳哥
canada → 维伦纽夫 (蒙特利尔)
spain → 加泰罗尼亚
austria → 红牛环
great-britain → 银石
hungary → 亨格罗宁
belgium → 斯帕-弗朗科尔尚
netherlands → 赞德福特
italy → 蒙扎 (含 Emilia Romagna 可能单独)
singapore → 滨海湾
united-states → 美洲 (奥斯汀)
mexico → 罗德里格斯兄弟
brazil → 英特拉格斯
las-vegas → 拉斯维加斯
qatar → 卢塞尔
abu-dhabi → 亚斯码头
```

## 4. 车队升级信息来源

### F1.com 新闻
- URL: `https://www.formula1.com/en/latest/all`
- 搜索关键词: "upgrade", "new parts", "technical", "aero", "floor", "wing", "sidepod"
- 按车队搜索: 在 WebSearch 中使用 "F1 {team} upgrade {race_name} {year}"

### 升级常见部位及术语
| 英文 | 中文 | 影响区域 |
|------|------|----------|
| Front Wing | 前翼 | 前部下压力、平衡 |
| Rear Wing | 后翼 | 尾速、直线下压力 |
| Floor | 底板 | 底盘下压力、地面效应 |
| Sidepod | 侧箱 | 气流管理、散热 |
| Diffuser | 扩散器 | 底部气流、下压力 |
| Nose | 鼻锥 | 前部气流 |
| Suspension | 悬挂 | 机械抓地力、轮胎管理 |
| Halo | 防护架 | 安全 (基本不变) |
| Engine Cover | 引擎盖 | 散热、尾部气流 |
| Brake Ducts | 刹车通风道 | 刹车温度管理、轮胎温度 |
| Floor Edge | 底板边缘 | 地面效应密封 |
| Edge Wing | 边缘翼 | 底板气流密封 |

### 升级信息搜索策略
使用 WebSearch 搜索以下模式:
1. `F1 {team} {race_name} upgrades {year}` — 车队在该站带来的升级
2. `F1 {team} new parts {race_name} {year}` — 新部件
3. `F1 {team} technical update {month} {year}` — 技术更新
4. `F1 {race_name} car updates all teams {year}` — 该站所有车队升级汇总

来源优先级:
1. F1.com 官方技术分析文章
2. Motorsport.com / Autosport 技术文章
3. 各车队官方社交媒体/新闻稿
4. F1 技术记者 (Giorgio Piola, Mark Hughes 等) 的分析

## 5. 当前赛季年份确定

执行时动态获取当前年份:
```python
from datetime import datetime
current_year = datetime.now().year
```

如果当前月份在 1-2 月 (赛季尚未开始)，使用上一年作为赛季年份。
F1 赛季通常 3 月开始，12 月结束。

## 6. 数据质量检查

获取数据后进行以下检查:
- [ ] 车手积分榜是否包含所有参赛车手 (通常 20 人)
- [ ] 最近一场比赛结果是否完整 (前 10 名得分)
- [ ] 下一场比赛是否已确定日期
- [ ] 数据是否为当前赛季 (年份正确)
- [ ] 如果赛季刚开始 (1-2 场)，预测应更多依赖排位赛数据
