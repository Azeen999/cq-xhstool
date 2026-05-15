from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.common_util import load_env
import json

api = XHS_Apis()
c = load_env()

# Test 1: get self info
print('=== get_user_selfinfo ===')
ok, msg, data = api.get_user_self_info(c)
print(f'ok={ok}, msg={msg}')
if data:
    print(json.dumps(data, ensure_ascii=False, indent=2)[:500])

# Test 2: get user info (other)
print('\n=== get_user_info (other) ===')
ok2, msg2, data2 = api.get_user_info('694cf4f0000000003700bd56', c)
print(f'ok={ok2}, msg={msg2}')
if data2:
    print(json.dumps(data2, ensure_ascii=False, indent=2)[:500])

# Test 3: get user notes (no xsec_token)
print('\n=== get_user_note_info (no xsec_token) ===')
ok3, msg3, data3 = api.get_user_note_info('694cf4f0000000003700bd56', '', c, '', 'pc_search')
print(f'ok={ok3}, msg={msg3}')
if data3:
    d3 = data3.get('data')
    if d3:
        notes = d3.get('notes', [])
        print(f'notes count: {len(notes)}')
        if notes:
            print(f'first note title: {notes[0].get("display_title", "")}')
    else:
        print(f'data is None, raw: {json.dumps(data3, ensure_ascii=False)[:300]}')
