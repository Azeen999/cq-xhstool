"""
小红书工具箱 — 便携版打包脚本
生成含 Python + Node.js 运行时的完整 ZIP，用户解压即用

用法：
    python build_portable.py
"""

import os
import sys
import shutil
import zipfile
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PKG_NAME = "小红书工具箱"
BUILD_DIR = ROOT / "build_portable"
DIST_DIR = BUILD_DIR / PKG_NAME
ZIP_PATH = ROOT / "dist_package" / f"{PKG_NAME}-便携版.zip"

# 便携版运行时来源
RUNTIME_SRC = ROOT / "dist_temp" / "runtime"

# 需要排除的文件/目录
EXCLUDE_DIRS = {
    "__pycache__", ".git", ".vscode", ".idea", "node_modules",
    "output", "dist_package", "dist_temp", "build_portable",
    ".trae-cn", "__pycache__",
}

EXCLUDE_FILES = {
    ".env", "pack.py", "build_portable.py", "startup.log",
    ".rag_index.pkl",
}

EXCLUDE_SUFFIXES = {".pyc", ".db", ".log"}

EXCLUDE_PATTERNS = {
    "package-lock.json",
    "test_api.py", "test_api2.py", "test_homefeed.py",
    "test_new_cookie.py", "test_new_token.py", "test_note_api.py",
    "test_search.py", "test_selfinfo.py", "test_user_page.py",
    "test_web_scrape.py", "slow_spider_blogger.py", "slow_spider_somefries.py",
}


def should_exclude(name: str, rel_path: str) -> bool:
    parts = Path(rel_path).parts
    if any(p in EXCLUDE_DIRS for p in parts):
        return True
    if name in EXCLUDE_FILES or name in EXCLUDE_PATTERNS:
        return True
    if any(name.endswith(s) for s in EXCLUDE_SUFFIXES):
        return True
    return False


def _get_env_path(dist_dir: Path) -> Path:
    """app.py 读取 .env 的实际路径"""
    return dist_dir / "工具类" / "博主蒸馏" / "spider_xhs" / ".env"


def create_start_bat(dist_dir: Path):
    """创建 start.bat，设置 PATH 后启动"""
    env_path = _get_env_path(dist_dir)
    env_rel = env_path.relative_to(dist_dir).as_posix().replace("/", "\\")

    content = r"""@echo off
cd /d "%~dp0"

:: Add runtime directory to PATH (for node.exe)
set "PATH=%CD%\runtime;%PATH%"

:: Check .env exists
if not exist "__ENV_REL__" (
    echo.
    echo  ==========================================
    echo   [重要] 首次使用请先配置 Cookie！
    echo  ==========================================
    echo.
    echo  请运行 setup.bat 完成初始化配置。
    echo.
    pause
    start setup.bat
    exit /b 1
)

echo.
echo  ==========================================
echo    小红书工具箱 - 启动中...
echo  ==========================================
echo.
echo  浏览器打开后，如果未自动跳转请访问：
echo  http://localhost:5001
echo.

runtime\python.exe app.py

if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] 启动失败！
    echo  请截图本窗口并反馈。
    echo.
    pause
)
"""
    content = content.replace("__ENV_REL__", env_rel)
    bat_path = dist_dir / "start.bat"
    bat_path.write_text(content, encoding="utf-8")


def create_setup_bat(dist_dir: Path):
    """创建 setup.bat（首次运行检查 Cookie）"""
    env_path = _get_env_path(dist_dir)
    env_rel = env_path.relative_to(dist_dir).as_posix().replace("/", "\\")

    content = r"""@echo off
cd /d "%~dp0"

echo.
echo  ==========================================
echo    小红书工具箱 - 首次运行检查
echo  ==========================================
echo.

:: Check .env exists in spider_xhs directory
if not exist "__ENV_REL__" (
    echo  [INFO] 未检测到 .env 配置文件
    echo.
    if exist "__ENV_EXAMPLE__" (
        copy "__ENV_EXAMPLE__" "__ENV_REL__" >nul
        echo  [OK] 已从模板创建 .env 文件
        echo.
    ) else (
        echo  [WARN] 模板文件不存在，请手动创建
        echo.
    )
)

:: Check if cookie is configured
findstr /C:"your_cookie_here" "__ENV_REL__" >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo  ==========================================
    echo   [重要] Cookie 未配置！
    echo  ==========================================
    echo.
    echo  请编辑以下文件，填入你小红书账号的 Cookie：
    echo  __ENV_REL__
    echo.
    echo  获取方法：
    echo  1. 用浏览器打开 https://www.xiaohongshu.com 并登录
    echo  2. 按 F12 打开开发者工具
    echo  3. 切换到 Network（网络）标签
    echo  4. 刷新页面
    echo  5. 点击任意请求，复制 Cookie 值
    echo  6. 粘贴到 .env 文件中
    echo.
    pause
    notepad "__ENV_REL__"
) else (
    echo.
    echo  [OK] Cookie 已配置，可以启动
    echo.
    echo  双击 start.bat 即可使用
    echo.
    pause
)
"""
    content = content.replace("__ENV_REL__", env_rel)
    env_example_rel = Path("工具类") / "博主蒸馏" / "spider_xhs" / ".env.example"
    content = content.replace("__ENV_EXAMPLE__", env_example_rel.as_posix().replace("/", "\\"))
    bat_path = dist_dir / "setup.bat"
    bat_path.write_text(content, encoding="utf-8")


def convert_bat_to_gbk(dist_dir: Path):
    """将 .bat 文件转为 GBK 编码（Windows CMD 兼容）"""
    for bat_file in dist_dir.rglob("*.bat"):
        try:
            content = bat_file.read_text(encoding="utf-8")
            bat_file.write_text(content, encoding="gbk", errors="replace")
        except Exception:
            pass


def main():
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    print()
    print("  ╔══════════════════════════════════════════╗")
    print("  ║   小红书工具箱 - 便携版打包              ║")
    print("  ╚══════════════════════════════════════════╝")
    print()

    # ── 检查运行时是否存在 ──
    if not RUNTIME_SRC.exists():
        print(f"  [ERROR] 运行时目录不存在: {RUNTIME_SRC}")
        print(f"  请先运行 python build_runtime.py 或手动下载 Python 嵌入版")
        sys.exit(1)

    python_exe = RUNTIME_SRC / "python.exe"
    node_exe = RUNTIME_SRC / "node.exe"
    if not python_exe.exists():
        print(f"  [ERROR] {python_exe} 不存在")
        sys.exit(1)

    print(f"  Python: {python_exe}")
    print(f"  Node:   {'✅' if node_exe.exists() else '❌ 未找到'}")
    print()

    # ── 清理构建目录 ──
    if DIST_DIR.exists():
        print("  清理旧构建目录...")
        shutil.rmtree(DIST_DIR, ignore_errors=True)
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    DIST_DIR.mkdir(parents=True, exist_ok=True)

    # ── 复制运行时 ──
    print("  复制运行时 (Python + Node.js)...")
    runtime_dst = DIST_DIR / "runtime"
    shutil.copytree(RUNTIME_SRC, runtime_dst, symlinks=False, dirs_exist_ok=True)
    runtime_size = sum(f.stat().st_size for f in runtime_dst.rglob("*") if f.is_file())
    print(f"  ✅ 运行时: {runtime_size / 1024 / 1024:.0f} MB")

    # ── 复制 node_modules ──
    nm_src = ROOT / "工具类" / "博主蒸馏" / "spider_xhs" / "node_modules"
    if nm_src.exists():
        print("  复制 node_modules...")
        nm_dst = DIST_DIR / "工具类" / "博主蒸馏" / "spider_xhs" / "node_modules"
        shutil.copytree(nm_src, nm_dst, symlinks=False)
        nm_size = sum(f.stat().st_size for f in nm_dst.rglob("*") if f.is_file())
        print(f"  ✅ node_modules: {nm_size / 1024 / 1024:.0f} MB")

    # ── 复制源文件 ──
    print("  复制源文件...")
    file_count = 0
    for root, dirs, files in os.walk(ROOT):
        # 跳过排除目录
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        rel_root = os.path.relpath(root, ROOT)
        if rel_root == ".":
            rel_root = ""

        for f in files:
            rel_path = os.path.join(rel_root, f) if rel_root else f
            if should_exclude(f, rel_path):
                continue
            src = os.path.join(root, f)
            dst = DIST_DIR / rel_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            file_count += 1
    print(f"  ✅ 源文件: {file_count} 个")

    # ── 清理可能被复制的 .env（防止泄露凭据）──
    env_in_build = DIST_DIR / "工具类" / "博主蒸馏" / "spider_xhs" / ".env"
    if env_in_build.exists():
        env_in_build.unlink()
        print("  🧹 已移除 .env 文件（保护凭据）")

    # ── 创建 spider_xhs 目录的 .env.example ──
    env_example_src = ROOT / ".env.example"
    env_example_dst = DIST_DIR / "工具类" / "博主蒸馏" / "spider_xhs" / ".env.example"
    if env_example_src.exists():
        shutil.copy2(env_example_src, env_example_dst)
        print("  ✅ 已创建 .env.example 模板")

    # ── 创建启动脚本 ──
    print("  创建启动脚本...")
    create_start_bat(DIST_DIR)
    create_setup_bat(DIST_DIR)

    # ── 创建空 output 目录 ──
    (DIST_DIR / "output" / "关键词搜索").mkdir(parents=True, exist_ok=True)
    (DIST_DIR / "output" / "帖子深挖").mkdir(parents=True, exist_ok=True)
    (DIST_DIR / "output" / "博主分析").mkdir(parents=True, exist_ok=True)
    (DIST_DIR / "输出").mkdir(parents=True, exist_ok=True)

    # ── 转换 .bat 为 GBK ──
    print("  转换 .bat 编码...")
    convert_bat_to_gbk(DIST_DIR)

    # ── 打包 ZIP ──
    print("  打包 ZIP...")
    ZIP_PATH.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(DIST_DIR):
            for f in files:
                full = os.path.join(root, f)
                arc = os.path.relpath(full, DIST_DIR)
                zf.write(full, arc)

    zip_size = ZIP_PATH.stat().st_size / (1024 * 1024)
    total_size = sum(f.stat().st_size for f in DIST_DIR.rglob("*") if f.is_file()) / (1024 * 1024)

    print()
    print("  ╔══════════════════════════════════════════╗")
    print("  ║          ✅ 打包完成！                    ║")
    print("  ╠══════════════════════════════════════════╣")
    print(f"  ║  ZIP: {ZIP_PATH.name}")
    print(f"  ║  大小: {zip_size:.0f} MB (压缩前 {total_size:.0f} MB)")
    print("  ╠══════════════════════════════════════════╣")
    print("  ║  使用方式：                              ║")
    print("  ║  1. 解压 ZIP                             ║")
    print("  ║  2. 编辑 .env 填入 Cookie                ║")
    print("  ║  3. 双击 start.bat                       ║")
    print("  ║  4. 浏览器自动打开 http://localhost:5001  ║")
    print("  ╚══════════════════════════════════════════╝")
    print()


if __name__ == "__main__":
    main()
