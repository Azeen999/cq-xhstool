from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.common_util import load_env
import json

api = XHS_Apis()
c = load_env()

print('=== 测试主页推荐 (可能包含自己的笔记) ===')
ok, msg, data = api.get_homefeed_recommend_by_num('recommend', 30, c)
print(f'ok={ok}, msg={msg}, type={type(data)}')
if isinstance(data, list):
    print(f'list count: {len(data)}')
    for item in data[:5]:
        note_card = item.get('note_card', {})
        if note_card:
            print(f"  - {note_card.get('display_title', 'N/A')[:30]} | ID: {note_card.get('id', 'N/A')}")
elif isinstance(data, dict) and data.get('data'):
    items = data['data'].get('items', [])
    print(f'items count: {len(items)}')
