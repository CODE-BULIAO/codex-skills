---
name: csmart-lark-docs
description: "从飞书多维表格读取 C-Smart 项目配置，支持所有自测技能（巡火、E-permit 等）获取测试所需的项目信息。读取地盤、場景、PRD、测试群 ID 等配置，自动提取业务规则并生成测试计划所需的数据。"
---

# C-Smart 飞书文档读取技能

本技能从飞书多维表格读取项目配置，为下游自测技能提供测试所需的项目信息。

## 飞书多维表格信息

**表格名称**：各地盤群組配置情況

**Wiki Token**：`KvUmwCEIDin2p8kVhVIc8oyCnZg`

**Bitable App Token**：`Vt0cbMdcRa6L9ZsJirJcs2tKnLg`

**数据表**：
- `tbl77ycCEeb0i1y7` - 数据表（主表，19 字段）
- `tblM2aRPrkvnjnyr` - bug記錄（17 字段）
- `tblqzlnEuGDoDf3U` - 自测报告模板（2 字段）

## 读取流程

### 1. 确定目标项目

用户提供地盤名称和場景类型，或从上下文推断：
- **地盤**：工地名称（如 "BMM柴灣"、"启德医院"）
- **場景**：业务类型，单选值包括：
  - 出料臺、吊船、外牆棚架、Lift Shaft、熱工序
  - EWPP 升降台作業、Hanger、Drill Hole、Pipe Duct
  - EWP帶電工程、CSP密閉空間工作、巡火

### 2. 查询数据表

使用 lark-mcp 工具查询 bitable 数据表：

```bash
# 初始化 MCP 连接
lark-mcp mcp -a <APP_ID> -s <APP_SECRET> --mode stdio -l zh

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

### 3. 提取关键字段

从查询结果中提取以下字段：

**路由信息**：
- `測試群組名`：WhatsApp 测试群名称
- `測試群group id`：测试群 ID（格式：`120363xxx@g.us`）
- `正式群組名`：生产群名称
- `正式群group id`：生产群 ID

**需求文档**：
- `PRD`：需求文档链接（需要权限）
- `原始需求副本`：需求文档副本链接（不需要权限，内容与 PRD 相同）

**业务配置**：
- `紙本/E-permit`：紙 / 都有 / E-permit / 未知 / 巡火
- `优先级`：P1 / P2 / P3 / 定製化
- `自测负责人`：负责人姓名
- `自测报告`：已有报告链接（如有）

**其他**：
- `是否已开发`：是 / 否
- `是否已交付`：是 / 否
- `对应多维表格`：关联的 bitable 链接（如有）
- `llm模型` / `llm base url` / `llm key`：LLM 配置（如有）
- `備註`：备注信息

### 4. 读取需求文档

优先使用 `PRD` 链接，如果无权限则自动切换到 `原始需求副本`：

```bash
# 读取文档内容（PRD 或副本）
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
        "path": {
          "document_id": "<DOC_TOKEN>"
        },
        "useUAT": true
      }
    }
  }'
```

### 5. 提取业务规则

从需求文档中提取：
- **触发词**：识别业务的关键词
- **点位字典**：有效的点位列表
- **调度规则**：定时任务的 cron 表达式
- **业务日规则**：跨日重置时间
- **输入格式**：用户输入的格式规范

详细提取规则参见 `references/doc-extraction-guide.md`。

### 6. 选择自测报告模板

根据 `紙本/E-permit` 字段选择对应的报告模板：

| 类型 | 模板说明 |
|------|---------|
| 紙 / 都有 | 纸permit类业务 |
| E-permit | e-permit类业务 |
| 巡火 / 其他 | 非标准业务 |

### 7. 输出配置

生成配置对象，供下游 skill 使用：

```json
{
  "project": {
    "name": "BMM柴灣",
    "code": "BMM-CHAI-WAN-外牆棚架",
    "scene": "外牆棚架"
  },
  "routing": {
    "test_group_name": "BMM 外牆棚架測試群",
    "test_group_id": "120363410065134145@g.us",
    "prod_group_name": "柴灣外牆棚架正式群",
    "prod_group_id": "120363410065134146@g.us"
  },
  "requirements": {
    "prd_url": "https://cohlzhtweb.feishu.cn/wiki/Ej0Ow8I0Jip6E5kAE5KcVvMXnEb",
    "prd_copy_url": "https://cohlzhtweb.feishu.cn/wiki/VKCxwST7eidsqak3f6gcmZuKnvh",
    "paper_type": "都有",
    "business_rules": {
      "triggers": ["外牆棚架", "棚架許可"],
      "points": [...],
      "schedule": "cron 0 18-23,0 * * *",
      "business_day_start": 6
    }
  },
  "metadata": {
    "priority": "P2",
    "developed": true,
    "delivered": false,
    "owner": "zhangziyu"
  }
}
```

## lark-mcp 安装和认证

### 安装 Node.js

```bash
# 下载 Node.js
curl -L -o node-arm64.tar.xz "https://nodejs.org/dist/v20.11.0/node-v20.11.0-darwin-arm64.tar.xz"

# 解压到用户目录
mkdir -p ~/.local && cd ~/.local && tar -xf /tmp/node-arm64.tar.xz
ln -sf ~/.local/node-v20.11.0-darwin-arm64 ~/.local/node

# 添加到 PATH
echo "export PATH=\$HOME/.local/node/bin:\$PATH" >> ~/.zshrc
export PATH=$HOME/.local/node/bin:$PATH
```

### 安装 lark-mcp

```bash
npm install -g @larksuiteoapi/lark-mcp
```

### 认证

```bash
lark-mcp login -a <APP_ID> -s <APP_SECRET>
```

认证后会在浏览器中打开授权页面，完成后即可使用。

### 启动 MCP 服务

```bash
lark-mcp mcp -a <APP_ID> -s <APP_SECRET> --mode streamable --port 3456 -l zh
```

## 字段说明

详细的字段定义和示例参见 `references/bitable-schema.md`。

## 错误处理

- **PRD 无权限**：自动使用 `原始需求副本`
- **记录不存在**：提示用户检查地盤和場景名称
- **MCP 连接失败**：检查 lark-mcp 服务是否运行
- **文档读取失败**：检查文档 token 是否正确
