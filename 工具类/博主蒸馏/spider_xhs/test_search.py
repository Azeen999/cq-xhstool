from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.common_util import load_env
import json

api = XHS_Apis()
c = load_env()

# 搜索你的小红书号
print('=== 搜索用户 zhanxialing123 ===')
ok, msg, data = api.get_search_keyword('zhanxialing123', c)
print(f'ok={ok}, msg={msg}')
if data:
    print(json.dumps(data, ensure_ascii=False, indent=2)[:2000])
