from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.common_util import load_env
import json

api = XHS_Apis()
c = load_env()

# 新的 xsec_token
new_token = 'ABmsdY9K7t9EXYxcIc7ELPLtswU36kaDild0SH-zI7Dc4='
user_id = '694cf4f0000000003700bd56'

print('=== 测试新 token 获取笔记列表 ===')
ok, msg, data = api.get_user_note_info(user_id, '', c, new_token, 'pc_search')
print(f'ok={ok}, msg={msg}')
if data:
    d = data.get('data')
    if d:
        notes = d.get('notes', [])
        print(f'[OK] 成功！笔记数量: {len(notes)}')
        if notes:
            print(f'第一篇标题: {notes[0].get("display_title", "")}')
    else:
        print(f'[FAIL] data 为 None')
        print(json.dumps(data, ensure_ascii=False, indent=2)[:500])
