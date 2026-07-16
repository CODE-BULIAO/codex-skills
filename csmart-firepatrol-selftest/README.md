# C-Smart 自测技能集合

C-Smart 系统的 Codex 自测技能仓库，集中管理各类业务的自动化测试技能和辅助工具。

## 技能列表

| 技能名称 | 功能说明 |
|---------|---------|
| csmart-firepatrol-selftest | C-Smart 通用巡火/夜巡自测：通过 project-profile.json 动态获取项目配置，覆盖测试群安全校验、点位与区间解析、跨日状态处理、定时/手动总结、缺失点统计、需求变更测试、运行耗时与 Token 消耗报告 |
| csmart-epermit-selftest | C-Smart E-permit（电子许可）系统自测：覆盖动火许可、纸质许可、安全照片、提醒、短码、webhook 状态及许可记录工作流 |
| csmart-lark-docs | C-Smart 飞书文档读取：从飞书项目索引表和文档中发现项目信息，生成 project-profile.json 供自测技能使用 |

## 目录结构

```
├── README.md                                  # 本文件
├── csmart-firepatrol-selftest/                # 通用巡火自测技能
│   ├── SKILL.md
│   ├── agents/
│   ├── evals/
│   │   └── generic-contracts.jsonl           # 参数化通用契约
│   ├── references/
│   │   └── test-baseline.md                  # 通用测试原则
│   ├── scripts/
│   │   ├── generate_cases.py                 # 动态生成测试计划
│   │   ├── runtime.py                        # 运行时配置发现（支持 --profile）
│   │   ├── send_image.py                     # 图片发送（支持 --profile）
│   │   ├── merge_cases.py                    # 合并测试计划
│   │   ├── build_report.py                   # 生成测试报告
│   │   └── fire_patrol_snapshot.py           # 状态快照
│   ├── tests/
│   │   ├── fixtures/                         # 多项目验证数据
│   │   ├── test_baseline.py
│   │   └── test_scripts.py
│   └── outputs/                              # 运行时输出目录
├── csmart-epermit-selftest/                   # E-permit 自测技能
│   ├── SKILL.md
│   ├── agents/
│   ├── config.example.json
│   ├── data/
│   ├── evals/
│   ├── references/
│   ├── scripts/
│   └── tests/
└── csmart-lark-docs/                          # 飞书文档读取技能
    ├── SKILL.md
    ├── agents/
    ├── references/
    │   ├── project-index-schema.md           # 项目索引表结构
    │   └── doc-extraction-guide.md           # 文档提取指南
    └── scripts/
        └── build_profile.py                  # 生成 project-profile.json
```

## 工作流程

```
飞书项目索引表 → csmart-lark-docs → project-profile.json → csmart-firepatrol-selftest → 测试报告
```

1. 使用 `csmart-lark-docs` 从飞书文档中发现项目信息
2. 生成 `project-profile.json` 配置文件
3. 使用 `csmart-firepatrol-selftest` 读取配置，动态生成测试计划并执行

## 添加新技能

在仓库根目录创建新的子文件夹，包含 `SKILL.md` 和相关的测试资源，并更新上方表格。
