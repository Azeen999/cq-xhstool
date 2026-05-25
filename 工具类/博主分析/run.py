#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书博主风格分析器 - 一键运行入口
使用本地爬虫获取博主数据，无需 TikHub Token
"""
import os
import sys
import argparse
import random
import time
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "博主蒸馏" / "scripts" / "utils"))
from utils.common import patch_subprocess_utf8
patch_subprocess_utf8()

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# 添加项目路径（确保能找到 scripts/ 模块）
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent))

from scripts.crawl import crawl_blogger_notes
from scripts.analyze import analyze_blogger_style
from scripts.report import generate_html_report
from scripts.skill_generator import generate_skill

def random_delay(min_delay=15, max_delay=30):
    """随机延迟，防封"""
    delay = random.uniform(min_delay, max_delay)
    print(f"  [DELAY] 等待 {delay:.1f} 秒...")
    time.sleep(delay)

def main():
    parser = argparse.ArgumentParser(description='小红书博主风格分析器')
    parser.add_argument('--url', type=str, help='博主主页链接')
    parser.add_argument('--name', type=str, help='博主名（会自动搜索）')
    parser.add_argument('--max-notes', type=int, default=50, help='最大采集数量')
    parser.add_argument('--output', type=str, default='./output', help='输出目录')
    args = parser.parse_args()

    # 参数校验
    if not args.url and not args.name:
        print("[ERROR] 必须提供 --url 或 --name 参数")
        sys.exit(1)

    print("="*60)
    print("🌟 小红书博主风格分析器")
    print("="*60)

    # 创建输出目录
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # ========== Phase 1: 数据采集 ==========
        print("\n📥 Phase 1: 数据采集")
        print("-"*40)
        
        notes_dir = output_dir / f"{args.name or 'unknown'}_笔记"
        notes_dir.mkdir(exist_ok=True)

        notes = crawl_blogger_notes(
            url=args.url,
            name=args.name,
            max_notes=args.max_notes,
            output_dir=notes_dir
        )
        
        if not notes:
            print("[ERROR] 采集失败，退出")
            sys.exit(1)
        
        print(f"✅ 成功采集 {len(notes)} 篇笔记")

        # ========== Phase 2: 风格分析 ==========
        print("\n🔍 Phase 2: 风格分析")
        print("-"*40)
        
        analysis_result = analyze_blogger_style(notes)
        print("✅ 分析完成")

        # ========== Phase 3: 生成 HTML 报告 ==========
        print("\n📝 Phase 3: 生成分析报告")
        print("-"*40)
        
        report_path = generate_html_report(
            analysis_result, 
            notes,
            output_dir / f"{args.name or 'unknown'}_分析报告.html"
        )
        print(f"✅ HTML 报告已生成: {report_path}")

        # ========== Phase 4: 生成创作 Skill ==========
        print("\n🧩 Phase 4: 生成创作指南")
        print("-"*40)
        
        skill_dir = generate_skill(analysis_result, output_dir)
        print(f"✅ 创作指南已生成: {skill_dir}")

        # ========== 完成 ==========
        print("\n" + "="*60)
        print("🎉 分析完成！")
        print(f"📂 笔记数据: {notes_dir}")
        print(f"📄 分析报告: {report_path}")
        print(f"🧩 创作指南: {skill_dir}")
        print("="*60)

    except Exception as e:
        print(f"[ERROR] 分析过程出错: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()