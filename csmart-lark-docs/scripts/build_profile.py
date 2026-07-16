#!/usr/bin/env python3
"""
从飞书多维表格记录构建项目配置。

用法：
  build_profile.py --input bitable_record.json --output profile.json

输入文件格式：bitable_v1_appTableRecord_search 返回的单条记录（包含 record_id 和 fields）
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Any


def extract_token(field_value: Any) -> str | None:
    """从链接字段中提取文档 token。"""
    if isinstance(field_value, list) and len(field_value) > 0:
        item = field_value[0]
        if isinstance(item, dict):
            return item.get("token")
    return None


def extract_link(field_value: Any) -> str | None:
    """从链接字段中提取完整链接。"""
    if isinstance(field_value, list) and len(field_value) > 0:
        item = field_value[0]
        if isinstance(item, dict):
            return item.get("link")
    return None


def extract_text(field_value: Any) -> str | None:
    """从文本字段中提取文本内容。"""
    if isinstance(field_value, str):
        return field_value
    if isinstance(field_value, list) and len(field_value) > 0:
        item = field_value[0]
        if isinstance(item, dict):
            return item.get("text")
    return None


def build_project_profile(record: dict) -> dict:
    """从 bitable 记录构建项目配置。"""
    fields = record.get("fields", {})
    record_id = record.get("record_id", "")
    
    # 提取基本信息
    site_name = extract_text(fields.get("地盤"))
    scene = extract_text(fields.get("場景"))
    paper_type = extract_text(fields.get("紙本/E-permit"))
    
    # 生成项目代码
    project_code = f"{site_name}-{scene}".replace(" ", "-").upper() if site_name and scene else ""
    
    # 提取路由信息
    test_group_name = extract_text(fields.get("測試群組名"))
    test_group_id = extract_text(fields.get("測試群group id"))
    prod_group_name = extract_text(fields.get("正式群組名"))
    prod_group_id = extract_text(fields.get("正式群group id"))
    
    # 提取需求文档链接
    prd_link = extract_link(fields.get("PRD"))
    prd_token = extract_token(fields.get("PRD"))
    prd_copy_link = extract_link(fields.get("原始需求副本"))
    prd_copy_token = extract_token(fields.get("原始需求副本"))
    
    # 提取元数据
    priority = extract_text(fields.get("优先级"))
    developed = extract_text(fields.get("是否已开发")) == "是"
    delivered = extract_text(fields.get("是否已交付")) == "是"
    owner = extract_text(fields.get("自测负责人"))
    
    # 提取报告链接
    report_link = extract_link(fields.get("自测报告"))
    report_token = extract_token(fields.get("自测报告"))
    
    # 提取关联表格
    related_table_link = extract_link(fields.get("对应多维表格"))
    related_table_token = extract_token(fields.get("对应多维表格"))
    
    # 提取 LLM 配置
    llm_model = extract_text(fields.get("llm模型"))
    llm_base_url = extract_text(fields.get("llm base url"))
    llm_key = extract_text(fields.get("llm key"))
    
    # 提取备注
    remarks = extract_text(fields.get("備註"))
    
    # 构建配置对象
    profile = {
        "source": {
            "record_id": record_id,
            "bitable_app_token": "Vt0cbMdcRa6L9ZsJirJcs2tKnLg",
            "table_id": "tbl77ycCEeb0i1y7"
        },
        "project": {
            "name": site_name,
            "code": project_code,
            "scene": scene
        },
        "routing": {
            "test_group_name": test_group_name,
            "test_group_id": test_group_id,
            "prod_group_name": prod_group_name,
            "prod_group_id": prod_group_id
        },
        "requirements": {
            "paper_type": paper_type,
            "prd_url": prd_link,
            "prd_token": prd_token,
            "prd_copy_url": prd_copy_link,
            "prd_copy_token": prd_copy_token,
            "business_rules": {}
        },
        "metadata": {
            "priority": priority,
            "developed": developed,
            "delivered": delivered,
            "owner": owner,
            "remarks": remarks
        }
    }
    
    if report_link:
        profile["existing_report"] = {
            "url": report_link,
            "token": report_token
        }
    
    if related_table_link:
        profile["related_table"] = {
            "url": related_table_link,
            "token": related_table_token
        }
    
    if llm_model and llm_model != "无":
        profile["llm"] = {
            "model": llm_model,
            "base_url": llm_base_url if llm_base_url != "无" else None,
            "key": llm_key if llm_key != "无" else None
        }
    
    return profile


def main():
    parser = argparse.ArgumentParser(description="从 bitable 记录构建项目配置")
    parser.add_argument("--input", "-i", required=True, help="输入的 bitable 记录 JSON 文件")
    parser.add_argument("--output", "-o", required=True, help="输出的项目配置 JSON 文件")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"错误：输入文件不存在：{args.input}", file=sys.stderr)
        sys.exit(1)
    
    with open(input_path, "r", encoding="utf-8") as f:
        record = json.load(f)
    
    profile = build_project_profile(record)
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)
    
    print(json.dumps({"status": "READY", "out": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
