"""
小红书工具箱 — 打包分发包
生成不含个人数据的干净 ZIP，供内部分发

用法：python pack.py
"""

import os
import sys
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PKG_NAME = "小红书工具箱"
DIST_DIR = ROOT / "dist_package"

EXCLUDE_DIRS = {
    "__pycache__", ".git", ".vscode", ".idea", "node_modules",
    "output", "dist_package", ".trae-cn",
}

EXCLUDE_FILES = {
    ".env", "start_hidden.vbs", "pack.bat", "pack.py", "startup.log",
}

EXCLUDE_SUFFIXES = {".pyc", ".db", ".pkl", ".log"}

EXCLUDE_PATTERNS = {
    "package-lock.json",
    "test_api.py", "test_api2.py", "test_homefeed.py",
    "test_new_cookie.py", "test_new_token.py", "test_note_api.py",
    "test_search.py", "test_selfinfo.py", "test_user_page.py",
    "test_web_scrape.py", "slow_spider_blogger.py", "slow_spider_somefries.py",
}

EXCLUDE_SUBDIRS = {
    "素材库/自我参数/粗趣",
    "素材库/自我参数/粗趣丨蛋仔小助手_笔记",
    "素材库/自我参数/_过程文件",
    "素材库/博主风格",
    "工具类/博主蒸馏/spider_xhs/data",
    "工具类/博主蒸馏/spider_xhs/__pycache__",
    "工具类/博主蒸馏/spider_xhs/node_modules",
    "工具类/博主蒸馏/spider_xhs/.git",
    "工具类/博主蒸馏/data",
    "工具类/博主蒸馏/spider_xhs/工具类",
}

EMPTY_DIRS = [
    "output",
    "素材库/自我参数",
    "素材库/博主风格",
]


def should_exclude(rel_path: str) -> bool:
    parts = Path(rel_path).parts
    if any(p in EXCLUDE_DIRS for p in parts):
        return True
    name = Path(rel_path).name
    if name in EXCLUDE_FILES or name in EXCLUDE_PATTERNS:
        return True
    if any(name.endswith(s) for s in EXCLUDE_SUFFIXES):
        return True
    for sub in EXCLUDE_SUBDIRS:
        if rel_path.replace("\\", "/").startswith(sub.replace("\\", "/")):
            return True
    return False


def main():
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    print()
    print("  ╔══════════════════════════════════════════╗")
    print("  ║   小红书工具箱 - 打包分发包               ║")
    print("  ╚══════════════════════════════════════════╝")
    print()

    if DIST_DIR.exists():
        print("  清理旧的打包目录...")
        shutil.rmtree(DIST_DIR, ignore_errors=True)

    pkg_dir = DIST_DIR / PKG_NAME
    zip_path = DIST_DIR / f"{PKG_NAME}.zip"

    print("  正在复制文件...")
    file_count = 0
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        rel_root = os.path.relpath(root, ROOT)
        for f in files:
            rel_file = os.path.join(rel_root, f) if rel_root != "." else f
            if should_exclude(rel_file):
                continue
            src = os.path.join(root, f)
            dst = pkg_dir / rel_file
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            file_count += 1

    print(f"  ✅ 复制了 {file_count} 个文件")

    print("  转换 .bat 文件为 GBK 编码...")
    bat_files_in_pkg = list(pkg_dir.rglob("*.bat"))
    for bf in bat_files_in_pkg:
        try:
            content = bf.read_text(encoding="utf-8")
            bf.write_text(content, encoding="gbk", errors="replace")
        except Exception:
            try:
                content = bf.read_text(encoding="gbk")
            except Exception:
                pass
    print(f"  ✅ 转换了 {len(bat_files_in_pkg)} 个 .bat 文件")

    print("  创建空目录结构...")
    for d in EMPTY_DIRS:
        (pkg_dir / d).mkdir(parents=True, exist_ok=True)

    print("  正在生成 ZIP...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(pkg_dir):
            for f in files:
                full = os.path.join(root, f)
                arc = os.path.relpath(full, DIST_DIR)
                zf.write(full, arc)

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print()
    print("  ╔══════════════════════════════════════════╗")
    print("  ║          ✅ 打包完成！                    ║")
    print("  ╠══════════════════════════════════════════╣")
    print(f"  ║  文件: {zip_path}")
    print(f"  ║  大小: {size_mb:.1f} MB")
    print("  ╠══════════════════════════════════════════╣")
    print("  ║  分发步骤：                               ║")
    print("  ║  1. 将 ZIP 发给同事                       ║")
    print("  ║  2. 解压到任意目录                        ║")
    print("  ║  3. 双击 setup.bat 安装依赖               ║")
    print("  ║  4. 编辑 .env 填入 Cookie                 ║")
    print("  ║  5. 双击 start.bat 启动                   ║")
    print("  ╚══════════════════════════════════════════╝")
    print()


if __name__ == "__main__":
    main()
