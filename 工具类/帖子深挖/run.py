#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书帖子深度分析器 - Skill入口
"""

import sys
import os
import argparse
import subprocess

SKILL_ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(SKILL_ROOT, "scripts")


def main():
    parser = argparse.ArgumentParser(description="小红书帖子深度分析器")
    parser.add_argument("url", help="小红书帖子链接")
    parser.add_argument("-o", "--output", default="./output/帖子深挖", help="输出目录")
    args = parser.parse_args()

    import re
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    python = sys.executable
    analyze_script = os.path.join(SCRIPTS_DIR, "analyze_post.py")

    # 生成输出文件名（支持 /item/ 和 /explore/ 两种格式）
    match = re.search(r'/(?:item|explore)/([a-f0-9]+)', args.url)
    note_id = match.group(1) if match else "unknown"
    output_file = os.path.join(args.output, f"帖子分析_{note_id}.md")

    cmd = [
        python, analyze_script,
        args.url,
        "-o", output_file
    ]

    print(f"[START] 开始分析帖子: {args.url}")
    print(f"[OUTPUT] {output_file}")
    print()

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print(f"\n[DONE] 分析完成！报告: {output_file}")
    else:
        print(f"\n[FAIL] 分析失败（退出码: {result.returncode}）")
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
