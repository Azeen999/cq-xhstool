from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.common_util import load_env
import json

api = XHS_Apis()
c = load_env()
ok, msg, data = api.get_user_note_info(
    '694cf4f0000000003700bd56', '', c,
    'ABmsdY9K7t9EXYxcIc7ELPLrSQImP_6--MS9E82CnaD6s=', 'pc_search'
)
print(f'ok={ok}, msg={msg}')
d = data.get('data') if data else None
print(f'data is None: {d is None}')
if d:
    notes = d.get('notes', [])
    print(f'notes count: {len(notes)}')
    if notes:
        print(f'first note: {json.dumps(notes[0], ensure_ascii=False)[:200]}')
