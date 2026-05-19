"""
图片缓存代理
缓存小红书 CDN 图片到本地，避免防盗链失效
"""

import os
import hashlib
import requests
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parent / "output" / "image_cache"


def _ensure_cache_dir():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _url_to_filename(url: str) -> str:
    """用 URL 的 MD5 作为缓存文件名"""
    return hashlib.md5(url.encode("utf-8")).hexdigest() + ".jpg"


def get_cached_path(url: str) -> str:
    """获取缓存文件路径（如果已缓存），否则返回 None"""
    fpath = CACHE_DIR / _url_to_filename(url)
    return str(fpath) if fpath.is_file() else ""


def cache_image(url: str) -> str | None:
    """下载并缓存图片，返回缓存路径"""
    _ensure_cache_dir()
    fpath = CACHE_DIR / _url_to_filename(url)
    if fpath.is_file():
        return str(fpath)
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.xiaohongshu.com/",
        })
        resp.raise_for_status()
        fpath.write_bytes(resp.content)
        return str(fpath)
    except Exception:
        return ""
