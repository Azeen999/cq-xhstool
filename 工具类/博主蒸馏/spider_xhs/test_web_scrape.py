import requests
import re
import json
from xhs_utils.common_util import load_env

cookies_str = load_env()

# 解析 cookie 字符串为字典
cookies = {}
for item in cookies_str.split(';'):
    if '=' in item:
        key, value = item.strip().split('=', 1)
        cookies[key] = value

url = 'https://www.xiaohongshu.com/user/profile/694cf4f4000000003700bd56'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

print(f'Fetching {url}...')
resp = requests.get(url, headers=headers, cookies=cookies, allow_redirects=True)
print(f'Status: {resp.status_code}')
print(f'URL after redirect: {resp.url}')

# 尝试从 HTML 中提取笔记数据
# 小红书通常把数据放在 <script>window.__INITIAL_STATE__ = {...}</script> 中
match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.+?});', resp.text)
if match:
    try:
        data = json.loads(match.group(1))
        print(f'Found __INITIAL_STATE__, keys: {list(data.keys())[:10]}')
        # 尝试找到笔记数据
        if 'user' in data:
            user_data = data['user']
            print(f'User data keys: {list(user_data.keys())[:10]}')
            if 'notes' in user_data:
                notes = user_data['notes']
                print(f'Found {len(notes)} notes')
    except Exception as e:
        print(f'Parse error: {e}')
else:
    print('No __INITIAL_STATE__ found')
    # 尝试其他模式
    note_pattern = r'"noteId":"(\d+)"'
    note_ids = re.findall(note_pattern, resp.text)
    print(f'Found note IDs: {note_ids[:10]}')
