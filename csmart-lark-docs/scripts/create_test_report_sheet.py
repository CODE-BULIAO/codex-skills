#!/usr/bin/env python3
"""
创建飞书多维表格用于保存自测报告，并自动回填到主表。

用法：
  create_test_report_sheet.py \
    --main-table-record-id <RECORD_ID> \
    --test-results <RESULTS_JSON> \
    --site-name <SITE_NAME> \
    --scene <SCENE>

环境变量：
  LARK_APP_ID: 飞书应用 App ID
  LARK_APP_SECRET: 飞书应用 App Secret
"""

import json
import argparse
import sys
import subprocess
import time
import os
from pathlib import Path


def run_lark_mcp_command(command: dict, app_id: str, app_secret: str) -> dict:
    """执行 lark-mcp 命令并返回结果。"""
    cmd_str = json.dumps(command)
    
    full_cmd = (
        f'echo \'{cmd_str}\' | '
        f'lark-mcp mcp -a {app_id} -s {app_secret} --mode stdio -l zh 2>/dev/null'
    )
    
    result = subprocess.run(
        full_cmd,
        shell=True,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"lark-mcp 命令失败: {result.stderr}")
    
    # 解析 JSON-RPC 响应（取最后一行有效 JSON）
    lines = result.stdout.strip().split('\n')
    for line in reversed(lines):
        line = line.strip()
        if line.startswith('{'):
            try:
                return json.loads(line)
            except:
                continue
    
    raise RuntimeError(f"无法解析 lark-mcp 响应: {result.stdout[:200]}")


def create_bitable(app_id: str, app_secret: str, title: str) -> str:
    """创建新的飞书多维表格，返回 app_token。"""
    command = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "bitable_v1_app_create",
            "arguments": {
                "data": {"name": title},
                "useUAT": True
            }
        }
    }
    
    result = run_lark_mcp_command(command, app_id, app_secret)
    
    if "error" in result:
        raise RuntimeError(f"创建表格失败: {result['error']}")
    
    content = result.get("result", {}).get("content", [])
    if not content:
        raise RuntimeError("创建表格失败: 无响应内容")
    
    text = content[0].get("text", "{}")
    data = json.loads(text)
    
    if "code" in data and data["code"] != 0:
        raise RuntimeError(f"创建表格失败: {data.get('msg', '未知错误')}")
    
    return data.get("app_token")


def get_default_table_id(app_token: str, app_id: str, app_secret: str) -> str:
    """获取新创建表格的默认数据表 ID。"""
    command = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "bitable_v1_appTable_list",
            "arguments": {
                "path": {"app_token": app_token},
                "useUAT": True
            }
        }
    }
    
    result = run_lark_mcp_command(command, app_id, app_secret)
    content = result.get("result", {}).get("content", [])
    
    if content:
        text = content[0].get("text", "{}")
        data = json.loads(text)
        tables = data.get("items", [])
        if tables:
            return tables[0]["table_id"]
    
    raise RuntimeError("无法获取默认数据表 ID")


def setup_report_fields(app_token: str, table_id: str, app_id: str, app_secret: str) -> None:
    """设置报告表格的字段。"""
    # 添加自定义字段
    fields_to_add = [
        {"field_name": "测试项", "type": 1},  # Text
        {"field_name": "状态", "type": 3, "property": {  # SingleSelect
            "options": [
                {"name": "PASS", "color": 0},
                {"name": "FAIL", "color": 1},
                {"name": "BLOCKED", "color": 2}
            ]
        }},
        {"field_name": "输入", "type": 1},  # Text
        {"field_name": "预期结果", "type": 1},  # Text
        {"field_name": "实际结果", "type": 1},  # Text
        {"field_name": "证据", "type": 1},  # Text
        {"field_name": "缺陷描述", "type": 1},  # Text
    ]
    
    for i, field in enumerate(fields_to_add):
        command = {
            "jsonrpc": "2.0",
            "id": i + 10,
            "method": "tools/call",
            "params": {
                "name": "bitable_v1_appTableField_create",
                "arguments": {
                    "path": {
                        "app_token": app_token,
                        "table_id": table_id
                    },
                    "data": {"field": field},
                    "useUAT": True
                }
            }
        }
        
        try:
            run_lark_mcp_command(command, app_id, app_secret)
            time.sleep(0.1)
        except Exception as e:
            print(f"  警告: 创建字段 {field['field_name']} 失败: {e}", file=sys.stderr)


def write_test_results(app_token: str, table_id: str, results: list, app_id: str, app_secret: str) -> None:
    """将测试结果写入多维表格。"""
    for i, result in enumerate(results):
        fields = {
            "测试项": [{"text": result.get("test_name", ""), "type": "text"}],
            "状态": result.get("status", ""),
            "输入": [{"text": str(result.get("input", "")), "type": "text"}],
            "预期结果": [{"text": str(result.get("expected", "")), "type": "text"}],
            "实际结果": [{"text": str(result.get("actual", "")), "type": "text"}],
            "证据": [{"text": str(result.get("evidence", "")), "type": "text"}],
            "缺陷描述": [{"text": str(result.get("defect", "")), "type": "text"}],
        }
        
        command = {
            "jsonrpc": "2.0",
            "id": i + 100,
            "method": "tools/call",
            "params": {
                "name": "bitable_v1_appTableRecord_create",
                "arguments": {
                    "path": {
                        "app_token": app_token,
                        "table_id": table_id
                    },
                    "data": {"fields": fields},
                    "useUAT": True
                }
            }
        }
        
        run_lark_mcp_command(command, app_id, app_secret)
        time.sleep(0.1)


def update_main_table(record_id: str, report_link: str, report_title: str, app_id: str, app_secret: str) -> None:
    """更新主表中的"自测报告"字段。"""
    main_app_token = "Vt0cbMdcRa6L9ZsJirJcs2tKnLg"
    main_table_id = "tbl77ycCEeb0i1y7"
    
    report_field = [{
        "link": report_link,
        "text": report_title,
        "token": report_link.split("/")[-1].split("?")[0],
        "type": "mention",
        "mentionType": "Bitable",
        "realMentionType": "Bitable"
    }]
    
    command = {
        "jsonrpc": "2.0",
        "id": 200,
        "method": "tools/call",
        "params": {
            "name": "bitable_v1_appTableRecord_update",
            "arguments": {
                "path": {
                    "app_token": main_app_token,
                    "table_id": main_table_id,
                    "record_id": record_id
                },
                "data": {
                    "fields": {
                        "自测报告": report_field
                    }
                },
                "useUAT": True
            }
        }
    }
    
    result = run_lark_mcp_command(command, app_id, app_secret)
    
    if "error" in result:
        raise RuntimeError(f"更新主表失败: {result['error']}")
    
    content = result.get("result", {}).get("content", [])
    if content:
        text = content[0].get("text", "{}")
        data = json.loads(text)
        if "code" in data and data["code"] != 0:
            raise RuntimeError(f"更新主表失败: {data.get('msg', '未知错误')}")


def main():
    parser = argparse.ArgumentParser(description="创建自测报告表格并回填主表")
    parser.add_argument("--main-table-record-id", required=True, help="主表记录 ID")
    parser.add_argument("--test-results", required=True, help="测试结果 JSON 文件")
    parser.add_argument("--site-name", required=True, help="地盘名称")
    parser.add_argument("--scene", required=True, help="场景名称")
    
    args = parser.parse_args()
    
    # 从环境变量获取飞书凭证
    app_id = os.environ.get("LARK_APP_ID")
    app_secret = os.environ.get("LARK_APP_SECRET")
    
    if not app_id or not app_secret:
        print("错误：请设置环境变量 LARK_APP_ID 和 LARK_APP_SECRET", file=sys.stderr)
        sys.exit(1)
    
    # 读取测试结果
    results_path = Path(args.test_results)
    if not results_path.exists():
        print(f"错误：测试结果文件不存在：{args.test_results}", file=sys.stderr)
        sys.exit(1)
    
    with open(results_path, "r", encoding="utf-8") as f:
        test_results = json.load(f)
    
    # 创建报告表格
    report_title = f"{args.site_name} {args.scene} 自测报告"
    print(f"正在创建多维表格: {report_title}")
    
    app_token = create_bitable(app_id, app_secret, report_title)
    print(f"✓ 表格已创建: {app_token}")
    
    # 获取默认数据表 ID
    table_id = get_default_table_id(app_token, app_id, app_secret)
    print(f"✓ 数据表 ID: {table_id}")
    
    # 设置字段
    print("正在设置表格字段...")
    setup_report_fields(app_token, table_id, app_id, app_secret)
    print("✓ 字段已设置")
    
    # 写入测试结果
    print(f"正在写入 {len(test_results)} 条测试结果...")
    write_test_results(app_token, table_id, test_results, app_id, app_secret)
    print(f"✓ 测试结果已写入")
    
    # 构建表格链接
    report_link = f"https://cohlzhtweb.feishu.cn/base/{app_token}"
    
    # 更新主表
    print(f"正在更新主表记录: {args.main_table_record_id}")
    update_main_table(args.main_table_record_id, report_link, report_title, app_id, app_secret)
    print(f"✓ 主表已更新")
    
    print(f"\n✅ 完成！")
    print(f"报告链接: {report_link}")
    
    # 输出 JSON 结果
    output = {
        "status": "SUCCESS",
        "report_token": app_token,
        "table_id": table_id,
        "report_link": report_link,
        "report_title": report_title,
        "records_written": len(test_results)
    }
    
    print(f"\n{json.dumps(output, ensure_ascii=False, indent=2)}")


if __name__ == "__main__":
    main()
