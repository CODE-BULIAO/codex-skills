# 飞书多维表格结构文档

## 表格基本信息

**表格名称**：各地盤群組配置情況

**Wiki Token**：`KvUmwCEIDin2p8kVhVIc8oyCnZg`

**Bitable App Token**：`Vt0cbMdcRa6L9ZsJirJcs2tKnLg`

---

## 数据表结构

### 1. 数据表 (tbl77ycCEeb0i1y7)

主表，包含所有项目配置信息，共 19 个字段。

#### 字段定义

| 字段名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| 地盤 | Text (主键) | 工地名称 | BMM柴灣、启德医院、安达臣-吊运高危工序警报 |
| 場景 | SingleSelect | 业务类型 | 出料臺、吊船、外牆棚架、Lift Shaft、熱工序、EWPP 升降台作業、Hanger、Drill Hole、Pipe Duct、EWP帶電工程、CSP密閉空間工作、巡火 |
| 紙本/E-permit | SingleSelect | 许可类型 | 紙、都有、E-permit、未知、巡火 |
| PRD | Text (链接) | 需求文档（需权限） | `[{"link":"https://cohlzhtweb.feishu.cn/wiki/xxx","text":"文档标题","token":"xxx","type":"mention"}]` |
| 原始需求副本 | Text (链接) | 需求文档副本（无需权限） | 格式同 PRD，内容相同 |
| 測試群組名 | Text | WhatsApp 测试群名称 | BMM 外牆棚架測試群 |
| 測試群group id | Text | 测试群 ID | `120363410065134145@g.us` |
| 正式群組名 | Text | 生产群名称 | 柴灣外牆棚架正式群 |
| 正式群group id | Text | 生产群 ID | `120363410065134146@g.us` |
| 优先级 | Text | 优先级 | P1、P2、P3、定製化 |
| 是否已开发 | SingleSelect | 开发状态 | 是、否 |
| 是否已交付 | SingleSelect | 交付状态 | 是、否 |
| 自测负责人 | Text | 负责人姓名 | zhangziyu |
| 自测报告 | Text (链接) | 已有报告链接 | `[{"link":"https://...","text":"报告标题","token":"xxx","type":"mention"}]` |
| 对应多维表格 | Text (链接) | 关联的 bitable | `[{"link":"https://...","text":"表名","token":"xxx","type":"mention","mentionType":"Bitable"}]` |
| llm模型 | Text | LLM 模型名称 | 无、gpt-4、claude-3 |
| llm base url | Text | LLM API 地址 | 无、https://api.openai.com/v1 |
| llm key | Text | LLM API 密钥 | 无、sk-xxx... |
| 備註 | Text | 备注信息 | 预估8人天左右，7/31 |

#### 字段值格式说明

**链接类型字段**（PRD、原始需求副本、自测报告、对应多维表格）：
```json
[
  {
    "link": "https://cohlzhtweb.feishu.cn/wiki/WaIpwDEM9iDe7GkMsyRcC6TInLQ",
    "mentionType": "Wiki",
    "realMentionType": "Docx",
    "text": "BMM柴灣 安全巡檢群紙本Permit",
    "token": "WaIpwDEM9iDe7GkMsyRcC6TInLQ",
    "type": "mention"
  }
]
```

提取时取数组第一个元素的 `token` 字段。

**SingleSelect 字段**（場景、紙本/E-permit、是否已开发、是否已交付）：
```json
{
  "場景": "外牆棚架",
  "紙本/E-permit": "都有",
  "是否已开发": "是",
  "是否已交付": "否"
}
```

**WhatsApp 群 ID 格式**：
- 测试群：`120363410065134145@g.us`
- 生产群：`120363410065134146@g.us`

#### 场景选项完整列表

| 值 | 说明 |
|----|------|
| 出料臺 | 出料台许可 |
| 吊船 | 吊船许可 |
| 外牆棚架 | 外墙棚架许可 |
| Lift Shaft | 升降机井许可 |
| 熱工序 | 热工序许可 |
| EWPP 升降台作業 | 升降台作业许可 |
| Hanger | Hanger 许可 |
| Drill Hole | 钻孔许可 |
| Pipe Duct | 管道许可 |
| EWP帶電工程 | 带电工程许可 |
| CSP密閉空間工作 | 密闭空间工作许可 |
| 巡火 | 巡火/夜巡许可 |

#### 纸本/E-permit 选项完整列表

| 值 | 说明 |
|----|------|
| 紙 | 仅纸本许可 |
| E-permit | 仅电子许可 |
| 都有 | 纸本和电子许可都有 |
| 未知 | 未知类型 |
| 巡火 | 巡火特殊类型 |

---

### 2. bug記錄 (tblM2aRPrkvnjnyr)

Bug 记录表，结构与数据表类似，但场景选项不含"巡火"，增加 bug 相关字段。

#### 字段定义

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 地盤 | Text (主键) | 工地名称 |
| 場景 | SingleSelect | 业务类型（不含巡火） |
| 紙本/E-permit | SingleSelect | 许可类型 |
| PRD | Text (链接) | 需求文档 |
| 原始需求副本 | Text (链接) | 需求文档副本 |
| 測試群組名 | Text | 测试群名称 |
| 測試群group id | Text | 测试群 ID |
| 正式群組名 | Text | 生产群名称 |
| 正式群group id | Text | 生产群 ID |
| 优先级 | Text | 优先级 |
| 是否已开发 | SingleSelect | 开发状态 |
| 是否已交付 | SingleSelect | 交付状态 |
| 自测负责人 | Text | 负责人姓名 |
| 自测报告 | Text (链接) | 报告链接 |
| 对应多维表格 | Text (链接) | 关联的 bitable |
| bug記錄 | Text | Bug 记录详情 |
| bug修復情況 | Text | Bug 修复状态 |

---

### 3. 自测报告模板 (tblqzlnEuGDoDf3U)

报告模板表，用于根据业务类型选择对应的报告模板。

#### 字段定义

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 文本 | Text (主键) | 模板文档链接 |
| 说明 | Text | 模板适用类型 |

#### 现有模板

| 说明 | 适用场景 |
|------|---------|
| 纸permit类业务 | 紙、都有 |
| e-permit类业务 | E-permit |
| 非标准业务 | 巡火、未知、其他 |

---

## 查询示例

### 查询特定项目

```bash
curl -X POST http://localhost:3456/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "bitable_v1_appTableRecord_search",
      "arguments": {
        "path": {
          "app_token": "Vt0cbMdcRa6L9ZsJirJcs2tKnLg",
          "table_id": "tbl77ycCEeb0i1y7"
        },
        "data": {
          "page_size": 50,
          "filter": {
            "conjunction": "and",
            "conditions": [
              {"field_name": "地盤", "operator": "is", "value": ["BMM柴灣"]},
              {"field_name": "場景", "operator": "is", "value": ["外牆棚架"]}
            ]
          }
        },
        "useUAT": true
      }
    }
  }'
```

### 查询所有已开发项目

```bash
curl -X POST http://localhost:3456/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "bitable_v1_appTableRecord_search",
      "arguments": {
        "path": {
          "app_token": "Vt0cbMdcRa6L9ZsJirJcs2tKnLg",
          "table_id": "tbl77ycCEeb0i1y7"
        },
        "data": {
          "page_size": 50,
          "filter": {
            "conjunction": "and",
            "conditions": [
              {"field_name": "是否已开发", "operator": "is", "value": ["是"]}
            ]
          }
        },
        "useUAT": true
      }
    }
  }'
```

---

## 数据提取规则

### PRD 和原始需求副本

- **PRD**：原始需求文档，可能需要权限
- **原始需求副本**：PRD 的副本，内容相同但不需要权限
- **使用规则**：优先使用 PRD，如果返回 403 或权限错误，自动切换到原始需求副本

### WhatsApp 群 ID

- 格式：`120363410065134145@g.us`
- 测试群：用于自测，可以发送测试消息
- 生产群：正式群，**禁止发送测试消息**

### 文档 Token 提取

链接字段返回的是数组，提取第一个元素的 token：

```python
def extract_token(field_value):
    if isinstance(field_value, list) and len(field_value) > 0:
        return field_value[0].get("token")
    return None
```

---

## 注意事项

1. **权限检查**：PRD 可能需要权限，失败时自动使用原始需求副本
2. **场景匹配**：场景是单选值，必须精确匹配
3. **群 ID 格式**：确保提取的是完整的 `@g.us` 后缀 ID
4. **文档类型**：根据 `mentionType` 判断文档类型（Wiki、Docx、Bitable）
