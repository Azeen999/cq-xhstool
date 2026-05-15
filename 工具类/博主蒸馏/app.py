"""
博主蒸馏器 — Web 界面
一键启动：python app.py
然后浏览器打开 http://localhost:5000
"""

import os
import sys
import json
import time
import queue
import threading
import subprocess
from pathlib import Path

# ── 切换到脚本所在目录（确保相对路径正确） ──
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify, Response, send_file

app = Flask(__name__)

# ── 全局任务记录 ──
_tasks: dict[str, dict] = {}
_task_lock = threading.Lock()

SCRIPTS_DIR = Path("scripts").resolve()
DATA_DIR = Path("data")
OUTPUT_DIR = Path("output")
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


# =============================================================
#  工具函数
# =============================================================

def _next_id() -> str:
    return f"task_{int(time.time())}_{len(_tasks)}"


def _run_subprocess(cmd: list, log_queue: queue.Queue):
    """在子线程中运行命令，输出逐行写入 log_queue"""
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            errors="replace",
            bufsize=1,           # 行缓冲
        )
        for line in iter(proc.stdout.readline, ""):
            log_queue.put(line)
            if not line:
                break
        proc.wait()
        log_queue.put(f"__EXIT_CODE__:{proc.returncode}\n")
    except Exception as e:
        log_queue.put(f"__EXIT_CODE__:1\n__ERROR__:{e}\n")
    finally:
        log_queue.put(None)  # 结束信号


def _find_result_json(task_data: dict) -> str | None:
    """扫描 data 目录找最新的 _notes_details.json"""
    pattern = "*_notes_details.json"
    files = sorted(DATA_DIR.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)
    return str(files[0]) if files else None


def _find_analysis_json(task_data: dict) -> str | None:
    """扫描 output 目录找分析结果"""
    files = sorted(OUTPUT_DIR.glob("*_数据底稿.md"), key=lambda f: f.stat().st_mtime, reverse=True)
    return str(files[0]) if files else None


# =============================================================
#  路由
# =============================================================

@app.route("/")
def index():
    """主页面"""
    return render_template("index.html")


@app.route("/api/start-crawl", methods=["POST"])
def start_crawl():
    """启动采集任务"""
    data = request.get_json()
    url = (data.get("url") or "").strip()
    user_id = (data.get("user_id") or "").strip()
    mode = data.get("mode", "url")  # url | id | self
    max_notes = data.get("max_notes", 30)

    # 构建命令
    python = sys.executable
    script = str(SCRIPTS_DIR / "spider_xhs_adapter.py")
    cmd = [python, script, "--output", str(DATA_DIR), "--max-notes", str(max_notes)]

    if mode == "self":
        cmd.append("--self")
    elif mode == "url" and url:
        cmd.extend(["--url", url])
    elif mode == "id" and user_id:
        cmd.extend(["--user-id", user_id])
    else:
        return jsonify({"ok": False, "error": "请提供博主 URL 或用户 ID"})

    # 创建任务
    task_id = _next_id()
    log_queue = queue.Queue()
    task = {
        "id": task_id,
        "type": "crawl",
        "cmd": cmd,
        "queue": log_queue,
        "done": False,
        "exit_code": None,
        "result_path": None,
    }
    with _task_lock:
        _tasks[task_id] = task

    # 启动线程
    t = threading.Thread(target=_run_subprocess, args=(cmd, log_queue), daemon=True)
    t.start()

    return jsonify({"ok": True, "task_id": task_id})


@app.route("/api/run-analysis", methods=["POST"])
def run_analysis():
    """启动分析（Phase 2）"""
    data = request.get_json()
    details_file = (data.get("details_file") or "").strip()

    if not details_file or not os.path.isfile(details_file):
        # 自动找最新的
        found = _find_result_json({})
        if not found:
            return jsonify({"ok": False, "error": "未找到采集数据文件，请先采集"})
        details_file = found

    python = sys.executable
    cmd = [
        python, str(SCRIPTS_DIR / "analyze.py"),
        details_file, "-o", str(DATA_DIR),
    ]

    task_id = _next_id()
    log_queue = queue.Queue()
    task = {
        "id": task_id,
        "type": "analysis",
        "cmd": cmd,
        "queue": log_queue,
        "done": False,
        "exit_code": None,
        "result_path": details_file,
    }
    with _task_lock:
        _tasks[task_id] = task

    t = threading.Thread(target=_run_subprocess, args=(cmd, log_queue), daemon=True)
    t.start()

    return jsonify({"ok": True, "task_id": task_id})


@app.route("/api/run-deep", methods=["POST"])
def run_deep():
    """启动深度分析（Phase 3 Step A）"""
    data = request.get_json()
    blogger_name = (data.get("blogger_name") or "").strip()
    mode = data.get("mode", "A")

    if not blogger_name:
        return jsonify({"ok": False, "error": "请输入博主名称"})

    # 自动找 analysis.json
    analysis_files = sorted(
        DATA_DIR.glob("*_analysis.json"),
        key=lambda f: f.stat().st_mtime, reverse=True
    )
    if not analysis_files:
        return jsonify({"ok": False, "error": "未找到分析文件，请先运行分析"})

    analysis_file = str(analysis_files[0])

    # 自动找 details.json
    details_files = sorted(
        DATA_DIR.glob("*_notes_details.json"),
        key=lambda f: f.stat().st_mtime, reverse=True
    )
    details_file = str(details_files[0]) if details_files else ""

    python = sys.executable
    cmd = [
        python, str(SCRIPTS_DIR / "deep_analyze.py"),
        analysis_file, blogger_name,
        "-o", str(OUTPUT_DIR),
        "--details", details_file,
        "--mode", mode,
    ]

    task_id = _next_id()
    log_queue = queue.Queue()
    task = {
        "id": task_id,
        "type": "deep",
        "cmd": cmd,
        "queue": log_queue,
        "done": False,
        "exit_code": None,
        "result_path": str(OUTPUT_DIR),
    }
    with _task_lock:
        _tasks[task_id] = task

    t = threading.Thread(target=_run_subprocess, args=(cmd, log_queue), daemon=True)
    t.start()

    return jsonify({"ok": True, "task_id": task_id})


@app.route("/api/task/<task_id>/stream")
def task_stream(task_id: str):
    """SSE 实时日志流"""
    with _task_lock:
        task = _tasks.get(task_id)
    if not task:
        return jsonify({"error": "task not found"}), 404

    log_queue = task["queue"]

    def generate():
        while True:
            line = log_queue.get()  # 阻塞等待
            if line is None:
                # 任务结束
                yield "event: done\ndata: \n\n"
                break
            # 用 JSON 编码保证安全
            encoded = json.dumps(line.rstrip("\n"))
            yield f"data: {encoded}\n\n"

    return Response(generate(), mimetype="text/event-stream")


@app.route("/api/task/<task_id>/status")
def task_status(task_id: str):
    """查询任务状态"""
    with _task_lock:
        task = _tasks.get(task_id)
    if not task:
        return jsonify({"error": "not found"}), 404

    # 尝试从队列读取 exit_code（非阻塞）
    exit_code = task.get("exit_code")
    done = task.get("done", False)

    # 收集结果文件
    result_files = {}
    if done:
        if task["type"] == "crawl":
            f = _find_result_json(task)
            if f:
                result_files["details_json"] = f
        elif task["type"] == "analysis":
            af = sorted(DATA_DIR.glob("*_analysis.json"), key=lambda f: f.stat().st_mtime, reverse=True)
            if af:
                result_files["analysis_json"] = str(af[0])
        elif task["type"] == "deep":
            dm = sorted(OUTPUT_DIR.glob("*_数据底稿.md"), key=lambda f: f.stat().st_mtime, reverse=True)
            tm = sorted(OUTPUT_DIR.glob("*_AI蒸馏任务.md"), key=lambda f: f.stat().st_mtime, reverse=True)
            if dm:
                result_files["data_draft"] = str(dm[0])
            if tm:
                result_files["ai_task"] = str(tm[0])

    return jsonify({
        "ok": True,
        "task_id": task_id,
        "done": done,
        "exit_code": exit_code,
        "result_files": result_files,
    })


@app.route("/api/download")
def download_file():
    """下载文件"""
    filepath = request.args.get("path", "")
    if not filepath or not os.path.isfile(filepath):
        return "File not found", 404

    filename = os.path.basename(filepath)
    return send_file(filepath, as_attachment=True, download_name=filename)


@app.route("/api/find-results")
def find_results():
    """查找已有的结果文件"""
    result = {
        "details_files": [],
        "analysis_files": [],
        "data_drafts": [],
        "ai_tasks": [],
    }
    for f in sorted(DATA_DIR.glob("*_notes_details.json"), key=lambda f: f.stat().st_mtime, reverse=True):
        result["details_files"].append(str(f))
    for f in sorted(DATA_DIR.glob("*_analysis.json"), key=lambda f: f.stat().st_mtime, reverse=True):
        result["analysis_files"].append(str(f))
    for f in sorted(OUTPUT_DIR.glob("*_数据底稿.md"), key=lambda f: f.stat().st_mtime, reverse=True):
        result["data_drafts"].append(str(f))
    for f in sorted(OUTPUT_DIR.glob("*_AI蒸馏任务.md"), key=lambda f: f.stat().st_mtime, reverse=True):
        result["ai_tasks"].append(str(f))
    return jsonify(result)


@app.route("/api/check-env", methods=["GET"])
def check_env():
    """检查环境配置"""
    checks = {}

    # Python
    checks["python"] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    # Spider_XHS 目录
    spider_dir = Path("spider_xhs")
    checks["spider_xhs"] = str(spider_dir.resolve()) if spider_dir.is_dir() else "NOT_FOUND"

    # .env
    env_file = spider_dir / ".env"
    checks["env_file"] = "FOUND" if env_file.is_file() else "NOT_FOUND"

    # Node.js
    try:
        r = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5)
        checks["nodejs"] = r.stdout.strip() if r.returncode == 0 else "NOT_FOUND"
    except Exception:
        checks["nodejs"] = "NOT_FOUND"

    # 核心 Python 包
    for pkg in ["requests", "flask", "execjs"]:
        try:
            __import__(pkg)
            checks[f"pkg_{pkg}"] = "OK"
        except ImportError:
            checks[f"pkg_{pkg}"] = "MISSING"

    return jsonify({"ok": True, "checks": checks})


# =============================================================
#  启动
# =============================================================

if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    print("=" * 50)
    print(" 博主蒸馏器 — Web 界面")
    print("=" * 50)
    print(f" 启动: http://localhost:5000")
    print(f" 数据: {DATA_DIR.resolve()}")
    print(f" 产出: {OUTPUT_DIR.resolve()}")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
