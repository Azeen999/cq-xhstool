import requests
import json
from xhs_utils.common_util import load_env
from apis.xhs_pc_apis import generate_request_params, splice_str

cookies_str = load_env()

# 尝试用 API 直接获取用户笔记
api = "/api/sns/web/v1/user_posted"
params = {
    "num": "30",
    "cursor": "",
    "user_id": "694cf4f4000000003700bd56",
    "image_formats": "jpg,webp,avif",
}

splice_api = splice_str(api, params)
headers, cookies, data = generate_request_params(cookies_str, splice_api, '', 'GET')

base_url = "https://edith.xiaohongshu.com"
url = base_url + splice_api

print(f'Requesting: {url}')
resp = requests.get(url, headers=headers, cookies=cookies)
print(f'Status: {resp.status_code}')
result = resp.json()
print(f'Response: {json.dumps(result, ensure_ascii=False, indent=2)[:1000]}')
