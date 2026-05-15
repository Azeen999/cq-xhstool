"""
bundle_spider.py — 将 Spider_XHS 打包到项目内

从 tools/Spider_XHS 复制到项目根目录的 spider_xhs/（排除 .git / node_modules / __pycache__ / data）。

用法：
    python bundle_spider.py                          # 从默认路径复制
    python bundle_spider.py --source ../tools/Spider_XHS  # 指定源目录
    python bundle_spider.py --dry-run                 # 预览要复制的文件
"""

import os
import sys
import shutil
import argparse

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# 排除的目录/文件模式
EXCLUDE_DIRS = frozenset({".git", "node_modules", "__pycache__", ".github", "data", "author"})
EXCLUDE_FILES = frozenset({".gitignore", "Dockerfile"})


def collect_files(src_root: str) -> list[tuple[str, str]]:
    """收集需要复制的文件，返回 [(源路径, 相对路径)]"""
    files = []
    for dirpath, dirnames, filenames in os.walk(src_root):
        # 排除目录（原地修改 dirnames 阻止 os.walk 进入）
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]

        rel_dir = os.path.relpath(dirpath, src_root)
        for fn in filenames:
            if fn in EXCLUDE_FILES:
                continue
            src = os.path.join(dirpath, fn)
            rel = os.path.join(rel_dir, fn) if rel_dir != "." else fn
            files.append((src, rel))
    return files


def main():
    parser = argparse.ArgumentParser(description="打包 Spider_XHS 到项目")
    parser.add_argument("--source",
                        default=r"D:\myproj\tools\Spider_XHS",
                        help="Spider_XHS 源目录（默认: D:\\myproj\\tools\\Spider_XHS）")
    parser.add_argument("--target",
                        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "spider_xhs"),
                        help="目标目录（默认: 项目根目录的 spider_xhs/）")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不复制")
    args = parser.parse_args()

    src_root = os.path.abspath(args.source)
    if not os.path.isdir(src_root):
        print(f"[ERROR] 源目录不存在: {src_root}")
        sys.exit(1)

    files = collect_files(src_root)
    print(f"[Spider_XHS] 打包")
    print(f"   来源: {src_root}")
    print(f"   目标: {os.path.abspath(args.target)}")
    print(f"   文件: {len(files)} 个")
    print()

    if args.dry_run:
        print("预览（将复制以下文件）：")
        for _, rel in sorted(files):
            print(f"  [+] {rel}")
        print(f"\n共 {len(files)} 个文件")
        return

    # 复制文件
    target_root = os.path.abspath(args.target)
    os.makedirs(target_root, exist_ok=True)

    count = 0
    for src, rel in files:
        dst = os.path.join(target_root, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        try:
            shutil.copy2(src, dst)
            count += 1
        except Exception as e:
            print(f"  [!] 复制失败: {rel} — {e}")

    print(f"\n[OK] 打包完成！共 {count} 个文件复制到 {target_root}")
    print()
    print("注意：node_modules 已排除，需要在目标机上运行：")
    print("  cd spider_xhs && npm install")
    print()
    print("然后配置 Cookie：")
    print("  echo 'COOKIES=你的Cookie值' > spider_xhs/.env")


if __name__ == "__main__":
    main()
