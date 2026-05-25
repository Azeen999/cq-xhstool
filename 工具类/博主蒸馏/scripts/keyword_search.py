"""
小红书关键词搜索 — 搜索笔记 + 获取详情 + 获取评论

用法：
    python keyword_search.py --keyword "露营" --max-notes 20 --time-range week --output ./data

时间范围：
    day    — 一天内
    week   — 一周内
    half   — 半年内
    all    — 不限（默认）

排序方式：
    general     — 综合排序（默认）
    time        — 最新优先
    popularity  — 最多点赞
    comment     — 最多评论
    collect     — 最多收藏
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

TIME_RANGE_MAP = {
    "day": 1,
    "week": 2,
    "half": 3,
    "all": 0,
}

SORT_TYPE_MAP = {
    "general": 0,
    "time": 1,
    "popularity": 2,
    "comment": 3,
    "collect": 4,
}


def random_delay(min_s=10, max_s=20):
    delay = random.uniform(min_s, max_s)
    print(f"  ⏳ 等待 {delay:.1f}s...")
    time.sleep(delay)


def short_delay(min_s=5, max_s=10):
    delay = random.uniform(min_s, max_s)
    time.sleep(delay)


def search_notes(keyword, max_notes, time_range, sort_type, fetch_comments=True):
    from apis.xhs_pc_apis import XHS_Apis
    from xhs_utils.common_util import load_env
    from xhs_utils.data_util import handle_note_info, handle_comment_info

    cookies_str = load_env()
    if not cookies_str:
        print("__ERROR__: Cookie为空，请先在设置中配置小红书Cookie")
        sys.exit(1)

    api = XHS_Apis()

    note_time = TIME_RANGE_MAP.get(time_range, 0)
    sort_choice = SORT_TYPE_MAP.get(sort_type, 0)

    print(f"\n{'='*60}")
    print(f"🔍 关键词搜索: {keyword}")
    print(f"📊 目标: {max_notes} 条 | 时间: {time_range} | 排序: {sort_type}")
    print(f"{'='*60}")

    print(f"\n📋 搜索笔记列表...")
    random_delay(8, 15)

    success, msg, notes = api.search_some_note(
        query=keyword,
        require_num=max_notes,
        cookies_str=cookies_str,
        sort_type_choice=sort_choice,
        note_type=0,
        note_time=note_time,
    )

    if not success:
        print(f"__ERROR__: 搜索失败: {msg}")
        sys.exit(1)

    notes = [n for n in notes if n.get('model_type') == 'note']
    print(f"✅ 搜索到 {len(notes)} 条笔记")

    results = []
    for i, note_item in enumerate(notes[:max_notes], 1):
        note_card = note_item.get('note_card', note_item.get('model_type', {}))
        if isinstance(note_card, str):
            note_card = note_item

        note_id = note_card.get('note_id', note_item.get('id', note_item.get('note_id', '')))
        title = note_card.get('display_title', note_card.get('title', ''))
        xsec_token = note_card.get('xsec_token', note_item.get('xsec_token', ''))
        user_info = note_card.get('user', {})
        nickname = user_info.get('nickname', '未知博主')
        interact = note_card.get('interact_info', {})

        print(f"\n[{i}/{min(max_notes, len(notes))}] {note_id} — {title[:30]}")

        note_url = f"https://www.xiaohongshu.com/explore/{note_id}?xsec_token={xsec_token}"

        random_delay(12, 25)

        note_data = None
        try:
            success_n, msg_n, note_detail = api.get_note_info(note_url, cookies_str)
            if success_n and note_detail:
                items = note_detail.get('data', {}).get('items', [])
                if items:
                    item = items[0]
                    item['url'] = note_url
                    note_data = handle_note_info(item)
        except Exception as e:
            print(f"  ⚠️ 获取详情失败: {str(e)}")

        if not note_data:
            note_data = {
                'note_id': note_id,
                'note_url': note_url,
                'note_type': '视频' if note_card.get('type') == 'video' else '图集',
                'user_id': user_info.get('user_id', ''),
                'home_url': f"https://www.xiaohongshu.com/user/profile/{user_info.get('user_id', '')}",
                'nickname': nickname,
                'avatar': user_info.get('avatar', ''),
                'title': title,
                'desc': note_card.get('desc', ''),
                'liked_count': interact.get('liked_count') or '0',
                'collected_count': interact.get('collected_count') or '0',
                'comment_count': interact.get('comment_count') or '0',
                'share_count': interact.get('share_count') or '0',
                'tags': [],
                'upload_time': '',
                'ip_location': note_card.get('ip_location', ''),
            }

        comments_raw = []
        if fetch_comments:
            print("  💬 获取评论...")
            try:
                success_c, msg_c, comment_list = api.get_note_all_comment(note_url, cookies_str)
                if success_c and isinstance(comment_list, list):
                    for c in comment_list:
                        try:
                            c['note_id'] = note_id
                            c['note_url'] = note_url
                            comments_raw.append(handle_comment_info(c))
                        except Exception:
                            pass
                    if comments_raw:
                        print(f"  ✅ {len(comments_raw)} 条评论")
                else:
                    print(f"  ⚠️ 评论获取失败: {msg_c}")
            except Exception as e:
                print(f"  ⚠️ 评论异常: {str(e)}")

        result = {
            "note": note_data,
            "comments": comments_raw,
        }
        results.append(result)

        likes = note_data.get('liked_count', '0')
        collects = note_data.get('collected_count', '0')
        comments = note_data.get('comment_count', '0')
        print(f"  ✅ [{title[:30]}] 赞:{likes} 藏:{collects} 评:{comments} | @{nickname}")

    return results


def save_results(results, keyword, output_dir):
    abs_output_dir = os.path.abspath(output_dir)
    os.makedirs(abs_output_dir, exist_ok=True)

    safe_keyword = re.sub(r'[\\/:*?"<>|]', "_", keyword).strip() or "search"
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_keyword}_搜索结果_{timestamp}.json"
    filepath = os.path.join(abs_output_dir, filename)

    output = {
        "keyword": keyword,
        "search_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_notes": len(results),
        "results": results,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"🎉 搜索完成!")
    print(f"   关键词: {keyword}")
    print(f"   有效: {len(results)} 条")
    print(f"   输出: {filepath}")
    print(f"{'='*60}")

    return filepath


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="小红书关键词搜索")
    parser.add_argument("--keyword", "-k", required=True, help="搜索关键词")
    parser.add_argument("--max-notes", "-n", type=int, default=20, help="最大搜索条数（默认20）")
    parser.add_argument("--time-range", "-t", default="all",
                        choices=["day", "week", "half", "all"],
                        help="时间范围: day=一天内, week=一周内, half=半年内, all=不限")
    parser.add_argument("--sort", "-s", default="general",
                        choices=["general", "time", "popularity", "comment", "collect"],
                        help="排序方式: general=综合, time=最新, popularity=最多点赞, comment=最多评论, collect=最多收藏")
    parser.add_argument("--output", "-o", default="./data", help="输出目录")
    parser.add_argument("--no-comments", action="store_true", help="跳过评论采集（加快速度）")
    args = parser.parse_args()

    results = search_notes(
        keyword=args.keyword,
        max_notes=args.max_notes,
        time_range=args.time_range,
        sort_type=args.sort,
        fetch_comments=not args.no_comments,
    )

    save_results(results, args.keyword, args.output)
