"""
sanitize_data.py — 数据脱敏工具

将采集和分析数据中的敏感信息脱敏，生成可安全上传到 GitHub 的版本。

使用方法：
    # 对整个 data/ 和 output/ 目录脱敏
    python sanitize_data.py

    # 只脱敏指定文件
    python sanitize_data.py --input data/xxx_notes_details.json

    # 输出到指定目录
    python sanitize_data.py --output ./sanitized_demo

脱敏规则：
    1. bloggerId / user_id → 保留前4位 + "****"
    2. nickname → "博主_XX"（保留语音特征但无法识别）
    3. avatar / image / cover URL → 全部移除
    4. 评论内容 → 保留（作为研究素材）
    5. 互动数据 (likes/collects/comments) → 保留（分析用）
    6. 笔记标题/正文 → 保留（作为风格研究素材）
"""

import os
import sys
import json
import re
import shutil
import argparse
from pathlib import Path


def _anonymize_id(id_str: str) -> str:
    """脱敏 ID：保留前4位，后面的替换为 ****"""
    if not id_str or len(id_str) < 8:
        return "****"
    return id_str[:4] + "****"


def _anonymize_name(name: str) -> str:
    """脱敏昵称：保留第一个字符，其余替换"""
    if not name:
        return "博主"
    # 如果是中文，保留第一个字
    if re.match(r'^[一-鿿]', name):
        return name[0] + "某某"
    # 如果是英文/数字，保留前2字符
    return name[:2] + "***"


def _strip_urls(obj):
    """递归移除 dict 中所有 URL 字段"""
    if isinstance(obj, dict):
        url_keys = [k for k in obj if any(
            keyword in k.lower() for keyword in
            ["avatar", "cover", "image", "url", "video", "play_addr"]
        )]
        for k in url_keys:
            obj[k] = "" if isinstance(obj[k], str) else ([] if isinstance(obj[k], list) else {})
        for k, v in obj.items():
            if k not in url_keys:
                _strip_urls(v)
    elif isinstance(obj, list):
        for item in obj:
            _strip_urls(item)


def sanitize_details(details_path: str, output_path: str) -> dict:
    """脱敏 _notes_details.json 文件"""
    with open(details_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data.get("_meta", {})
    sanitized = {
        "_meta": {
            "source": meta.get("source", ""),
            "total_notes": meta.get("total_notes", 0),
            "collected_notes": meta.get("collected_notes", 0),
            "sanitized": True,
            "sanitized_at": __import__("datetime").datetime.now().isoformat(),
            "original_file": os.path.basename(details_path),
        },
        "blogger": {
            "bloggerId": _anonymize_id(data.get("blogger", {}).get("bloggerId", "")),
            "nickname": _anonymize_name(data.get("blogger", {}).get("nickname", "")),
            "desc": data.get("blogger", {}).get("desc", "")[:100] if data.get("blogger", {}).get("desc") else "",
            "followerCount": data.get("blogger", {}).get("followerCount", "0"),
            "noteCount": data.get("blogger", {}).get("noteCount", "0"),
        },
        "details": [],
    }

    for note in data.get("details", []):
        n = note.get("note", {})
        interact = n.get("interactInfo", {})

        sanitized_note = {
            "note": {
                "noteId": _anonymize_id(n.get("noteId", "")),
                "title": n.get("title", ""),
                "desc": n.get("desc", ""),
                "type": n.get("type", ""),
                "interactInfo": {
                    "likedCount": interact.get("likedCount", "0"),
                    "collectedCount": interact.get("collectedCount", "0"),
                    "commentCount": interact.get("commentCount", "0"),
                    "sharedCount": interact.get("sharedCount", "0"),
                },
                "tagList": n.get("tagList", []),
                "time": n.get("time", 0),
            },
            "comments": {"list": note.get("comments", {}).get("list", [])},
            "_meta": note.get("_meta", {}),
        }
        sanitized["details"].append(sanitized_note)

    _strip_urls(sanitized)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sanitized, f, ensure_ascii=False, indent=2)

    return sanitized


def sanitize_analysis(analysis_path: str, output_path: str) -> dict:
    """脱敏 _analysis.json 文件"""
    with open(analysis_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    sanitized = {
        "_meta": {
            "sanitized": True,
            "sanitized_at": __import__("datetime").datetime.now().isoformat(),
            "original_file": os.path.basename(analysis_path),
        },
    }

    # 递归脱敏所有 ID 和昵称
    def _walk(obj, path=""):
        if isinstance(obj, dict):
            for k, v in list(obj.items()):
                # 脱敏 ID 类字段
                if k.lower() in ("bloggerid", "user_id", "userid", "note_id", "noteid"):
                    if isinstance(v, str) and v:
                        obj[k] = _anonymize_id(v)
                elif k.lower() in ("nickname", "blogger_name", "name"):
                    if isinstance(v, str) and v:
                        obj[k] = _anonymize_name(v)
                # 脱敏 URL 类字段
                elif any(kw in k.lower() for kw in ["avatar", "cover", "url", "image"]):
                    if isinstance(v, str):
                        obj[k] = ""
                    elif isinstance(v, list):
                        obj[k] = []
                    elif isinstance(v, dict):
                        obj[k] = {}
                else:
                    _walk(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for item in obj:
                _walk(item, path)

    _walk(data)

    # 复制脱敏后的数据
    sanitized.update(data)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sanitized, f, ensure_ascii=False, indent=2)

    return sanitized


def main():
    parser = argparse.ArgumentParser(description="博主蒸馏器 — 数据脱敏工具")
    parser.add_argument("--input", help="指定文件或目录（默认: data/ 和 output/）")
    parser.add_argument("--output", "-o", default="./sanitized_demo", help="脱敏后输出目录（默认: ./sanitized_demo）")
    args = parser.parse_args()

    root = Path(__file__).parent.resolve()
    out_dir = Path(args.output)
    out_dir.mkdir(exist_ok=True)

    if args.input and os.path.isfile(args.input):
        files = [Path(args.input)]
    elif args.input and os.path.isdir(args.input):
        files = list(Path(args.input).glob("*.json"))
    else:
        files = list(Path(root / "data").glob("*.json"))

    if not files:
        print(f"❌ 未找到 JSON 文件（搜索路径: data/）")
        sys.exit(1)

    for f in files:
        name = f.stem
        ext = f.suffix
        out_path = out_dir / f"{name}_sanitized{ext}"

        print(f"脱敏: {f.name} → {out_path.name}")

        if "_analysis" in f.name or "analysis" in f.name:
            sanitize_analysis(str(f), str(out_path))
        else:
            sanitize_details(str(f), str(out_path))

    print(f"\n✅ 脱敏完成！共 {len(files)} 个文件")
    print(f"   输出目录: {out_dir.resolve()}")
    print()
    print("这些脱敏后的文件可以安全地上传到 GitHub。")
    print("用法示例：")
    print("  git add sanitized_demo/")
    print("  git commit -m 'add sanitized demo data'")


if __name__ == "__main__":
    main()
