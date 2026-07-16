---
name: csmart-lark-docs
description: "从飞书多维表格读取 C-Smart 项目配置，支持所有自测技能（巡火、E-permit 等）获取测试所需的项目信息。支持将自测报告自动回填到主表。"
---

# C-Smart 飞书文档读取

从飞书多维表格中读取项目配置，为自测技能提供测试所需信息，并将自测报告自动回填到主表。

## 飞书多维表格信息

**表格名称**：各地盤群組配置情況

**Wiki Token**：`KvUmwCEIDin2p8kVhVIc8oyCnZg`

**Bitable App Token**：`Vt0cbMdcRa6L9ZsJirJcs2tKnLg`

**3 个数据表**：
- `tbl77ycCEeb0i1y7` - 数据表（主表，19 字段）
- `tblM2aRPrkvnjnyr` - bug記錄（17 字段）
- `tblqzlnEuGDoDf3U` - 自测报告模板（2 字段）

## 完整工作流程

```
用户指定地盘+场景
    ↓
1. 查询主表 → 获取 record_id、测试群 ID、PRD 链接
    ↓
2. 读取 PRD 文档（无权限时用原始需求副本）→ 提取业务规则
    ↓
3. 输出项目配置 → 供下游 skill 执行测试
    ↓
4. 测试完成 → 创建飞书多维表格保存报告
    ↓
5. 将报告链接自动回填到主表"自测报告"字段
```

## 步骤 1：查询主表获取项目配置

使用 lark-mcp 的 bitable API 查询数据表，按地盤和場景筛选：

```bash
# 查询特定地盤和場景的记录
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

### 关键字段提取

从查询结果中提取：

| 字段 | 用途 |
|------|------|
| `record_id` | 主表记录 ID，用于后续回填 |
| `測試群group id` | WhatsApp 测试群 ID |
| `正式群group id` | WhatsApp 生产群 ID（禁止发送） |
| `PRD` | 需求文档链接（需权限） |
| `原始需求副本` | 需求文档副本（无需权限） |
| `紙本/E-permit` | 许可类型，决定报告模板 |
| `自测负责人` | 负责人 |

## 步骤 2：读取需求文档

优先使用 PRD，无权限时自动切换到原始需求副本：

```bash
# 读取文档内容
curl -X POST http://localhost:3456/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "docx_v1_document_rawContent",
      "arguments": {
        "path": {"document_id": "<DOC_TOKEN>"},
        "useUAT": true
      }
    }
  }'
```

提取业务规则详见 `references/doc-extraction-guide.md`。

## 步骤 3：输出项目配置

使用 `scripts/build_profile.py` 生成配置：

```bash
python3 scripts/build_profile.py \
  --input bitable_record.json \
  --output outputs/<run-id>/project-profile.json
```

## 步骤 4：创建自测报告表格

测试完成后，使用 `scripts/create_test_report_sheet.py` 创建飞书多维表格保存报告：

```bash
export LARK_APP_ID=<APP_ID>
export LARK_APP_SECRET=<APP_SECRET>

python3 scripts/create_test_report_sheet.py \
  --main-table-record-id <RECORD_ID> \
  --test-results outputs/<run-id>/results.jsonl \
  --site-name "BMM柴灣" \
  --scene "外牆棚架"
```

脚本会：
1. 创建新的多维表格（标题格式：`<地盘> <场景> 自测报告`）
2. 设置字段：测试项、状态（PASS/FAIL/BLOCKED）、输入、预期结果、实际结果、证据、缺陷描述
3. 将测试结果写入表格
4. 将表格链接自动回填到主表的"自测报告"字段

## 步骤 5：自动回填主表

`create_test_report_sheet.py` 会自动完成回填，使用 `bitable_v1_appTableRecord_update` API 更新主表：

```json
{
  "fields": {
    "自测报告": [{
      "link": "https://cohlzhtweb.feishu.cn/base/<APP_TOKEN>",
      "text": "<地盘> <场景> 自测报告",
      "token": "<APP_TOKEN>",
      "type": "mention",
      "mentionType": "Bitable",
      "realMentionType": "Bitable"
    }]
  }
}
```

## 自测报告模板

根据 `紙本/E-permit` 字段选择报告模板：

| 紙本/E-permit | 模板 |
|---------------|------|
| 紙 | 纸permit类业务 |
| E-permit | e-permit类业务 |
| 都有 | 根据具体场景选择 |
| 巡火 | 非标准业务 |

模板表格（`tblqzlnEuGDoDf3U`）包含已有模板文档链接。

## lark-mcp 安装和认证

### 安装

```bash
# 安装 Node.js
curl -L -o node-arm64.tar.xz "https://nodejs.org/dist/v20.11.0/node-v20.11.0-darwin-arm64.tar.xz"
mkdir -p ~/.local && cd ~/.local && tar -xf node-arm64.tar.xz
ln -sf ~/.local/node-v20.11.0-darwin-arm64 ~/.local/node
echo "export PATH=\$HOME/.local/node/bin:\$PATH" >> ~/.zshrc

# 安装 lark-mcp
npm install -g @larksuiteoapi/lark-mcp
```

### 认证

```bash
lark-mcp login -a <APP_ID> -s <APP_SECRET>
```

### 启动 MCP 服务

```bash
lark-mcp mcp -a <APP_ID> -s <APP_SECRET> --mode stdio -l zh
```

## 参考文档

- `references/bitable-schema.md` - 多维表格完整字段定义
- `references/doc-extraction-guide.md` - 需求文档提取指南
