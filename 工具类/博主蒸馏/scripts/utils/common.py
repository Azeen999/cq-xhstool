"""通用工具函数"""

import re
import subprocess


def patch_subprocess_utf8():
    """Monkey-patch subprocess.Popen 强制 UTF-8，防止 execjs 在 GBK 系统上崩溃。
    安全可重复调用（幂等）。
    """
    if getattr(subprocess.Popen, '_utf8_patched', False):
        return
    _original = subprocess.Popen.__init__
    def _patched(self, *args, **kwargs):
        if kwargs.get('universal_newlines') or kwargs.get('text'):
            kwargs.setdefault('encoding', 'utf-8')
            kwargs.setdefault('errors', 'replace')
        return _original(self, *args, **kwargs)
    subprocess.Popen.__init__ = _patched
    subprocess.Popen._utf8_patched = True


def parse_count(s):
    """解析 '1.2万' / '1,234' / '12' 等格式为整数"""
    if not s:
        return 0
    s = str(s).strip().replace(",", "")
    if not s:
        return 0
    try:
        if "万" in s:
            return int(float(s.replace("万", "")) * 10000)
        return int(s)
    except (ValueError, TypeError):
        return 0


def safe_filename(name):
    """将字符串转为安全文件名"""
    return re.sub(r'[\\/:*?"<>|]', "_", name).strip()


# ============================================================
# 平台注册表
# ============================================================

PLATFORM_REGISTRY = {
    "xhs": {
        "name": "小红书",
        "name_en": "Xiaohongshu",
        "content_unit": "笔记",
        "user_id_label": "用户ID",
        "note_id_label": "笔记ID",
        "default_deep_analysis": True,
    },
}

SUPPORTED_PLATFORMS = list(PLATFORM_REGISTRY.keys())

CATEGORY_MAP = {
    "general": "通用",
    "food": "美食",
    "fitness": "健身",
    "travel": "旅行",
    "fashion": "时尚",
    "beauty": "护肤",
    "digital": "数码",
    "home": "家居",
    "parenting": "育儿",
    "pet": "宠物",
    "emotion": "情感",
    "tech": "科技",
    "art": "艺术",
    "sport": "运动",
    "car": "汽车",
    "education": "教育",
    "finance": "财经",
    "game": "游戏",
    "knowledge": "知识",
    "comic": "动漫",
    "music": "音乐",
    "fun": "搞笑",
}


def get_platform_config(platform: str) -> dict:
    """
    获取平台配置，平台名不区分大小写。

    Args:
        platform: 平台标识（"xhs" 或 "douyin"）

    Returns:
        平台配置 dict

    Raises:
        ValueError: 不支持的平台
    """
    key = platform.lower().strip()
    if key not in PLATFORM_REGISTRY:
        supported = ", ".join(SUPPORTED_PLATFORMS)
        raise ValueError(f"不支持的平台: '{platform}'，当前支持: {supported}")
    return PLATFORM_REGISTRY[key]
