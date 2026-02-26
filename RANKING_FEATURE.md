# 会战排名定期记录功能

## 功能概述

此功能每30分钟自动从游戏API获取会战排名前60的数据，并将其记录到本地数据库中，供用户查询排名信息。

## 功能详情

### 1. 自动排名记录
- **触发方式**：在出刀监控运行期间，系统每30分钟自动调用一次
- **获取数据**：调用 `/clan_battle/period_ranking` API，分页获取前60名排名（每页10名，共6页）
- **存储位置**：SQLite数据库（`data/clanbattle/{group_id}/clanbattle.db`）
- **保留期限**：30天内的数据

### 2. 新增数据库表
在 `period_ranking` 表中存储：
- `rank` - 排名位置（1-60）
- `clan_id` - 公会ID
- `clan_name` - 公会名称
- `leader_id` - 会长ID
- `leader_name` - 会长名称
- `damage` - 总伤害数
- `timestamp` - 记录时间戳

### 3. 新增命令

#### 查看排名
```
【查看排名】 或 【排名记录】
```
显示：
- 当前排名前10的公会
- 本群所在公会的排名位置

#### 排名详情
```
【排名详情】
```
显示完整的排名列表（前60名），包括：
- 排名位置
- 公会名称
- 会长名称
- 总伤害数

### 4. 文件修改

#### model.py
- 添加 `fetch_period_ranking(page)` 方法：获取指定页码的排名数据
- 添加 `record_period_ranking()` 方法：定期获取并记录排名数据（30分钟间隔）
- 添加 `save_ranking(ranking_data)` 方法：将排名数据保存到数据库
- 初始化 `RankingDao` 和 `last_ranking_fetch` 时间戳

#### sql.py
- 新增 `RankingDao` 类，提供以下方法：
  - `add_ranking(ranking_data)` - 添加排名数据
  - `get_latest_ranking()` - 获取最新的排名记录
  - `get_ranking_by_time(timestamp)` - 获取指定时间的排名
  - `get_all_timestamps()` - 获取所有时间戳
  - `refresh()` - 清除30天前的数据

#### __init__.py
- 在监控循环中添加 `await clan_info.record_period_ranking()` 调用
- 添加 `view_ranking()` 命令处理函数
- 添加 `view_ranking_detail()` 命令处理函数
- 在定时任务中添加 `RankingDao.refresh()` 调用
- 更新帮助文本

## 工作流程

1. **初始化**：用户发送【出刀监控】命令启动监控
2. **定期记录**：在监控运行期间，每30分钟执行一次排名记录
3. **API调用**：调用6次 `/clan_battle/period_ranking` API（page 0-5）
4. **数据汇总**：提取所有返回的排名数据
5. **数据保存**：将排名数据存储到SQLite数据库
6. **查询**：用户可随时发送查询命令查看排名

## 技术细节

### 排名记录频率控制
```python
# 检查是否已经超过30分钟
if current_time - self.last_ranking_fetch < 30 * 60:
    return
```

### API调用参数
```python
{
    'clan_id': self.clan_id,
    'clan_battle_id': self.clan_battle_id,
    'period': 1,
    'month': 0,
    'page': page,  # 0-5
    'is_my_clan': 0,
    'is_first': 1
}
```

### 数据库清理策略
- 每天凌晨4:59执行清理任务
- 删除30天之前的排名记录

## 注意事项

1. 自动排名记录仅在出刀监控运行时进行
2. 若连续30分钟内已有记录，则不会重复获取
3. 每个API调用间隔0.5秒，避免请求过快
4. 排名数据按时间戳分组保存，同一时间的多条记录视为一次完整的排名记录

## 故障排除

### 排名数据为空
- 确保已启动出刀监控【出刀监控】
- 等待30分钟以获取第一次排名记录
- 检查网络连接和API可用性

### 查询命令无响应
- 确认本群已启动出刀监控
- 检查是否已有排名数据（未启动监控30分钟）
- 查看机器人日志以获取更多错误信息
