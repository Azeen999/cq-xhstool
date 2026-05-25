"""
Spider_XHS 适配器：用 Spider_XHS 采集博主数据，转换为博主蒸馏器兼容格式。

用法：
    # 方式1：直接输入用户ID
    python spider_xhs_adapter.py --user-id 694cf4f4000000003700bd56 --max-notes 30 --output ./data
    
    # 方式2：输入完整URL（自动提取用户ID）
    python spider_xhs_adapter.py --url "https://www.xiaohongshu.com/user/profile/694cf4f4000000003700bd56?xsec_token=xxx" --max-notes 30
    
    # 方式3：采集自己的账号（自动获取当前登录账号）
    python spider_xhs_adapter.py --self --max-notes 30

博主ID获取方法：
1. 打开小红书用户主页（PC端）
2. URL格式：https://www.xiaohongshu.com/user/profile/{user_id}
3. user_id 就是博主ID，通常是19位数字+字母组合，如：694cf4f4000000003700bd56

注意：如果是采集自己的账号，建议使用 --self 参数，自动获取正确的用户ID
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

# Spider_XHS 目录：优先找脚本旁边的 spider_xhs/，再退回 tools/Spider_XHS
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SPIDER_DIR = os.path.join(_SCRIPT_DIR, "..", "spider_xhs")
if not os.path.isdir(SPIDER_DIR):
    SPIDER_DIR = os.path.join(_SCRIPT_DIR, "..", "..", "..", "tools", "Spider_XHS")
if not os.path.isdir(SPIDER_DIR):
    print(f"❌ 未找到 Spider_XHS 目录（尝试过: {os.path.abspath(SPIDER_DIR)}）")
    sys.exit(1)

SPIDER_DIR = os.path.abspath(SPIDER_DIR)
sys.path.insert(0, SPIDER_DIR)

_original_cwd = os.getcwd()
os.chdir(SPIDER_DIR)


def extract_user_id_from_url(url):
    """从小红书用户主页URL中提取用户ID"""
    # 匹配模式：/user/profile/后面的字符串（18-26位十六进制字符）
    pattern = r'/user/profile/([a-f0-9]{18,26})'
    match = re.search(pattern, url, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def validate_user_id(user_id):
    """验证用户ID格式是否正确"""
    if not user_id:
        return False, "用户ID不能为空"
    # 小红书用户ID是十六进制字符串，长度通常为19-25位
    if not re.match(r'^[a-f0-9]{18,26}$', user_id, re.IGNORECASE):
        return False, f"用户ID格式不正确（应为十六进制字符），当前: {user_id} ({len(user_id)}位)"
    return True, "格式正确"


def get_self_user_info():
    """获取当前登录账号的信息"""
    try:
        from apis.xhs_pc_apis import XHS_Apis
        from xhs_utils.common_util import load_env
        
        cookies_str = load_env()
        if not cookies_str:
            return None, "Cookie为空，请检查 D:\\myproj\\tools\\Spider_XHS\\.env"

        api = XHS_Apis()
        ok, msg, data = api.get_user_self_info(cookies_str)
        
        if not ok or not data:
            return None, f"获取账号信息失败: {msg}"
        
        user_data = data.get('data', {}).get('result', {})
        if not user_data:
            return None, "返回数据格式异常"
        
        user_id = user_data.get('user_id', '')
        nickname = user_data.get('nickname', '')
        notes_count = user_data.get('notes_count', 0)
        fans = user_data.get('fans', 'N/A')
        
        return {
            'user_id': user_id,
            'nickname': nickname,
            'notes_count': notes_count,
            'fans': fans
        }, None
        
    except Exception as e:
        return None, f"获取账号信息异常: {str(e)}"


def random_delay(min_s=35, max_s=60):
    """随机延迟，控制30条笔记总时间约30分钟"""
    delay = random.uniform(min_s, max_s)
    print(f"  ⏳ 等待 {delay:.1f}s...")
    time.sleep(delay)


def short_delay(min_s=8, max_s=15):
    """短延迟，用于列表翻页等操作"""
    delay = random.uniform(min_s, max_s)
    print(f"  ⏳ 等待 {delay:.1f}s...")
    time.sleep(delay)


def initial_delay(min_s=10, max_s=20):
    """初始延迟，第一次请求前"""
    delay = random.uniform(min_s, max_s)
    print(f"⏳ 初始等待 {delay:.1f}s...")
    time.sleep(delay)


def convert_note_to_distiller_format(note_info, comments_raw=None):
    note = {
        "note": {
            "noteId": note_info.get("note_id", ""),
            "title": note_info.get("title", ""),
            "desc": note_info.get("desc", ""),
            "type": "video" if note_info.get("note_type") == "视频" else "normal",
            "interactInfo": {
                "likedCount": str(note_info.get("liked_count", "0")),
                "collectedCount": str(note_info.get("collected_count", "0")),
                "commentCount": str(note_info.get("comment_count", "0")),
                "sharedCount": str(note_info.get("share_count", "0")),
            },
            "tagList": [{"name": t} for t in note_info.get("tags", [])],
            "time": 0,
            # 以下为新增字段
            "noteUrl": note_info.get("note_url", ""),
            "userId": note_info.get("user_id", ""),
            "userHomeUrl": note_info.get("home_url", ""),
            "nickname": note_info.get("nickname", ""),
            "avatar": note_info.get("avatar", ""),
            "imageList": note_info.get("image_list", []),
            "videoCover": note_info.get("video_cover", ""),
            "videoAddr": note_info.get("video_addr", ""),
            "ipLocation": note_info.get("ip_location", ""),
            "uploadTime": note_info.get("upload_time", ""),
        },
        "comments": {"list": []},
        "_feed_id": note_info.get("note_id", ""),
        "_meta": {
            "source": "xhs",
            "adapter": "spider_xhs",
        },
    }

    upload_time_str = note_info.get("upload_time", "")
    if upload_time_str:
        try:
            from datetime import datetime
            dt = datetime.strptime(upload_time_str, "%Y-%m-%d %H:%M:%S")
            note["note"]["time"] = int(dt.timestamp())
        except (ValueError, TypeError):
            pass

    if comments_raw and isinstance(comments_raw, list):
        converted_comments = []
        for c in comments_raw:
            converted_comments.append({
                "content": c.get("content", ""),
                "likeCount": str(c.get("like_count", "0")),
                "userInfo": {
                    "nickname": c.get("nickname", "读者"),
                    "userId": c.get("user_id", ""),
                    "avatar": c.get("avatar", ""),
                },
                "subComments": [],
                "sub_comment_has_more": False,
                "sub_comment_cursor": "",
                "note_id": note_info.get("note_id", ""),
                "id": c.get("comment_id", ""),
                # 新增
                "ipLocation": c.get("ip_location", ""),
                "uploadTime": c.get("upload_time", ""),
            })
        note["comments"]["list"] = converted_comments

    return note


def normalize_note_info(note_info):
    """将原始列表数据标准化为 handle_note_info 的输出格式"""
    interact = note_info.get("interact_info", {})
    return {
        "note_id": note_info.get("note_id", ""),
        "title": note_info.get("display_title", note_info.get("title", "")),
        "desc": note_info.get("desc", ""),
        "note_type": "视频" if note_info.get("type") == "video" else "图集",
        "liked_count": interact.get("liked_count", "0"),
        "collected_count": interact.get("collected_count", "0"),
        "comment_count": interact.get("comment_count", "0"),
        "share_count": interact.get("share_count", "0"),
        "tags": [],
        "upload_time": "",
    }


def crawl_and_convert(user_id, max_notes, output_dir, xsec_token="", fetch_comments=True, nickname=""):
    from apis.xhs_pc_apis import XHS_Apis
    from xhs_utils.common_util import load_env
    from xhs_utils.data_util import handle_note_info, handle_comment_info
    
    cookies_str = load_env()
    if not cookies_str:
        print("❌ Cookie为空，请检查 D:\\myproj\\tools\\Spider_XHS\\.env")
        sys.exit(1)

    api = XHS_Apis()

    print(f"\n{'='*60}")
    print(f"🔍 采集博主笔记: {user_id}")
    print(f"📊 目标: {max_notes} 条")
    if nickname:
        print(f"👤 昵称: {nickname}")
    print(f"{'='*60}")

    print(f"\n📋 获取笔记列表...")
    initial_delay()

    all_notes = []
    cursor = ""
    while len(all_notes) < max_notes:
        success, msg, res_json = api.get_user_note_info(user_id, cursor, cookies_str, xsec_token, "pc_search")
        if not success:
            print(f"❌ 获取笔记列表失败: {msg}")
            break
        
        data = res_json.get("data")
        if not data:
            print(f"⚠️ 返回数据为空，可能Cookie过期或用户无笔记")
            break
        
        notes = data.get("notes", [])
        if not notes:
            break
        
        all_notes.extend(notes)
        print(f"  已获取 {len(all_notes)} 条笔记...")
        
        if not data.get("has_more", False):
            break
        
        cursor = str(data.get("cursor", ""))
        if not cursor:
            break
        
        short_delay()

    if not all_notes:
        print(f"❌ 未获取到任何笔记")
        print(f"   请检查：1. 用户ID是否正确 2. Cookie是否有效 3. 该账号是否有公开笔记")
        sys.exit(1)

    print(f"✅ 共 {len(all_notes)} 篇笔记，采集前 {min(max_notes, len(all_notes))} 篇")

    details = []
    for i, note_info in enumerate(all_notes[:max_notes], 1):
        note_id = note_info.get("note_id", "")
        title = note_info.get("title", "") or note_info.get("display_title", "")
        
        print(f"\n[{i}/{min(max_notes, len(all_notes))}] {note_id}")
        random_delay(15, 30)

        # 获取笔记详情（使用列表中的 xsec_token）
        xsec = note_info.get("xsec_token", "")
        note_url = f"https://www.xiaohongshu.com/explore/{note_id}?xsec_token={xsec}"
        success, msg, note_detail = api.get_note_info(note_url, cookies_str)

        if not success or not note_detail:
            print(f"  ⚠️ 获取详情失败: {msg}")
            note_data = normalize_note_info(note_info)
        else:
            try:
                items = note_detail.get('data', {}).get('items', [])
                if items:
                    item = items[0]
                    item['url'] = note_url
                    note_data = handle_note_info(item)
                else:
                    print(f"  ⚠️ 详情数据为空")
                    note_data = normalize_note_info(note_info)
            except Exception as e:
                print(f"  ⚠️ 解析详情失败: {str(e)}")
                note_data = normalize_note_info(note_info)

        # 获取评论
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

        # 转换为蒸馏器格式
        distiller_note = convert_note_to_distiller_format(note_data, comments_raw)
        details.append(distiller_note)

        # 输出进度
        interact = note_data.get("interact_info", note_data)
        likes = str(interact.get("liked_count", interact.get("likes", "0")))
        collects = str(interact.get("collected_count", interact.get("collects", "0")))
        comments = str(interact.get("comment_count", interact.get("comments", "0")))
        print(f"  ✅ [{title[:30]}...] 赞:{likes} 藏:{collects} 评:{comments}")

    # 获取博主信息
    print("\n📝 获取博主信息...")
    success_u, msg_u, user_info = api.get_user_info(user_id, cookies_str)

    blogger_nickname = nickname
    blogger_desc = ""
    blogger_avatar = ""
    blogger_followers = "0"
    if success_u and user_info and user_info.get('data', {}).get('basic_info'):
        basic = user_info['data']['basic_info']
        if not blogger_nickname:
            blogger_nickname = basic.get('nickname', '')
        blogger_desc = basic.get('desc', '')
        blogger_avatar = basic.get('imageb', '')
        interactions = user_info['data'].get('interactions', [])
        if len(interactions) > 1:
            blogger_followers = str(interactions[1].get('count', '0'))

    final_result = {
        "blogger": {
            "bloggerId": user_id,
            "nickname": blogger_nickname,
            "desc": blogger_desc,
            "avatar": blogger_avatar,
            "verified": False,
            "followerCount": blogger_followers,
            "noteCount": str(len(all_notes)),
        },
        "details": details,
        "_meta": {
            "source": "spider_xhs",
            "total_notes": len(all_notes),
            "collected_notes": len(details),
            "fetch_comments": fetch_comments,
        },
    }

    # 生成安全文件名
    safe_name = re.sub(r'[\\/:*?"<>|]', "_", final_result["blogger"]["nickname"] or user_id)
    safe_name = safe_name.strip() or user_id

    abs_output_dir = os.path.abspath(output_dir)
    os.makedirs(abs_output_dir, exist_ok=True)
    details_path = os.path.join(abs_output_dir, f"{safe_name}_notes_details.json")
    with open(details_path, "w", encoding="utf-8") as f:
        json.dump(final_result, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"🎉 采集完成!")
    print(f"   博主: {final_result['blogger']['nickname'] or user_id}")
    print(f"   有效: {len(details)}/{len(all_notes)} 条")
    print(f"   输出: {details_path}")
    print(f"{'='*60}")

    return details_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spider_XHS 适配器 — 采集并转换为蒸馏器格式")
    parser.add_argument("--user-id", help="小红书用户ID（20位十六进制字符）")
    parser.add_argument("--url", help="小红书用户主页URL（会自动提取用户ID）")
    parser.add_argument("--self", action="store_true", help="采集当前登录账号")
    parser.add_argument("--xsec-token", default="", help="xsec_token（从用户主页URL获取）")
    parser.add_argument("--max-notes", type=int, default=30, help="最大采集条数（默认30）")
    parser.add_argument("--output", "-o", default="./data", help="输出目录")
    parser.add_argument("--no-comments", action="store_true", help="跳过评论采集（加快速度）")
    args = parser.parse_args()

    # 确定用户ID
    user_id = None
    nickname = ""
    
    if args.self:
        # 采集自己的账号
        print("🔍 正在获取当前登录账号信息...")
        self_info, error = get_self_user_info()
        if self_info and self_info.get('user_id'):
            user_id = self_info['user_id']
            nickname = self_info['nickname']
            print(f"✅ 当前登录账号: {nickname} (ID: {user_id})")
            print(f"   笔记数: {self_info['notes_count']} | 粉丝: {self_info['fans']}")
        else:
            # 非交互模式（如被 app.py 子进程调用）或无法获取时，退出并给提示
            print(f"⚠️ 无法自动获取账号信息: {error}")
            print("   请使用 --url 参数提供你的小红书主页链接")
            print("   例如: --url \"https://www.xiaohongshu.com/user/profile/YOUR_USER_ID\"")
            sys.exit(1)
    elif args.url:
        # 从URL提取用户ID
        user_id = extract_user_id_from_url(args.url)
        if user_id:
            print(f"✅ 从URL提取用户ID: {user_id}")
        else:
            print(f"❌ 无法从URL提取用户ID: {args.url}")
            sys.exit(1)
    elif args.user_id:
        # 直接使用提供的用户ID
        user_id = args.user_id
    else:
        print("❌ 请提供 --user-id、--url 或 --self 参数")
        parser.print_help()
        sys.exit(1)

    # 验证用户ID格式
    valid, msg = validate_user_id(user_id)
    if not valid:
        print(f"❌ {msg}")
        sys.exit(1)
    
    print(f"✅ 用户ID格式验证通过: {user_id}")

    # 运行采集
    result = crawl_and_convert(
        user_id=user_id,
        max_notes=args.max_notes,
        output_dir=args.output,
        xsec_token=args.xsec_token,
        fetch_comments=not args.no_comments,
        nickname=nickname,
    )
