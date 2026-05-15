#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书博主爬虫模块
使用本地爬虫获取博主笔记数据
"""
import subprocess

_original_popen_init = subprocess.Popen.__init__

def _patched_popen_init(self, *args, **kwargs):
    if kwargs.get('universal_newlines') or kwargs.get('text'):
        kwargs.setdefault('encoding', 'utf-8')
    return _original_popen_init(self, *args, **kwargs)

subprocess.Popen.__init__ = _patched_popen_init

import os
import sys
import random
import time
from pathlib import Path

# 添加爬虫路径（指向共享 Spider_XHS）
_SPIDER_DIR = str((Path(__file__).parent.parent.parent / '博主蒸馏' / 'spider_xhs').resolve())
sys.path.append(_SPIDER_DIR)
os.environ.setdefault("SPIDER_XHS_DIR", _SPIDER_DIR)

from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.common_util import load_env
from xhs_utils.data_util import handle_note_info

def random_delay(min_delay=3, max_delay=8):
    """随机延迟（测试用，生产环境建议15-30秒）"""
    delay = random.uniform(min_delay, max_delay)
    print(f"  [DELAY] {delay:.1f}s")
    time.sleep(delay)

def save_note(note_info, index, save_dir):
    """保存单篇笔记"""
    title = note_info.get('title', f'笔记_{index}')
    # 清理标题中的非法字符
    title = ''.join(c for c in title if c.isalnum() or c in (' ', '-', '_', '。', '！', '？')).strip()
    if not title:
        title = f'笔记_{index}'
    
    note_dir = save_dir / f'{index:02d}_{title[:50]}'
    note_dir.mkdir(exist_ok=True)

    # 保存正文
    with open(note_dir / '正文.txt', 'w', encoding='utf-8') as f:
        f.write(f"标题：{note_info.get('title', '')}\n")
        f.write(f"点赞：{note_info.get('liked_count', '')}\n")
        f.write(f"收藏：{note_info.get('collected_count', '')}\n")
        f.write(f"评论：{note_info.get('comment_count', '')}\n")
        f.write(f"时间：{note_info.get('upload_time', '')}\n")
        f.write(f"链接：{note_info.get('note_url', '')}\n")
        f.write(f"IP属地：{note_info.get('ip_location', '')}\n")
        f.write("\n" + "="*50 + "\n\n")
        f.write(note_info.get('desc', ''))

    # 保存图片列表
    image_list = note_info.get('image_list', [])
    if image_list:
        with open(note_dir / '图片列表.txt', 'w', encoding='utf-8') as f:
            for i, url in enumerate(image_list):
                f.write(f"图片{i+1}: {url}\n")

    print(f"  [SAVED] {note_dir.name}")
    return note_info

def crawl_blogger_notes(url=None, name=None, max_notes=50, output_dir=None):
    """
    爬取博主笔记
    
    Args:
        url: 博主主页链接
        name: 博主名（备用）
        max_notes: 最大采集数量
        output_dir: 输出目录
    
    Returns:
        笔记列表
    """
    print(f"📤 开始采集博主数据")
    
    # 将输出目录转换为绝对路径（因为后续会切换目录）
    if output_dir:
        output_dir = output_dir.resolve()
    
    # 保存当前目录，后续切换到 Spider_XHS 目录（因为 execjs 需要在有 node_modules 的目录运行）
    original_cwd = os.getcwd()
    spider_dir = _SPIDER_DIR
    
    try:
        # 切换到 Spider_XHS 目录
        os.chdir(spider_dir)
        
        # 加载 Cookie
        cookies_str = load_env()
        if not cookies_str:
            print(f"[ERROR] Cookie 为空，请检查 {os.path.join(_SPIDER_DIR, '.env')}")
            return []

        api = XHS_Apis()
        all_notes = []

        if url:
            # 直接使用链接
            print(f"🔗 使用博主链接: {url}")
            success, msg, notes_data = api.get_user_all_notes(url, cookies_str)
            if not success:
                print(f"[ERROR] 获取笔记列表失败: {msg}")
                return []
            
            print(f"📊 发现 {len(notes_data)} 篇笔记")
            
            # 采集详情
            for i, note in enumerate(notes_data[:max_notes]):
                note_url = f"https://www.xiaohongshu.com/explore/{note['note_id']}?xsec_token={note['xsec_token']}"
                print(f"[{i+1}/{max_notes}] {note_url}")
                
                random_delay()
                
                ok, msg, data = api.get_note_info(note_url, cookies_str)
                if ok and data:
                    try:
                        item = data['data']['items'][0]
                        item['url'] = note_url
                        info = handle_note_info(item)
                        info['note_url'] = note_url
                        info['title'] = note.get('title', '')
                        info['liked_count'] = note.get('liked_count', 0)
                        info['collected_count'] = note.get('collected_count', 0)
                        info['comment_count'] = note.get('comment_count', 0)
                        
                        if output_dir:
                            save_note(info, i+1, output_dir)
                        all_notes.append(info)
                    except Exception as e:
                        print(f"  [WARN] 解析失败: {e}")
                else:
                    print(f"  [FAIL] {msg}")
    
        elif name:
            # 通过博主名搜索（需要实现搜索功能）
            print(f"🔍 搜索博主: {name}")
            # 这里可以扩展搜索功能
            print("[WARN] 通过博主名搜索功能尚未实现，请提供博主主页链接")
            return []
        
        print(f"✅ 采集完成，共 {len(all_notes)} 篇")
        return all_notes
        
    finally:
        # 恢复原目录
        os.chdir(original_cwd)

if __name__ == '__main__':
    # 测试
    test_url = "https://www.xiaohongshu.com/user/profile/61ade68500000000210253b6"
    crawl_blogger_notes(url=test_url, max_notes=5, output_dir=Path('./test_output'))