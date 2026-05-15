from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.common_util import load_env
import json

api = XHS_Apis()
c = load_env()

print('=== 获取自己的账号信息 ===')
ok, msg, data = api.get_user_self_info(c)
if ok and data:
    user_data = data.get('data', {}).get('result', {})
    print(f"✅ 昵称: {user_data.get('nickname', '')}")
    print(f"✅ 用户ID: {user_data.get('user_id', '')}")
    print(f"✅ 小红书号: {user_data.get('red_id', '')}")
    print(f"✅ 粉丝: {user_data.get('fans', 'N/A')}")
    print(f"✅ 笔记数: {user_data.get('notes_count', 0)}")
else:
    print(f"❌ 获取失败: {msg}")
    print(f"data: {json.dumps(data, ensure_ascii=False)[:300] if data else 'None'}")
