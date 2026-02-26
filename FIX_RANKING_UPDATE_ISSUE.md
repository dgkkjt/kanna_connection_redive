# 排名更新问题修复说明

## 问题描述
当取消监控后，即使还有其他监控账号在运行，这些账号也无法更新排名信息。

## 根本原因

### 问题分析
系统采用**全局单一排名获取账号**的设计，避免多个账号重复获取排名而浪费资源：

1. **初始化时**：第一个启动监控的账号被指定为`ranking_fetch_qq_id`（全局排名获取账号）
2. **关键问题**：当这个账号取消监控时，代码直接将`ranking_fetch_qq_id`设为`None`
3. **后果**：其他正在运行的监控账号虽然仍然活跃，但因为`ranking_fetch_qq_id`被设为`None`，它们无法执行排名更新

### 在 model.py 中的检查逻辑
```python
# record_period_ranking() 方法中的检查
if ranking_fetch_qq_id is None or ranking_fetch_qq_id != current_qq_id:
    return  # 无法执行排名获取
```

## 修复方案

### 修改内容

#### 1. **`delete_monitor()` 函数**
当用户取消监控时，如果该用户是全局排名获取账号：
- ✅ **新逻辑**：遍历其他群的监控，寻找还在活跃的监控账号
- ✅ 若找到活跃监控，将排名获取责任重新分配给它
- ✅ 仅当没有其他活跃监控时，才将`ranking_fetch_qq_id`设为`None`

```python
if ranking_fetch_qq_id == qq_id:
    # 检查是否还有其他活跃的监控账号
    new_ranking_fetcher = None
    for gid, cinfo in clanbattle_info.items():
        if gid != group_id and cinfo.loop_check:
            new_ranking_fetcher = cinfo.qq_id
            break
    ranking_fetch_qq_id = new_ranking_fetcher
```

#### 2. **异常处理的三处位置**
在以下异常情况下也应用相同的重新分配逻辑：
- ✅ 监控被手动停止（`loop_num`改变）
- ✅ 账号被顶号
- ✅ 重试次数超限

#### 3. **`add_monitor()` 函数的初始化逻辑增强**
启动新监控时添加验证：
- ✅ 检查当前分配的`ranking_fetch_qq_id`账号是否仍然活跃
- ✅ 如果原分配账号已不活跃，自动重新分配给新启动的账号
- ✅ 这确保了在边界情况下的快速恢复

```python
# 验证当前分配的排名获取账号是否仍然活跃
account_still_active = False
for gid, cinfo in clanbattle_info.items():
    if cinfo.qq_id == ranking_fetch_qq_id and cinfo.loop_check:
        account_still_active = True
        break

# 如果原来分配的账号不活跃了，分配给新启动的账号
if not account_still_active:
    ranking_fetch_qq_id = qq_id
```

## 工作流程示例

### 场景：多群监控的情况
1. **群A账号X启动监控** → `ranking_fetch_qq_id = X`
2. **群B账号Y启动监控** → 账号X仍活跃，保持`ranking_fetch_qq_id = X`
3. **账号X取消监控** → 检测到账号Y仍活跃 → `ranking_fetch_qq_id = Y`
4. **群B继续运行** → 账号Y继续执行排名更新 ✅

### 场景：顺序停止的情况
1. **群A账号X启动** → `ranking_fetch_qq_id = X`
2. **群B账号Y启动** → `ranking_fetch_qq_id = X`
3. **账号X被顶号** → 检测到Y仍活跃 → `ranking_fetch_qq_id = Y`
4. **账号Y被顶号** → 没有其他活跃监控 → `ranking_fetch_qq_id = None`

## 测试建议

### 测试场景
1. **多群同时监控**：启动多个群的监控，然后逐个取消，观察排名是否持续更新
2. **异常情况**：模拟账号被顶号的场景，验证排名转移
3. **快速切换**：快速启动和停止不同的监控，确保`ranking_fetch_qq_id`正确转移

### 验证方法
- 下【查看排名】或【排名详情】命令，检查排名时间戳是否在30分钟间隔内更新
- 查看日志输出，确认排名获取账号的正确转移

## 文件修改生效说明
- **修改文件**：[clanbattle/__init__.py](clanbattle/__init__.py)
- **修改位置**：
  - 第95-111行：初始化阶段的账号验证逻辑
  - 第181-227行：异常处理中的三处重新分配逻辑
  - 第233-254行：`delete_monitor()` 函数的重新分配逻辑

修复后，即使有任何监控被中断，只要还有其他活跃的监控账号，排名更新就能持续进行。
