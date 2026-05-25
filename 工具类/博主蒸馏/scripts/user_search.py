"""
小红书用户搜索 — 搜索博主/用户

用法：
    python user_search.py --keyword "露营博主" --max-users 10 --output ./data
"""

import os
import sys
import json
import time
import argparse
import re

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "utils"))
from utils.common import patch_subprocess_utf8
patch_subprocess_utf8()

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SPIDER_DIR = os.path.join(_SCRIPT_DIR, "..", "spider_xhs")
if not os.path.isdir(SPIDER_DIR):
    SPIDER_DIR = os.path.join(_SCRIPT_DIR, "..", "..", "..", "tools", "Spider_XHS")
if not os.path.isdir(SPIDER_DIR):
    print(f"__ERROR__: 未找到 spider_xhs 目录")
    sys.exit(1)

SPIDER_DIR = os.path.abspath(SPIDER_DIR)
sys.path.insert(0, SPIDER_DIR)
os.chdir(SPIDER_DIR)


def search_users(keyword: str, max_users: int, output_dir: str):
    from apis.xhs_pc_apis import XHS_Apis
    from xhs_utils.common_util import load_env

    cookies_str = load_env()
    if not cookies_str:
        print("__ERROR__: Cookie 为空")
        sys.exit(1)

    api = XHS_Apis()
    print(f"🔍 搜索用户: {keyword}")

    success, msg, user_list = api.search_some_user(keyword, max_users, cookies_str)

    if not success or not user_list:
        print(f"__ERROR__: 搜索失败: {msg}")
        sys.exit(1)

    users = []
    for u in user_list:
        try:
            user_id = u.get("id", u.get("user_id", u.get("userId", "")))
            nickname = u.get("name", u.get("nickname", u.get("nickName", "")))
            avatar = u.get("image", u.get("avatar", u.get("avatar_url", "")))
            desc = u.get("sub_title", u.get("desc", u.get("description", "")))
            fans = u.get("fans", u.get("fans_count", u.get("follower_count", u.get("fans_total", "0"))))
            notes = u.get("note_count", u.get("notes", u.get("notes_count", "0")))

            users.append({
                "user_id": user_id,
                "nickname": nickname,
                "avatar": avatar,
                "desc": desc,
                "fans": str(fans),
                "notes": str(notes),
                "home_url": f"https://www.xiaohongshu.com/user/profile/{user_id}" if user_id else "",
            })
        except Exception as e:
            print(f"  ⚠️ 解析用户失败: {e}")
            continue

    output = {
        "keyword": keyword,
        "total": len(users),
        "users": users,
        "search_time": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    os.makedirs(output_dir, exist_ok=True)
    safe_name = re.sub(r'[\\/:*?"<>|]', "_", keyword)
    output_path = os.path.join(output_dir, f"usersearch_{safe_name}_{int(time.time())}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*40}")
    print(f"✅ 用户搜索完成: {len(users)} 个用户")
    print(f"   关键词: {keyword}")
    print(f"   输出: {output_path}")
    print(f"{'='*40}")
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="小红书用户搜索")
    parser.add_argument("--keyword", required=True, help="搜索关键词")
    parser.add_argument("--max-users", type=int, default=10, help="最大用户数（默认10）")
    parser.add_argument("--output", "-o", default="./data", help="输出目录")
    args = parser.parse_args()

    search_users(args.keyword, args.max_users, args.output)
