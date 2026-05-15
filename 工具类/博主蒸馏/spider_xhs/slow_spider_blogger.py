"""
慢速爬取博主笔记（防封版）
间隔：20-40秒（随机）
"""
import os, sys, time, random

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.common_util import load_env
from xhs_utils.data_util import handle_note_info

# 配置
USER_ID = '61ade68500000000210253b6'
USER_URL = f'https://www.xiaohongshu.com/user/profile/{USER_ID}'
SAVE_DIR = rf'D:\myproj\参考\{USER_ID}_笔记'
MAX_NOTES = 20
MIN_DELAY = 15
MAX_DELAY = 30

def random_delay():
    delay = random.uniform(MIN_DELAY, MAX_DELAY)
    print(f"  [DELAY] waiting {delay:.1f}s...")
    time.sleep(delay)

def save_note(note_info, index, save_dir):
    title = ''.join(c for c in note_info.get('title', f'笔记_{index}')
                    if c.isalnum() or c in (' ', '-', '_')).strip()
    if not title:
        title = f'笔记_{index}'
    note_dir = os.path.join(save_dir, f'{index:02d}_{title}')
    os.makedirs(note_dir, exist_ok=True)

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
            for i, url in enumerate(image_list):
                f.write(f"图片{i+1}: {url}\n")

    print(f"  [SAVED] {note_dir}")
    return note_dir

def main():
    print("="*60)
    print(f"[START] 采集博主笔记: {USER_ID}")
    print(f"[DELAY] 间隔: {MIN_DELAY}-{MAX_DELAY}秒/篇")
    print(f"[COUNT] 目标: {MAX_NOTES}篇")
    print("="*60)

    os.makedirs(SAVE_DIR, exist_ok=True)

    cookies_str = load_env()
    if not cookies_str:
        print("[ERROR] Cookie为空，请检查 D:\\myproj\\Spider_XHS\\.env")
        return

    api = XHS_Apis()
    print(f"\n[GET] 获取笔记列表...")
    random_delay()

    success, msg, all_notes = api.get_user_all_notes(USER_URL, cookies_str)
    if not success:
        print(f"[ERROR] 获取失败: {msg}")
        return

    print(f"[INFO] 共 {len(all_notes)} 篇笔记，采集前 {min(MAX_NOTES, len(all_notes))} 篇\n")

    saved = 0
    for i, note in enumerate(all_notes[:MAX_NOTES]):
        note_url = f"https://www.xiaohongshu.com/explore/{note['note_id']}?xsec_token={note['xsec_token']}"
        print(f"[{i+1}/{MAX_NOTES}] {note_url}")
        random_delay()

        ok, msg, data = api.get_note_info(note_url, cookies_str)
        if ok and data:
            try:
                item = data['data']['items'][0]
                item['url'] = note_url
                info = handle_note_info(item)
                info['note_url'] = note_url
                save_note(info, i+1, SAVE_DIR)
                saved += 1
            except Exception as e:
                print(f"  [WARN] {e}")
        else:
            print(f"  [FAIL] {msg}")
        print()

    print("="*60)
    print(f"[DONE] 成功 {saved}/{MAX_NOTES} 篇")
    print(f"[DIR] {SAVE_DIR}")
    print("="*60)

if __name__ == '__main__':
    main()