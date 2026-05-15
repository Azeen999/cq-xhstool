"""
慢速爬取 SomeFries 的前20篇笔记
请求间隔：15-30秒（随机），避免被封
"""
import os
import sys
import time
import random
from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.common_util import load_env
from xhs_utils.data_util import handle_note_info

# 配置
USER_ID = '54701b42d6e4a942975b8059'
USER_URL = f'https://www.xiaohongshu.com/user/profile/{USER_ID}'
SAVE_DIR = r'D:\myproj\参考\SomeFries_笔记'
MAX_NOTES = 5
MIN_DELAY = 15
MAX_DELAY = 30

def random_delay():
    delay = random.uniform(MIN_DELAY, MAX_DELAY)
    print(f"  [DELAY] waiting {delay:.1f} seconds...")
    time.sleep(delay)

def save_note_content(note_info, index, save_dir):
    title = note_info.get('title', f'笔记_{index}')
    title = ''.join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
    if not title:
        title = f'笔记_{index}'

    note_dir = os.path.join(save_dir, f'{index:02d}_{title}')
    os.makedirs(note_dir, exist_ok=True)

    # handle_note_info returns: note_url, liked_count, collected_count, comment_count, share_count, title, desc, image_list, etc.
    with open(os.path.join(note_dir, '正文.txt'), 'w', encoding='utf-8') as f:
        f.write(f"标题：{note_info.get('title', '')}\n")
        f.write(f"点赞：{note_info.get('liked_count', '')}\n")
        f.write(f"收藏：{note_info.get('collected_count', '')}\n")
        f.write(f"评论：{note_info.get('comment_count', '')}\n")
        f.write(f"时间：{note_info.get('upload_time', '')}\n")
        f.write(f"链接：{note_info.get('note_url', '')}\n")
        f.write(f"IP属地：{note_info.get('ip_location', '')}\n")
        f.write("\n" + "="*50 + "\n\n")
        f.write(note_info.get('desc', ''))

    image_list = note_info.get('image_list', [])
    if image_list:
        with open(os.path.join(note_dir, '图片列表.txt'), 'w', encoding='utf-8') as f:
            for i, img_url in enumerate(image_list):
                f.write(f"图片{i+1}: {img_url}\n")

    print(f"  [SAVED] {note_dir}")
    return note_dir

def main():
    print("="*60)
    print("[START] Starting slow crawl for SomeFries notes")
    print(f"[DIR] Save directory: {SAVE_DIR}")
    print(f"[DELAY] Request interval: {MIN_DELAY}-{MAX_DELAY} seconds")
    print(f"[COUNT] Target: {MAX_NOTES} notes")
    print("="*60)

    os.makedirs(SAVE_DIR, exist_ok=True)

    cookies_str = load_env()
    if not cookies_str:
        print("[ERROR] Cookie is empty")
        return

    api = XHS_Apis()

    print(f"\n[GET] Fetching user notes list...")
    random_delay()

    success, msg, all_notes = api.get_user_all_notes(USER_URL, cookies_str)
    if not success:
        print(f"[ERROR] Failed to get notes list: {msg}")
        return

    print(f"[INFO] User has {len(all_notes)} notes total, will crawl first {min(MAX_NOTES, len(all_notes))}\n")

    saved_count = 0
    for i, note in enumerate(all_notes[:MAX_NOTES]):
        note_id = note.get('note_id', '')
        xsec_token = note.get('xsec_token', '')
        note_url = f"https://www.xiaohongshu.com/explore/{note_id}?xsec_token={xsec_token}"

        print(f"[{i+1}/{MAX_NOTES}] Crawling note...")
        print(f"  [URL] {note_url}")

        random_delay()

        success, msg, note_data = api.get_note_info(note_url, cookies_str)
        if success and note_data:
            try:
                item = note_data['data']['items'][0]
                item['url'] = note_url
                note_info = handle_note_info(item)
                note_info['note_url'] = note_url
                save_note_content(note_info, i+1, SAVE_DIR)
                saved_count += 1
            except Exception as e:
                print(f"  [WARN] Parse failed: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"  [FAIL] Fetch failed: {msg}")

        print()

    print("="*60)
    print(f"[DONE] Successfully saved {saved_count}/{MAX_NOTES} notes")
    print(f"[DIR] Save location: {SAVE_DIR}")
    print("="*60)

if __name__ == '__main__':
    main()