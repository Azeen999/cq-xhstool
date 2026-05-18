"""
小红书工具箱 — 统一 Web 入口
包含：博主分析、帖子深挖、文案改写、写作库
一键启动：python app.py
"""

import os
import sys
import json
import time
import queue
import threading
import subprocess
from datetime import datetime
from pathlib import Path

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify, Response, send_file

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

# ── 全局 CORS 头（兼容浏览器限制） ──
@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response

# ── 路径常量 ──
ROOT = Path(".").resolve()
TOOLS_DIR = ROOT / "工具类"
MATERIAL_DIR = ROOT / "素材库"
OUTPUT_DIR = ROOT / "output"
SPIDER_DIR = TOOLS_DIR / "博主蒸馏" / "spider_xhs"
DATA_DIR = TOOLS_DIR / "博主蒸馏" / "data"

# 素材库子目录
MATERIAL_BLOGGER_DIR = MATERIAL_DIR / "博主风格"  # 已分析的博主风格（deep_analyze产出）
MATERIAL_SELF_DIR = MATERIAL_DIR / "自我参数"    # 自己的写作参数

DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MATERIAL_SELF_DIR.mkdir(parents=True, exist_ok=True)
MATERIAL_BLOGGER_DIR.mkdir(parents=True, exist_ok=True)

# ── 全局任务管理 ──
_tasks: dict[str, dict] = {}
_task_lock = threading.Lock()
_running_procs: dict[str, subprocess.Popen] = {}
_procs_lock = threading.Lock()
_task_stop_flags: dict[str, threading.Event] = {}
_stop_flags_lock = threading.Lock()


def _next_id() -> str:
    return f"task_{int(time.time())}_{len(_tasks)}"


def _get_stop_event(task_id: str) -> threading.Event:
    with _stop_flags_lock:
        if task_id not in _task_stop_flags:
            _task_stop_flags[task_id] = threading.Event()
        return _task_stop_flags[task_id]


def _cleanup_stop_event(task_id: str):
    with _stop_flags_lock:
        _task_stop_flags.pop(task_id, None)


def _is_stopped(task_id: str) -> bool:
    with _stop_flags_lock:
        ev = _task_stop_flags.get(task_id)
        return ev is not None and ev.is_set()


def _run_subprocess(cmd: list, log_queue: queue.Queue, task_id: str | None = None, cwd=None):
    """在子线程中运行命令，输出逐行写入 log_queue。task_id 不为 None 时自动更新任务状态"""
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    exit_code = 1
    try:
        if task_id is not None and _is_stopped(task_id):
            log_queue.put("[STOP] 任务已被用户终止，跳过启动\n")
            return
        # 使用二进制模式 + 手动 decode，避免 Python 3.14 _readerthread
        # 在 GBK 系统上解码失败导致 pipe 崩溃的问题
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=cwd,
            env=env,
        )
        if task_id is not None:
            with _procs_lock:
                _running_procs[task_id] = proc
        for line in iter(proc.stdout.readline, b""):
            text = line.decode("utf-8", errors="replace")
            log_queue.put(text)
        proc.wait()
        exit_code = proc.returncode
        log_queue.put(f"__EXIT_CODE__:{exit_code}\n")
    except Exception as e:
        log_queue.put(f"__EXIT_CODE__:1\n__ERROR__:{e}\n")
    finally:
        if task_id is not None:
            _cleanup_stop_event(task_id)
            with _procs_lock:
                _running_procs.pop(task_id, None)
            with _task_lock:
                if task_id in _tasks:
                    _tasks[task_id]["done"] = True
                    _tasks[task_id]["exit_code"] = exit_code
        log_queue.put(None)


# =============================================================
#  工具函数
# =============================================================

def _find_result_json():
    files = sorted(DATA_DIR.glob("*_notes_details.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    return str(files[0]) if files else None

def _find_analysis_json():
    files = sorted(DATA_DIR.glob("*_analysis.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    return str(files[0]) if files else None

def _find_deep_output(prefix=""):
    search_roots = [OUTPUT_DIR]
    if MATERIAL_SELF_DIR.is_dir():
        search_roots.append(MATERIAL_SELF_DIR)
    if MATERIAL_BLOGGER_DIR.is_dir():
        search_roots.append(MATERIAL_BLOGGER_DIR)
    dm, tm, bk, fm, tp = [], [], [], [], []
    for root in search_roots:
        dm.extend(root.rglob(f"{prefix}*_数据底稿.md"))
        tm.extend(root.rglob(f"{prefix}*_AI蒸馏任务.md"))
        bk.extend(root.rglob(f"{prefix}*_博主深度拆解.md"))
        fm.extend(root.rglob(f"{prefix}*_内容公式总结.md"))
        tp.extend(root.rglob(f"{prefix}*_选题素材库.md"))
    # 按修改时间排序，取最新的
    for lst in [dm, tm, bk, fm, tp]:
        lst.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return {
        "data_draft": str(dm[0]) if dm else None,
        "ai_task": str(tm[0]) if tm else None,
        "deep_breakdown": str(bk[0]) if bk else None,
        "formula_summary": str(fm[0]) if fm else None,
        "topic_library": str(tp[0]) if tp else None,
    }

def _tree_walk(dir_path: Path, prefix=""):
    """递归列出目录树"""
    items = []
    try:
        entries = sorted(dir_path.iterdir(), key=lambda e: (not e.is_dir(), e.name))
    except PermissionError:
        return items
    for entry in entries:
        name = entry.name
        if name.startswith("."):
            continue
        if entry.is_dir():
            children = _tree_walk(entry, f"{prefix}{name}/")
            items.append({"name": name, "type": "dir", "path": str(entry), "children": children})
        else:
            size = entry.stat().st_size
            items.append({"name": name, "type": "file", "path": str(entry), "size": size})
    return items


# =============================================================
#  博主蒸馏 — 路由
# =============================================================

def _run_pipeline(params: dict, log_queue: queue.Queue, task_id: str):
    """一键管道：采集 → 分析 → 蒸馏，依次执行，通过 SSE 推送阶段进度"""
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    exit_code = 0
    result_files = {}

    def _run_cmd(cmd, cwd=None):
        nonlocal exit_code
        if _is_stopped(task_id):
            log_queue.put("[STOP] 任务已被用户终止，跳过此阶段\n")
            return -1
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd, env=env)
        with _procs_lock:
            _running_procs[task_id] = proc
        for line in iter(proc.stdout.readline, b""):
            text = line.decode("utf-8", errors="replace")
            log_queue.put(text)
        proc.wait()
        with _procs_lock:
            _running_procs.pop(task_id, None)
        return proc.returncode

    try:
        # ── Phase 1: 采集 ──
        log_queue.put("__PHASE__:1\n")
        python = sys.executable
        script = str(TOOLS_DIR / "博主蒸馏" / "scripts" / "spider_xhs_adapter.py")
        cmd = [python, script, "--output", str(DATA_DIR), "--max-notes", str(params["max_notes"])]
        if params.get("url"):
            cmd.extend(["--url", params["url"]])
        elif params.get("mode") == "self":
            cmd.append("--self")
        elif params.get("user_id"):
            cmd.extend(["--user-id", params["user_id"]])
        else:
            log_queue.put("[ERROR] 缺少博主 URL 或用户 ID\n")
            exit_code = 1
            return

        rc = _run_cmd(cmd)
        if rc != 0:
            log_queue.put(f"[ERROR] 采集阶段失败 (exit={rc})\n")
            exit_code = rc
            return

        details_file = _find_result_json()
        if details_file:
            result_files["details_json"] = details_file
            try:
                with open(details_file, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                if isinstance(raw, dict) and raw.get("blogger", {}).get("nickname"):
                    params["blogger_name"] = raw["blogger"]["nickname"]
                raw_details = raw.get("details", []) if isinstance(raw, dict) else raw
                bad_items = [i for i, item in enumerate(raw_details) if not isinstance(item, dict)]
                if bad_items:
                    log_queue.put(f"[WARN] 数据中有 {len(bad_items)} 个非字典项（索引: {bad_items[:5]}），将跳过\n")
            except Exception as e:
                log_queue.put(f"[WARN] 数据文件读取异常: {e}\n")
        log_queue.put("__PHASE_DONE__:1\n")

        # ── Phase 2: 分析 ──
        log_queue.put("__PHASE__:2\n")
        if not details_file:
            log_queue.put("[ERROR] 未找到采集数据文件，跳过分析\n")
            exit_code = 1
            return

        cmd = [python, str(TOOLS_DIR / "博主蒸馏" / "scripts" / "analyze.py"), details_file, "-o", str(DATA_DIR)]
        rc = _run_cmd(cmd)
        if rc != 0:
            log_queue.put(f"[ERROR] 分析阶段失败 (exit={rc})\n")
            exit_code = rc
            return

        analysis_file = _find_analysis_json()
        if analysis_file:
            result_files["analysis_json"] = analysis_file
        log_queue.put("__PHASE_DONE__:2\n")

        # ── Phase 3: 蒸馏 ──
        log_queue.put("__PHASE__:3\n")
        blogger_name = params.get("blogger_name", "")
        if not blogger_name and analysis_file:
            blogger_name = Path(analysis_file).name.replace("_analysis.json", "")
        if not blogger_name:
            blogger_name = "unknown"

        if not analysis_file:
            log_queue.put("[ERROR] 未找到分析文件，跳过蒸馏\n")
            exit_code = 1
            return

        details_files = sorted(DATA_DIR.glob("*_notes_details.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        details_for_deep = str(details_files[0]) if details_files else ""

        mode = params.get("deep_mode", "A")
        # 根据模式输出到对应的素材目录
        deep_out_dir = str(MATERIAL_SELF_DIR) if mode == "B" else str(MATERIAL_BLOGGER_DIR)
        os.makedirs(deep_out_dir, exist_ok=True)
        cmd = [
            python, str(TOOLS_DIR / "博主蒸馏" / "scripts" / "deep_analyze.py"),
            analysis_file, blogger_name,
            "-o", deep_out_dir,
            "--details", details_for_deep,
            "--mode", mode,
        ]
        rc = _run_cmd(cmd)
        if rc != 0:
            log_queue.put(f"[ERROR] 蒸馏阶段失败 (exit={rc})\n")
            exit_code = rc
            return

        deep_out = _find_deep_output()
        result_files.update(deep_out)
        log_queue.put("__PHASE_DONE__:3\n")

    except Exception as e:
        log_queue.put(f"[ERROR] 管道异常: {e}\n")
        exit_code = 1
    finally:
        _cleanup_stop_event(task_id)
        with _task_lock:
            if task_id in _tasks:
                _tasks[task_id]["done"] = True
                _tasks[task_id]["exit_code"] = exit_code
                _tasks[task_id]["result_files"] = result_files
        log_queue.put(None)


@app.route("/api/one-click-analyze", methods=["POST", "GET"])
def one_click_analyze():
    """一键分析：采集 → 分析 → 蒸馏，自动串联"""
    if request.method == "GET":
        data = request.args
    else:
        data = request.get_json() or request.form

    url = (data.get("url") or "").strip()
    user_id = (data.get("user_id") or "").strip()
    mode = data.get("mode", "url")
    max_notes = data.get("max_notes", 30)
    blogger_name = (data.get("blogger_name") or "").strip()
    deep_mode = data.get("deep_mode", "A")

    if mode != "self" and not url and not user_id:
        return jsonify({"ok": False, "error": "请提供博主 URL 或用户 ID"})

    params = {
        "url": url,
        "user_id": user_id,
        "mode": mode,
        "max_notes": max_notes,
        "blogger_name": blogger_name,
        "deep_mode": deep_mode,
    }

    task_id = _next_id()
    log_queue = queue.Queue()
    task = {
        "id": task_id,
        "type": "pipeline",
        "queue": log_queue,
        "done": False,
        "exit_code": None,
        "result_files": {},
    }
    with _task_lock:
        _tasks[task_id] = task
    t = threading.Thread(target=_run_pipeline, args=(params, log_queue, task_id), daemon=True)
    t.start()
    return jsonify({"ok": True, "task_id": task_id})


@app.route("/api/start-crawl", methods=["POST", "GET"])
def start_crawl():
    if request.method == "GET":
        data = request.args
    else:
        data = request.get_json() or request.form
    url = (data.get("url") or "").strip()
    user_id = (data.get("user_id") or "").strip()
    mode = data.get("mode", "url")
    max_notes = data.get("max_notes", 30)

    python = sys.executable
    script = str(TOOLS_DIR / "博主蒸馏" / "scripts" / "spider_xhs_adapter.py")
    cmd = [python, script, "--output", str(DATA_DIR), "--max-notes", str(max_notes)]

    if url:
        cmd.extend(["--url", url])
    elif mode == "self":
        cmd.append("--self")
    elif mode == "id" and user_id:
        cmd.extend(["--user-id", user_id])
    else:
        return jsonify({"ok": False, "error": "请提供博主 URL 或用户 ID"})

    task_id = _next_id()
    log_queue = queue.Queue()
    task = {"id": task_id, "type": "crawl", "cmd": cmd, "queue": log_queue, "done": False, "exit_code": None}
    with _task_lock:
        _tasks[task_id] = task
    t = threading.Thread(target=_run_subprocess, args=(cmd, log_queue, task_id), daemon=True)
    t.start()
    return jsonify({"ok": True, "task_id": task_id})


@app.route("/api/run-analysis", methods=["POST", "GET"])
def run_analysis():
    data = request.args if request.method == "GET" else (request.get_json() or request.form)
    details_file = (data.get("details_file") or "").strip()
    if not details_file or not os.path.isfile(details_file):
        found = _find_result_json()
        if not found:
            return jsonify({"ok": False, "error": "未找到采集数据文件，请先采集"})
        details_file = found

    python = sys.executable
    cmd = [python, str(TOOLS_DIR / "博主蒸馏" / "scripts" / "analyze.py"), details_file, "-o", str(DATA_DIR)]

    task_id = _next_id()
    log_queue = queue.Queue()
    task = {"id": task_id, "type": "analysis", "cmd": cmd, "queue": log_queue, "done": False, "exit_code": None}
    with _task_lock:
        _tasks[task_id] = task
    t = threading.Thread(target=_run_subprocess, args=(cmd, log_queue, task_id), daemon=True)
    t.start()
    return jsonify({"ok": True, "task_id": task_id})


@app.route("/api/run-deep", methods=["POST", "GET"])
def run_deep():
    data = request.args if request.method == "GET" else (request.get_json() or request.form)
    blogger_name = (data.get("blogger_name") or "").strip()
    mode = data.get("mode", "A")
    if not blogger_name:
        return jsonify({"ok": False, "error": "请输入博主名称"})

    analysis_files = sorted(DATA_DIR.glob("*_analysis.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not analysis_files:
        return jsonify({"ok": False, "error": "未找到分析文件，请先运行分析"})

    analysis_file = str(analysis_files[0])
    details_files = sorted(DATA_DIR.glob("*_notes_details.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    details_file = str(details_files[0]) if details_files else ""

    python = sys.executable
    cmd = [
        python, str(TOOLS_DIR / "博主蒸馏" / "scripts" / "deep_analyze.py"),
        analysis_file, blogger_name,
        "-o", str(OUTPUT_DIR),
        "--details", details_file,
        "--mode", mode,
    ]

    task_id = _next_id()
    log_queue = queue.Queue()
    task = {"id": task_id, "type": "deep", "cmd": cmd, "queue": log_queue, "done": False, "exit_code": None}
    with _task_lock:
        _tasks[task_id] = task
    t = threading.Thread(target=_run_subprocess, args=(cmd, log_queue, task_id), daemon=True)
    t.start()
    return jsonify({"ok": True, "task_id": task_id})


# =============================================================
#  帖子深挖 — 路由
# =============================================================

def _scan_post_dive_history():
    """扫描帖子深挖历史记录"""
    pd_dir = OUTPUT_DIR / "帖子深挖"
    if not pd_dir.is_dir():
        return []
    import re
    records = []
    for md_file in sorted(pd_dir.glob("帖子分析_*.md"), key=lambda f: f.stat().st_mtime, reverse=True):
        note_id = md_file.stem.replace("帖子分析_", "")
        mtime = datetime.fromtimestamp(md_file.stat().st_mtime)
        title = ""
        try:
            content = md_file.read_text(encoding="utf-8")
            tm = re.search(r"\*\*标题\*\*:\s*(.+)", content)
            if tm:
                title = tm.group(1).strip()
            if not title or title == "无标题":
                am = re.search(r"\*\*作者\*\*:\s*(.+)", content)
                author = am.group(1).strip() if am else ""
                title = f"{author}的帖子" if author and author != "未知作者" else f"帖子 {note_id[:8]}"
        except Exception:
            title = f"帖子 {note_id[:8]}"
        url = f"https://www.xiaohongshu.com/explore/{note_id}"
        records.append({
            "note_id": note_id,
            "title": title,
            "url": url,
            "path": str(md_file),
            "time": mtime.strftime("%Y-%m-%d %H:%M"),
            "mtime_ts": md_file.stat().st_mtime,
        })
    return records


@app.route("/api/post-dive/history")
def post_dive_history():
    return jsonify({"ok": True, "records": _scan_post_dive_history()})


@app.route("/api/post-dive/read")
def post_dive_read():
    filepath = request.args.get("path", "")
    if not filepath:
        return jsonify({"ok": False, "error": "no path"})
    full_path = Path(filepath).resolve()
    pd_dir = (OUTPUT_DIR / "帖子深挖").resolve()
    if not str(full_path).startswith(str(pd_dir)):
        return jsonify({"ok": False, "error": "access denied"})
    if not full_path.is_file():
        return jsonify({"ok": False, "error": "file not found"})
    try:
        content = full_path.read_text(encoding="utf-8")
    except Exception:
        return jsonify({"ok": False, "error": "read failed"})
    return jsonify({"ok": True, "content": content, "name": full_path.name})


@app.route("/api/start-post-dive", methods=["POST", "GET"])
def start_post_dive():
    data = request.args if request.method == "GET" else (request.get_json() or request.form)
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"ok": False, "error": "请提供帖子链接"})

    python = sys.executable
    run_script = str(TOOLS_DIR / "帖子深挖" / "run.py")
    # 同时支持 /item/ 和 /explore/ 两种 URL 格式
    note_id = "unknown"
    for pat in ["/item/", "/explore/"]:
        if pat in url:
            note_id = url.split(pat)[-1].split("?")[0]
            break
    output_dir = str(OUTPUT_DIR / "帖子深挖")
    os.makedirs(output_dir, exist_ok=True)
    cmd = [python, run_script, url, "-o", output_dir]

    task_id = _next_id()
    log_queue = queue.Queue()
    task = {"id": task_id, "type": "post_dive", "cmd": cmd, "queue": log_queue, "done": False, "exit_code": None}
    with _task_lock:
        _tasks[task_id] = task
    t = threading.Thread(target=_run_subprocess, args=(cmd, log_queue, task_id), daemon=True)
    t.start()
    return jsonify({"ok": True, "task_id": task_id})


# =============================================================
#  文案改写 — 路由
# =============================================================

def _scan_rewrite_styles():
    """扫描所有可用的创作风格 SKILL.md"""
    styles = []
    for skill_path in sorted(MATERIAL_SELF_DIR.rglob("SKILL.md")):
        try:
            content = skill_path.read_text(encoding="utf-8")
        except Exception:
            content = ""
        name = _extract_style_name(skill_path, content)
        styles.append({"name": name, "path": str(skill_path), "preview": content[:200]})
    for search_dir in [OUTPUT_DIR, MATERIAL_BLOGGER_DIR]:
        for skill_path in sorted(search_dir.rglob("SKILL.md")):
            try:
                content = skill_path.read_text(encoding="utf-8")
            except Exception:
                content = ""
            name = _extract_style_name(skill_path, content)
            styles.append({"name": name, "path": str(skill_path), "preview": content[:200]})
    seen = set()
    unique = []
    for s in styles:
        if s["name"] not in seen:
            seen.add(s["name"])
            unique.append(s)
    return unique


def _extract_style_name(skill_path, content):
    import re
    m = re.search(r"^name:\s*(.+)$", content, re.MULTILINE)
    if m:
        raw = m.group(1).strip()
        if any('\u4e00' <= c <= '\u9fff' for c in raw):
            return raw
        label = raw.replace("-creation-guide", "").replace("-guide", "").replace("-", " ").title()
        dm = re.search(r"description:\s*[\|>]*\s*\n?\s*(.+)", content, re.MULTILINE)
        if dm:
            desc = dm.group(1).strip()
            cm = re.search(r"「(.+?)」", desc)
            if cm:
                return cm.group(1) + "风格"
            cm2 = re.search(r"([\u4e00-\u9fff]{2,6})(?:内容|创作|风格|文案)", desc)
            if cm2:
                return cm2.group(1) + "风格"
        return label
    m2 = re.search(r"^#\s*(.+?)[·\s]", content, re.MULTILINE)
    if m2:
        return m2.group(1).strip() + "风格"
    parent = skill_path.parent.parent
    if parent.name == "创作指南.skill":
        return parent.parent.name + "风格"
    return parent.name


@app.route("/api/rewrite/styles")
def rewrite_styles():
    return jsonify({"ok": True, "styles": _scan_rewrite_styles()})


@app.route("/api/rewrite/generate", methods=["POST"])
def rewrite_generate():
    """SSE 流式代理大模型 API，生成改写文案"""
    body = request.json or {}
    api_url = body.get("api_url", "").strip()
    api_key = body.get("api_key", "").strip()
    model = body.get("model", "deepseek-chat").strip()
    reference_text = body.get("reference_text", "").strip()
    style_path = body.get("style_path", "")
    activity_type = body.get("activity_type", "")
    word_count = body.get("word_count", 200)
    tone_level = body.get("tone_level", 3)

    if not api_url:
        return jsonify({"ok": False, "error": "请填写 API URL"}), 400
    if not api_key:
        return jsonify({"ok": False, "error": "请填写 API Key"}), 400
    if not reference_text:
        return jsonify({"ok": False, "error": "请输入参考文案"}), 400

    style_content = ""
    if style_path:
        try:
            style_content = Path(style_path).read_text(encoding="utf-8")
        except Exception:
            pass

    tone_map = {1: "正式书面语，少用emoji", 2: "偏书面，偶尔口语化", 3: "口语化，适度emoji", 4: "非常口语化，大量emoji和网络用语", 5: "极致口语化，全emoji+网络梗"}
    tone_desc = tone_map.get(tone_level, "口语化，适度emoji")

    system_prompt = """你是一个小红书文案创作专家。你的任务是根据用户提供的参考文案和风格要求，改写出符合小红书调性的文案。

## 核心规则
- 口语化、短句分行、emoji点缀、有安利感
- 违禁词（不能出现）：第一/最佳/唯一/顶级/极致/绝对、私信/V/微信/卫星/扣1/暗号、淘宝/抖音/京东及其谐音、包教包会/保证/100%有效、史上/全网最低价
- 合规替换：私信/V/微信 → 点下方链接报名；包教包会 → 专人带教，带你上手

## 输出格式
**标题**（≤20字）

**正文**
[改写后的文案]

**Tags**
#话题标签"""

    user_parts = [f"请根据以下参考文案进行改写：\n\n---\n{reference_text}\n---"]
    if style_content:
        user_parts.append(f"\n\n## 必须遵守的创作风格指南\n\n{style_content[:3000]}\n\n请严格遵循以上风格指南进行创作。")
    if activity_type:
        user_parts.append(f"\n\n## 内容类型\n{activity_type}")
    user_parts.append(f"\n\n## 语气要求\n{tone_desc}")
    user_parts.append(f"\n\n## 字数要求\n控制在{word_count}字左右")
    user_prompt = "".join(user_parts)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    import requests as http_req

    def generate():
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }
            payload = {
                "model": model,
                "messages": messages,
                "stream": True,
                "temperature": 0.7,
                "max_tokens": 2048,
            }
            resp = http_req.post(api_url, headers=headers, json=payload, stream=True, timeout=120)
            resp.raise_for_status()
            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        yield f"data: [DONE]\n\n"
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield f"data: {json.dumps(content)}\n\n"
                    except json.JSONDecodeError:
                        continue
            yield f"data: [DONE]\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps(str(e))}\n\n"

    return Response(generate(), mimetype="text/event-stream")


# =============================================================
#  文案改写 — LLM 改写
# =============================================================

LLM_API_BASE_DEFAULT = "https://api.deepseek.com/v1"


def _get_llm_key() -> str:
    """从 .env 读取 LLM API Key"""
    env_path = SPIDER_DIR / ".env"
    if env_path.is_file():
        import re
        content = env_path.read_text(encoding="utf-8")
        m = re.search(r'LLM_API_KEY\s*=\s*[\'"]?(.*?)[\'"]?\s*$', content, re.MULTILINE)
        if m:
            return m.group(1).strip()
    return ""


def _get_llm_base() -> str:
    """从 .env 读取 LLM API Base URL"""
    env_path = SPIDER_DIR / ".env"
    if env_path.is_file():
        import re
        content = env_path.read_text(encoding="utf-8")
        m = re.search(r'LLM_API_BASE\s*=\s*[\'"]?(.*?)[\'"]?\s*$', content, re.MULTILINE)
        if m:
            return m.group(1).strip().rstrip("/")
    return LLM_API_BASE_DEFAULT


def _save_llm_env(key: str, api_base: str = "") -> None:
    """保存 LLM 配置到 .env"""
    env_path = SPIDER_DIR / ".env"
    content = ""
    if env_path.is_file():
        content = env_path.read_text(encoding="utf-8")
    import re
    if re.search(r'^LLM_API_KEY\s*=', content, re.MULTILINE):
        content = re.sub(r'^LLM_API_KEY\s*=.*$', f'LLM_API_KEY={key}', content, count=1, flags=re.MULTILINE)
    else:
        content += f'\nLLM_API_KEY={key}\n'
    if api_base:
        if re.search(r'^LLM_API_BASE\s*=', content, re.MULTILINE):
            content = re.sub(r'^LLM_API_BASE\s*=.*$', f'LLM_API_BASE={api_base}', content, count=1, flags=re.MULTILINE)
        else:
            content += f'LLM_API_BASE={api_base}\n'
    env_path.write_text(content, encoding="utf-8")


def _call_llm(system_prompt: str, user_text: str) -> dict:
    """调用 OpenAI 兼容接口，返回 {"ok": True, "content": "..."} 或 {"ok": False, "error": "..."}"""
    api_key = _get_llm_key()
    if not api_key:
        return {"ok": False, "error": "API Key 未配置，请先设置"}
    base_url = _get_llm_base()
    url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-v4-flash",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        "temperature": 0.7,
        "max_tokens": 2000,
    }
    try:
        import requests as req
        resp = req.post(url, headers=headers, json=payload, timeout=60)
        if resp.status_code == 401:
            return {"ok": False, "error": "API Key 无效或已过期"}
        if resp.status_code == 404:
            return {"ok": False, "error": f"接口地址错误 (404)。请检查 LLM_API_BASE 配置"}
        resp.raise_for_status()
        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not content:
            return {"ok": False, "error": "模型返回为空"}
        # 过滤 thinking 标签
        import re
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        return {"ok": True, "content": content}
    except req.exceptions.Timeout:
        return {"ok": False, "error": "请求超时，请稍后重试"}
    except req.exceptions.ConnectionError:
        return {"ok": False, "error": f"无法连接 {base_url}，请检查网络或 LLM_API_BASE 配置"}
    except Exception as e:
        return {"ok": False, "error": f"调用失败: {e}"}


@app.route("/api/copy-rewrite-content")
def copy_rewrite_content():
    """返回文案改写的 SKILL.md 内容"""
    skill_path = TOOLS_DIR / "文案改写" / "SKILL.md"
    if skill_path.is_file():
        content = skill_path.read_text(encoding="utf-8")
        return jsonify({"ok": True, "content": content})
    return jsonify({"ok": False, "error": "SKILL.md not found"})


@app.route("/api/llm-status")
def llm_status():
    """检查 LLM API Key 是否已配置"""
    key = _get_llm_key()
    preview = key[:12] + "..." if len(key) > 12 else ""
    return jsonify({"ok": True, "configured": bool(key), "preview": preview})


@app.route("/api/save-llm-key", methods=["POST"])
def save_llm_key():
    """保存 LLM API Key"""
    data = request.get_json() or request.form
    key = (data.get("key") or "").strip()
    api_base = (data.get("api_base") or "").strip()
    if not key:
        return jsonify({"ok": False, "error": "API Key 不能为空"})
    _save_llm_env(key, api_base)
    return jsonify({"ok": True, "message": "LLM 配置已保存"})


@app.route("/api/rewrite-copy", methods=["POST"])
def rewrite_copy():
    """调用 LLM 改写文案"""
    data = request.get_json() or request.form
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"ok": False, "error": "请输入需要改写的文案"})
    skill_path = TOOLS_DIR / "文案改写" / "SKILL.md"
    system_prompt = ""
    if skill_path.is_file():
        content = skill_path.read_text(encoding="utf-8")
        import re
        m = re.match(r'^---.*?---\s*(.*)', content, re.DOTALL)
        if m:
            system_prompt = m.group(1).strip()
        else:
            system_prompt = content.strip()
    else:
        system_prompt = "你是一个小红书文案改写助手。请将用户提供的文案改写成小红书风格：口语化、短句分行、emoji点缀、有安利感。控制在200字左右。"
    system_prompt += "\n\n请直接输出改写后的文案，不要加解释。"
    result = _call_llm(system_prompt, text)
    return jsonify(result)


#  素材库 — 博主风格浏览
# =============================================================

def _scan_bloggers():
    """扫描所有已蒸馏的博主，返回博主列表"""
    bloggers = []
    seen = set()

    analysis_files = sorted(DATA_DIR.glob("*_analysis.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    for af in analysis_files:
        name = af.name.replace("_analysis.json", "")
        if name in seen:
            continue
        seen.add(name)
        info = {"name": name, "files": {}, "notes_count": 0, "avg_likes": 0, "total_likes": 0}
        try:
            with open(af, "r", encoding="utf-8") as f:
                data = json.load(f)
            stats = data.get("stats", {})
            blogger = data.get("blogger", {})
            info["notes_count"] = stats.get("total", 0)
            info["avg_likes"] = stats.get("avg_likes", 0)
            info["total_likes"] = stats.get("total_likes", 0)
            info["total_collects"] = stats.get("total_collects", 0)
            info["total_comments"] = stats.get("total_comments", 0)
            info["category_stats"] = data.get("category_stats", {})
            info["blogger_desc"] = blogger.get("desc", "")
            info["blogger_id"] = blogger.get("bloggerId", "")
            info["notes"] = []
            for n in data.get("notes", []):
                info["notes"].append({
                    "id": n.get("id", ""),
                    "title": n.get("title", ""),
                    "likes": n.get("likes", 0),
                    "collects": n.get("collects", 0),
                    "comments_count": n.get("comments_count", 0),
                    "tags": n.get("tags", []),
                    "category": n.get("category", ""),
                    "type": n.get("type", "normal"),
                })
        except Exception:
            pass
        info["files"]["analysis_json"] = str(af)

        details_f = DATA_DIR / f"{name}_notes_details.json"
        if details_f.exists():
            info["files"]["details_json"] = str(details_f)

        for suffix, key in [
            ("_博主深度拆解.md", "deep_breakdown"),
            ("_内容公式总结.md", "formula_summary"),
            ("_选题素材库.md", "topic_library"),
            ("_数据底稿.md", "data_draft"),
            ("_AI蒸馏任务.md", "ai_task"),
            ("_全量笔记结构化分析.md", "structured_analysis"),
        ]:
            for root in [OUTPUT_DIR, MATERIAL_BLOGGER_DIR]:
                if root.is_dir():
                    matches = list(root.rglob(f"{name}{suffix}"))
                    if matches:
                        info["files"][key] = str(matches[0])
                        break

        # 从新结构（嵌套）/ 旧结构（扁平）两种方式找笔记目录
        notes_dir = None
        for root in [OUTPUT_DIR, MATERIAL_BLOGGER_DIR]:
            if root.is_dir():
                matches = sorted(root.rglob(f"{name}_笔记"), key=lambda p: len(str(p)))
                if matches:
                    notes_dir = matches[0]
                    break
        if notes_dir is not None and notes_dir.is_dir():
            info["files"]["notes_dir"] = str(notes_dir)
            info["posts"] = []
            for sub in sorted(notes_dir.iterdir()):
                if sub.is_dir():
                    body_file = sub / "正文.txt"
                    img_file = sub / "图片列表.txt"
                    post = {
                        "folder": sub.name,
                        "title": sub.name.split("_", 1)[-1] if "_" in sub.name else sub.name,
                    }
                    if body_file.exists():
                        try:
                            post["content"] = body_file.read_text(encoding="utf-8").strip()
                        except Exception:
                            pass
                    if img_file.exists():
                        try:
                            imgs = img_file.read_text(encoding="utf-8").strip().split("\n")
                            post["images"] = [l.strip() for l in imgs if l.strip()]
                        except Exception:
                            pass
                    info["posts"].append(post)

        bloggers.append(info)

    # 第二遍：扫描 素材库/博主风格/ 中的目录，补充没有 analysis.json 的博主
    if MATERIAL_BLOGGER_DIR.is_dir():
        for entry in sorted(MATERIAL_BLOGGER_DIR.iterdir()):
            if not entry.is_dir() or entry.name.startswith('_'):
                continue
            name = entry.name
            if name in seen:
                continue
            seen.add(name)

            info = {"name": name, "files": {}, "notes_count": 0, "avg_likes": 0, "total_likes": 0}

            # 尝试找笔记目录（兼容 笔记/ 和 {name}_笔记/ 两种命名）
            notes_dir = None
            for sub_name in [f"{name}_笔记", "笔记"]:
                p = entry / sub_name
                if p.is_dir():
                    notes_dir = p
                    break
            if notes_dir is not None:
                # 如果笔记目录的子目录里没有 正文.txt，可能是多了一层（如 笔记/薯岛_笔记/）
                inner = sorted(notes_dir.iterdir())
                if all(sub.is_dir() and not (sub / "正文.txt").exists() for sub in inner):
                    # 取第一个有子目录的级
                    for sub in inner:
                        deeper = list(sub.iterdir())
                        if any(d.is_dir() for d in deeper):
                            notes_dir = sub
                            break
                info["files"]["notes_dir"] = str(notes_dir)
                info["posts"] = []
                for sub in sorted(notes_dir.iterdir()):
                    if sub.is_dir():
                        body_file = sub / "正文.txt"
                        img_file = sub / "图片列表.txt"
                        post = {"folder": sub.name, "title": sub.name.split("_", 1)[-1] if "_" in sub.name else sub.name}
                        if body_file.exists():
                            try:
                                post["content"] = body_file.read_text(encoding="utf-8").strip()
                            except Exception:
                                pass
                        if img_file.exists():
                            try:
                                imgs = img_file.read_text(encoding="utf-8").strip().split("\n")
                                post["images"] = [l.strip() for l in imgs if l.strip()]
                            except Exception:
                                pass
                        info["posts"].append(post)
                info["notes_count"] = len(info.get("posts", []))

            # 读取 analysis_data.json 获取统计数据
            ad_file = entry / "analysis_data.json"
            if ad_file.exists():
                try:
                    with open(ad_file, "r", encoding="utf-8") as f:
                        ad = json.load(f)
                    if not info.get("notes_count"):
                        info["notes_count"] = ad.get("total_notes", 0)
                    if not info.get("total_likes"):
                        info["total_likes"] = ad.get("total_likes", 0)
                    if not info.get("avg_likes"):
                        info["avg_likes"] = round(ad.get("avg_likes", 0), 1)
                    info["files"]["analysis_data"] = str(ad_file)
                except Exception:
                    pass

            # 标记已存在的风格文件
            for skill_name in [f"{name}_创作指南.skill", "创作指南.skill"]:
                skill_dir = entry / skill_name
                if skill_dir.is_dir():
                    skill_md = skill_dir / "SKILL.md"
                    info["files"]["deep_breakdown"] = str(skill_md) if skill_md.exists() else str(skill_dir)
                    break

            # 扫描博主根目录下的 .md 文件（如 蒸馏报告.md、粗门问题.md 等）
            for md_file in sorted(entry.glob("*.md")):
                fn = md_file.name
                if "博主深度拆解" in fn or "深度拆解" in fn:
                    info["files"]["deep_breakdown"] = info["files"].get("deep_breakdown") or str(md_file)
                elif "内容公式" in fn or "公式总结" in fn:
                    info["files"]["formula_summary"] = str(md_file)
                elif "选题素材" in fn or "选题库" in fn:
                    info["files"]["topic_library"] = str(md_file)
                elif "数据底稿" in fn:
                    info["files"]["data_draft"] = str(md_file)
                elif "蒸馏报告" in fn:
                    info["files"]["distill_report"] = str(md_file)
                elif "帖子分析" in fn:
                    info["files"]["post_analysis"] = info["files"].get("post_analysis") or str(md_file)
                elif "诊断报告" in fn or "账号诊断" in fn:
                    info["files"]["diagnosis"] = str(md_file)
                else:
                    label = fn.replace(".md", "").replace(name, "").strip("_- ")
                    if label:
                        info["files"]["report_" + label] = str(md_file)
                    else:
                        info["files"]["report_" + fn.replace(".md", "")] = str(md_file)

            # 扫描 分析报告/ 子目录
            report_dir = entry / "分析报告"
            if report_dir.is_dir():
                for md_file in sorted(report_dir.rglob("*.md")):
                    fn = md_file.name
                    if "帖子分析" in fn:
                        info["files"]["post_analysis"] = info["files"].get("post_analysis") or str(md_file)
                    elif "博主深度拆解" in fn or "深度拆解" in fn:
                        info["files"]["deep_breakdown"] = info["files"].get("deep_breakdown") or str(md_file)
                    elif "蒸馏报告" in fn:
                        info["files"]["distill_report"] = str(md_file)
                    elif "诊断报告" in fn or "账号诊断" in fn:
                        info["files"]["diagnosis"] = str(md_file)
                    else:
                        info["files"]["report_" + fn.replace(".md", "")] = str(md_file)
                for html_file in sorted(report_dir.rglob("*.html")):
                    fn = html_file.name
                    if "蒸馏报告" in fn:
                        info["files"]["distill_report_html"] = str(html_file)

            # 扫描 _过程文件/原始素材/ 中的关联文件
            process_dir = MATERIAL_BLOGGER_DIR / "_过程文件" / "原始素材"
            if process_dir.is_dir():
                for md_file in sorted(process_dir.glob(f"{name}_*.md")):
                    fn = md_file.name
                    if "博主深度拆解" in fn:
                        info["files"]["deep_breakdown"] = info["files"].get("deep_breakdown") or str(md_file)
                    elif "内容公式" in fn or "公式总结" in fn:
                        info["files"]["formula_summary"] = info["files"].get("formula_summary") or str(md_file)
                    elif "选题素材" in fn or "选题库" in fn:
                        info["files"]["topic_library"] = info["files"].get("topic_library") or str(md_file)
                    elif "数据底稿" in fn:
                        info["files"]["data_draft"] = info["files"].get("data_draft") or str(md_file)
                    elif "全量笔记结构化分析" in fn:
                        info["files"]["structured_analysis"] = info["files"].get("structured_analysis") or str(md_file)

            bloggers.append(info)

    return bloggers


@app.route("/api/bloggers")
def api_bloggers():
    return jsonify({"ok": True, "bloggers": _scan_bloggers()})


@app.route("/api/blogger/<name>")
def api_blogger_detail(name):
    bloggers = _scan_bloggers()
    for b in bloggers:
        if b["name"] == name:
            return jsonify({"ok": True, "blogger": b})
    return jsonify({"ok": False, "error": "博主不存在"}), 404


@app.route("/api/blogger-file")
def api_blogger_file():
    """读取博主的某个产出文件"""
    filepath = request.args.get("path", "")
    if not filepath:
        return jsonify({"ok": False, "error": "no path"})
    full_path = Path(filepath).resolve()
    if not full_path.is_file():
        return jsonify({"ok": False, "error": "file not found"})
    try:
        content = full_path.read_text(encoding="utf-8")
    except Exception:
        return jsonify({"ok": False, "error": "read failed"})
    return jsonify({"ok": True, "content": content, "name": full_path.name})


@app.route("/api/blogger-html")
def api_blogger_html():
    filepath = request.args.get("path", "")
    if not filepath:
        return "no path", 400
    full_path = Path(filepath).resolve()
    if not full_path.is_file():
        return "file not found", 404
    try:
        content = full_path.read_text(encoding="utf-8")
    except Exception:
        return "read failed", 500
    return content


# =============================================================
#  素材库 — 路由
# =============================================================

_MATERIAL_ROOTS = {
    "博主风格": str(MATERIAL_BLOGGER_DIR.resolve()),
    "自我参数": str(MATERIAL_SELF_DIR.resolve()),
}


@app.route("/api/material-lib/tree")
def material_lib_tree():
    """返回素材库两个分类的目录树"""
    sections = {}
    for section_name, root_path in _MATERIAL_ROOTS.items():
        root = Path(root_path)
        if root.is_dir():
            sections[section_name] = {
                "root": str(root),
                "tree": _tree_walk(root),
            }
        else:
            sections[section_name] = {"root": str(root), "tree": []}
    return jsonify({"ok": True, "sections": sections})


@app.route("/api/material-lib/read")
def material_lib_read():
    """读取素材库中的文件内容（安全检查：必须在任一素材库目录内）"""
    filepath = request.args.get("path", "")
    if not filepath:
        return jsonify({"ok": False, "error": "no path"})
    full_path = Path(filepath).resolve()

    allowed = False
    for root_path in _MATERIAL_ROOTS.values():
        if str(full_path).startswith(root_path):
            allowed = True
            break
    if not allowed:
        return jsonify({"ok": False, "error": "access denied"})
    if not full_path.is_file():
        return jsonify({"ok": False, "error": "file not found"})

    try:
        content = full_path.read_text(encoding="utf-8")
    except Exception:
        return jsonify({"ok": False, "error": "read failed (binary?)"})

    ext = full_path.suffix.lower()
    return jsonify({
        "ok": True,
        "content": content,
        "name": full_path.name,
        "ext": ext,
        "section": next((s for s, p in _MATERIAL_ROOTS.items() if str(full_path).startswith(p)), ""),
    })


@app.route("/api/material-lib/write", methods=["POST"])
def material_lib_write():
    """写入素材库文件（安全检查：必须在自我参数目录内）"""
    body = request.get_json(force=True)
    filepath = body.get("path", "")
    content = body.get("content", "")
    if not filepath:
        return jsonify({"ok": False, "error": "no path"})
    full_path = Path(filepath).resolve()
    self_dir = MATERIAL_SELF_DIR.resolve()
    if not str(full_path).startswith(str(self_dir)):
        return jsonify({"ok": False, "error": "only self-params files can be edited"})
    if not full_path.is_file():
        return jsonify({"ok": False, "error": "file not found"})
    try:
        full_path.write_text(content, encoding="utf-8")
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})
    return jsonify({"ok": True})


# =============================================================
#  共享路由
# =============================================================

@app.route("/")
def index():
    return render_template("index.html", output_dir=str(OUTPUT_DIR.resolve()))


@app.route("/api/task/<task_id>/stream")
def task_stream(task_id: str):
    with _task_lock:
        task = _tasks.get(task_id)
    if not task:
        return jsonify({"error": "task not found"}), 404

    log_queue = task["queue"]

    def generate():
        while True:
            line = log_queue.get()
            if line is None:
                with _task_lock:
                    t = _tasks.get(task_id, {})
                payload = json.dumps({
                    "exit_code": t.get("exit_code", -1),
                    "result_files": t.get("result_files", {}),
                    "type": t.get("type", ""),
                })
                yield f"event: done\ndata: {payload}\n\n"
                break
            stripped = line.rstrip("\n")
            if stripped.startswith("__PHASE__:"):
                phase_num = stripped.split(":")[1]
                yield f"event: phase\ndata: {phase_num}\n\n"
            elif stripped.startswith("__PHASE_DONE__:"):
                phase_num = stripped.split(":")[1]
                yield f"event: phase_done\ndata: {phase_num}\n\n"
            elif stripped.startswith("[ERROR]"):
                yield f"event: error_event\ndata: {json.dumps(stripped)}\n\n"
                yield f"data: {json.dumps(stripped)}\n\n"
            else:
                encoded = json.dumps(stripped)
                yield f"data: {encoded}\n\n"

    return Response(generate(), mimetype="text/event-stream")


@app.route("/api/task/<task_id>/status")
def task_status(task_id: str):
    with _task_lock:
        task = _tasks.get(task_id)
    if not task:
        return jsonify({"error": "not found"}), 404

    done = task.get("done", False)
    exit_code = task.get("exit_code")
    # 优先用任务存储的结果文件，再按类型回退查找
    result_files = task.get("result_files", {})
    if done and not result_files:
        t = task["type"]
        if t == "crawl":
            f = _find_result_json()
            if f:
                result_files["details_json"] = f
        elif t == "analysis":
            af = _find_analysis_json()
            if af:
                result_files["analysis_json"] = af
        elif t in ("deep",):
            result_files = _find_deep_output()
        elif t == "post_dive":
            pd_dir = OUTPUT_DIR / "帖子深挖"
            md_files = sorted(pd_dir.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
            if md_files:
                result_files["report_md"] = str(md_files[0])

    return jsonify({
        "ok": True, "task_id": task_id, "done": done,
        "exit_code": exit_code, "type": task["type"], "result_files": result_files,
    })


@app.route("/api/task/<task_id>/stop", methods=["POST"])
def task_stop(task_id: str):
    """终止正在运行的任务"""
    # 设置停止标志，防止管道在阶段间隙继续
    _get_stop_event(task_id).set()

    with _procs_lock:
        proc = _running_procs.get(task_id)

    if proc:
        try:
            proc.kill()
            # 关闭管道强制 readline 立即返回
            if proc.stdout:
                proc.stdout.close()
            proc.wait(timeout=5)
        except Exception:
            pass

        with _procs_lock:
            _running_procs.pop(task_id, None)

    # 即使没有找到进程（阶段间隙），也标记任务为已完成
    with _task_lock:
        if task_id in _tasks:
            _tasks[task_id]["done"] = True
            _tasks[task_id]["exit_code"] = -1

    return jsonify({"ok": True, "message": "任务已终止"})


@app.route("/api/download")
def download_file():
    filepath = request.args.get("path", "")
    if not filepath or not os.path.isfile(filepath):
        return "File not found", 404
    filename = os.path.basename(filepath)
    return send_file(filepath, as_attachment=True, download_name=filename)


@app.route("/api/find-results")
def find_results():
    result = {"details_files": [], "analysis_files": [], "data_drafts": [], "ai_tasks": []}
    for f in sorted(DATA_DIR.glob("*_notes_details.json"), key=lambda f: f.stat().st_mtime, reverse=True):
        result["details_files"].append(str(f))
    for f in sorted(DATA_DIR.glob("*_analysis.json"), key=lambda f: f.stat().st_mtime, reverse=True):
        result["analysis_files"].append(str(f))
    for f in sorted(OUTPUT_DIR.glob("*_数据底稿.md"), key=lambda f: f.stat().st_mtime, reverse=True):
        result["data_drafts"].append(str(f))
    for f in sorted(OUTPUT_DIR.glob("*_AI蒸馏任务.md"), key=lambda f: f.stat().st_mtime, reverse=True):
        result["ai_tasks"].append(str(f))
    return jsonify(result)


@app.route("/api/self-account")
def self_account():
    """返回当前 Cookie 对应的登录账号信息"""
    try:
        scripts_dir = TOOLS_DIR / "博主蒸馏" / "scripts"
        helper = scripts_dir / "get_self_info.py"
        python = sys.executable
        r = subprocess.run(
            [python, str(helper)],
            capture_output=True, text=True, timeout=30,
            env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
        )
        out = r.stdout.strip()
        if out:
            return jsonify(json.loads(out))
        return jsonify({"ok": False, "error": f"no output (stderr: {r.stderr[:200]})"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/cookie-info")
def cookie_info():
    """返回当前 Cookie 状态"""
    env_path = SPIDER_DIR / ".env"
    if not env_path.is_file():
        return jsonify({"ok": True, "exists": False, "length": 0, "preview": ""})
    try:
        content = env_path.read_text(encoding="utf-8")
        import re
        m = re.search(r'COOKIES\s*=\s*(.*)', content)
        if m:
            val = m.group(1).strip().strip("'\"").strip()
            preview = val[:30] + "..." if len(val) > 30 else val
            return jsonify({"ok": True, "exists": True, "length": len(val), "preview": preview})
        return jsonify({"ok": True, "exists": False, "length": 0, "preview": ""})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/update-cookie", methods=["POST"])
def update_cookie():
    """更新 .env 文件中的 Cookie"""
    data = request.get_json() or request.form
    new_cookie = (data.get("cookie") or "").strip().strip("'").strip('"')
    if not new_cookie:
        return jsonify({"ok": False, "error": "Cookie 不能为空"})
    if len(new_cookie) < 20:
        return jsonify({"ok": False, "error": "Cookie 太短，请复制完整的 Cookie 字符串"})

    env_path = SPIDER_DIR / ".env"
    try:
        if env_path.is_file():
            content = env_path.read_text(encoding="utf-8")
            import re
            if re.search(r'^COOKIES\s*=', content, re.MULTILINE):
                content = re.sub(
                    r'^COOKIES\s*=.*$',
                    f'COOKIES={new_cookie}',
                    content,
                    count=1,
                    flags=re.MULTILINE,
                )
            else:
                content += f'\nCOOKIES={new_cookie}\n'
        else:
            content = f'# 小红书 Cookie\nCOOKIES={new_cookie}\n'

        env_path.write_text(content, encoding="utf-8")
        return jsonify({"ok": True, "message": "Cookie 已更新", "preview": new_cookie[:30] + "..."})
    except Exception as e:
        return jsonify({"ok": False, "error": f"写入失败: {e}"})


@app.route("/api/check-env", methods=["GET"])
def check_env():
    checks = {}
    checks["python"] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    checks["spider_xhs"] = str(SPIDER_DIR.resolve()) if SPIDER_DIR.is_dir() else "NOT_FOUND"
    checks["env_file"] = "FOUND" if (SPIDER_DIR / ".env").is_file() else "NOT_FOUND"
    try:
        r = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5)
        checks["nodejs"] = r.stdout.strip() if r.returncode == 0 else "NOT_FOUND"
    except Exception:
        checks["nodejs"] = "NOT_FOUND"
    for pkg in ["requests", "flask", "execjs"]:
        try:
            __import__(pkg)
            checks[f"pkg_{pkg}"] = "OK"
        except ImportError:
            checks[f"pkg_{pkg}"] = "MISSING"
    return jsonify({"ok": True, "checks": checks})


# =============================================================
#  历史结果 & 文件预览
# =============================================================

def _file_info(f: Path) -> dict:
    return {
        "name": f.name,
        "path": str(f),
        "size": f.stat().st_size,
        "mtime": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
        "ext": f.suffix.lower(),
    }


@app.route("/api/history-results")
def history_results():
    """扫描所有产出目录，按工具分类返回结果列表"""
    results = {
        "博主分析": {"采集数据": [], "分析结果": [], "深度蒸馏": []},
        "帖子深挖": {"分析报告": []},
    }

    for f in sorted(DATA_DIR.glob("*_notes_details.json"), key=lambda f: f.stat().st_mtime, reverse=True):
        results["博主分析"]["采集数据"].append(_file_info(f))
    for f in sorted(DATA_DIR.glob("*_analysis.json"), key=lambda f: f.stat().st_mtime, reverse=True):
        results["博主分析"]["分析结果"].append(_file_info(f))
    for pattern in ["*_数据底稿.md", "*_AI蒸馏任务.md", "*_分析报告.html", "*_创作指南.skill"]:
        for root in [OUTPUT_DIR, OUTPUT_DIR / "博主分析", MATERIAL_BLOGGER_DIR]:
            if root.is_dir():
                for f in sorted(root.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True):
                    if not any(f.name == existing["name"] for existing in results["博主分析"]["深度蒸馏"]):
                        results["博主分析"]["深度蒸馏"].append(_file_info(f))

    for f in sorted((OUTPUT_DIR / "帖子深挖").glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True):
        info = _file_info(f)
        # 从文件内容中提取帖子标题
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
            m = re.search(r'\*\*标题\*\*:\s*(.+)', text)
            if m:
                info["display_name"] = m.group(1).strip()
        except Exception:
            pass
        results["帖子深挖"]["分析报告"].append(info)

    return jsonify({"ok": True, "results": results})


@app.route("/api/delete-file", methods=["POST"])
def delete_file():
    """删除指定的产出文件"""
    data = request.get_json() or request.form
    filepath = (data.get("path") or "").strip()
    if not filepath:
        return jsonify({"ok": False, "error": "no path"})
    full_path = Path(filepath).resolve()
    if not str(full_path).startswith(str(ROOT.resolve())):
        return jsonify({"ok": False, "error": "access denied"})
    if not full_path.is_file():
        return jsonify({"ok": False, "error": "file not found"})
    try:
        os.remove(full_path)
        return jsonify({"ok": True, "message": f"已删除 {full_path.name}"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/file-preview")
def file_preview():
    """读取文件内容用于预览"""
    filepath = request.args.get("path", "")
    if not filepath:
        return jsonify({"ok": False, "error": "no path"})
    full_path = Path(filepath).resolve()
    # 安全检查：必须在项目目录内
    if not str(full_path).startswith(str(ROOT.resolve())):
        return jsonify({"ok": False, "error": "access denied"})
    if not full_path.is_file():
        return jsonify({"ok": False, "error": "file not found"})

    ext = full_path.suffix.lower()
    try:
        raw = full_path.read_bytes()
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        return jsonify({"ok": False, "error": "binary file", "binary": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

    return jsonify({
        "ok": True,
        "content": content,
        "name": full_path.name,
        "ext": ext,
    })


# =============================================================
#  启动
# =============================================================

if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    PORT = int(os.environ.get("XHS_PORT", 5001))

    # 自动释放端口：杀掉占用 5001 的旧进程
    if sys.platform == "win32":
        try:
            r = subprocess.run(
                ["netstat", "-ano"], capture_output=True, text=True, timeout=5
            )
            for line in r.stdout.splitlines():
                if f":{PORT}" in line and "LISTENING" in line:
                    parts = line.strip().split()
                    pid = parts[-1]
                    subprocess.run(
                        ["taskkill", "/F", "/PID", pid],
                        capture_output=True, timeout=5,
                    )
                    print(f"  🧹 已释放端口 {PORT} (PID {pid})")
                    break
        except Exception:
            pass

    print("=" * 50)
    print(" 小红书工具箱 — 统一 Web 入口")
    print("=" * 50)
    print(f" 启动: http://localhost:{PORT}")
    print(f" 工具: 博主分析 / 帖子深挖 / 文案改写")
    print(f" 素材库: {MATERIAL_DIR.resolve()}")
    print(f" 产出: {OUTPUT_DIR.resolve()}")
    print("=" * 50)
    app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)
