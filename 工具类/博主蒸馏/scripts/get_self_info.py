#!/usr/bin/env python3
"""返回当前登录账号信息（JSON）"""
import sys, os, json

# 设置路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

spider_dir = os.path.join(script_dir, "..", "spider_xhs")
sys.path.insert(0, spider_dir)
os.chdir(spider_dir)

os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from spider_xhs_adapter import get_self_user_info
info, err = get_self_user_info()
if info:
    print(json.dumps({"ok": True, "nickname": info.get("nickname", ""), "user_id": info.get("user_id", ""), "error": ""}, ensure_ascii=False))
else:
    print(json.dumps({"ok": False, "nickname": "", "user_id": "", "error": err or "unknown"}, ensure_ascii=False))
