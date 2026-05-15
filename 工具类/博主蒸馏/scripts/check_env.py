#!/usr/bin/env python3
"""
环境检查：Python 版本、依赖、Spider_XHS 目录
"""

import sys
import os
import subprocess


def check_python_version():
    required = (3, 10)
    current = sys.version_info[:2]
    ok = current >= required
    print(f"{'✅' if ok else '❌'} Python 版本: {sys.version.split()[0]} {'>=3.10' if ok else '<3.10'}")
    return ok


def check_nodejs():
    try:
        r = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5)
        ok = r.returncode == 0
        print(f"{'✅' if ok else '❌'} Node.js: {r.stdout.strip() if ok else '未找到'}")
        return ok
    except Exception:
        print("❌ Node.js: 未找到或无法运行")
        return False


def check_spider_xhs():
    spider_dir = os.path.join(os.path.dirname(__file__), "..", "spider_xhs")
    env_file = os.path.join(spider_dir, ".env")
    has_dir = os.path.isdir(spider_dir)
    has_env = os.path.isfile(env_file)
    print(f"{'✅' if has_dir else '❌'} Spider_XHS 目录: {spider_dir}")
    if has_env:
        print(f"✅ Cookie 文件: {env_file}")
    else:
        print(f"❌ Cookie 文件未找到: {env_file}")
    return has_dir and has_env


def main():
    print()
    print("=" * 50)
    print("  环境检查")
    print("=" * 50)
    ok_py = check_python_version()
    ok_node = check_nodejs()
    ok_spider = check_spider_xhs()
    all_ok = ok_py and ok_node and ok_spider
    print(f"\n{'✅ 环境检查通过' if all_ok else '❌ 环境检查未通过'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
