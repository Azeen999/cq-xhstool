"""
小红书热门推荐 — 获取各频道热门笔记

用法：
    python hot_feed.py --category general --max-notes 20 --output ./data
"""

import os
import sys
import json
import time
import random
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

from utils.common import CATEGORY_MAP


def fetch_hot_feed(category: str, max_notes: int, output_dir: str):
    from apis.xhs_pc_apis import XHS_Apis
    from xhs_utils.common_util import load_env
    from xhs_utils.data_util import handle_note_info

    cookies_str = load_env()
    if not cookies_str:
        print("__ERROR__: Cookie 为空")
        sys.exit(1)

    api = XHS_Apis()
    cat_label = CATEGORY_MAP.get(category, category)
    print(f"📡 获取频道 [{cat_label}] 热门推荐...")

    success, msg, note_list = api.get_homefeed_recommend_by_num(category, max_notes, cookies_str)

    if not success or not note_list:
        print(f"__ERROR__: 获取失败: {msg}")
        sys.exit(1)

    notes = []
    for item in note_list:
        try:
            note_data = handle_note_info(item)
            note_id = note_data.get("note_id", item.get("id", ""))
            notes.append({
                "note_id": note_id,
                "title": note_data.get("title", ""),
                "desc": note_data.get("desc", ""),
                "note_type": note_data.get("note_type", ""),
                "user_id": note_data.get("user_id", ""),
                "nickname": note_data.get("nickname", ""),
                "avatar": note_data.get("avatar", ""),
                "home_url": note_data.get("home_url", ""),
                "liked_count": note_data.get("liked_count", "0"),
                "collected_count": note_data.get("collected_count", "0"),
                "comment_count": note_data.get("comment_count", "0"),
                "share_count": note_data.get("share_count", "0"),
                "tags": note_data.get("tags", []),
                "image_list": note_data.get("image_list", []),
                "video_cover": note_data.get("video_cover", ""),
                "ip_location": note_data.get("ip_location", ""),
                "upload_time": note_data.get("upload_time", ""),
            })
        except Exception as e:
            print(f"  ⚠️ 解析笔记失败: {e}")
            continue

    if not notes:
        print("__ERROR__: 未能解析任何笔记")
        sys.exit(1)

    output = {
        "category": category,
        "category_label": cat_label,
        "total": len(notes),
        "results": notes,
        "fetch_time": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    os.makedirs(output_dir, exist_ok=True)
    safe_cat = re.sub(r'[\\/:*?"<>|]', "_", cat_label)
    output_path = os.path.join(output_dir, f"hotfeed_{safe_cat}_{int(time.time())}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*40}")
    print(f"✅ 热门推荐获取完成: {len(notes)} 条")
    print(f"   频道: {cat_label}")
    print(f"   输出: {output_path}")
    print(f"{'='*40}")
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="小红书热门推荐")
    parser.add_argument("--category", default="general", help="频道类别 (general/food/travel/...)")
    parser.add_argument("--max-notes", type=int, default=20, help="数量")
    parser.add_argument("--output", "-o", default="./data", help="输出目录")
    args = parser.parse_args()

    fetch_hot_feed(args.category, args.max_notes, args.output)
