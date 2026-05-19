"""
粗趣 RAG 问答引擎
基于 jieba 分词 + TF-IDF 向量检索 + DeepSeek 回答
零外部依赖（jieba 已安装）
"""

import os
import re
import json
import math
import pickle
import threading
from pathlib import Path
from collections import Counter

import jieba

# ── 路径常量 ──
ROOT_DIR = Path(__file__).resolve().parent.parent
CUXI_KB_DIR = ROOT_DIR / "素材库" / "自我参数"
INDEX_CACHE = ROOT_DIR / ".rag_index.pkl"


def _tokenize(text: str) -> list[str]:
    """分词 + 过滤停用词"""
    words = jieba.lcut(text)
    # 停用词
    stop = {"的", "了", "和", "是", "就", "都", "而", "及", "与", "着", "或",
            "一个", "没有", "我们", "你们", "他们", "这个", "那个", "这些", "那些",
            "什么", "怎么", "如何", "为什么", "因为", "所以", "但是", "可是",
            "如果", "可以", "能", "会", "要", "应该", "觉得", "认为", "知道",
            "在", "有", "不", "也", "很", "到", "说", "去", "看", "自己",
            "这", "那", "上", "给", "当", "跟", "对", "使", "比", "从",
            "所", "然", "后", "过", "天", "下", "可", "出", "只", "又", "再",
            "把", "无", "被", "中", "更", "吗", "同", "哪", "它", "哦",
            "的", "了", "是", "和", "就", "都", "而", "及", "与", "着",
            "或", "一个", "没有", "我们", "你们", "他们", "这个", "那个",
            "这些", "那些", "什么", "怎么", "如何", "为什么", "因为", "所以",
            "但是", "可是", "如果", "可以", "能", "会", "要", "应该", "觉得",
            "认为", "知道", "在", "有", "不", "也", "很", "到", "说", "去",
            "看", "自己", "这", "那", "上", "给", "当", "跟", "对", "使",
            "比", "从", "所", "然", "后", "过", "天", "下", "可", "出",
            "只", "又", "再", "把", "无", "被", "中", "更", "吗", "同",
            "哪", "它", "哦", "哈", "啊", "嗯", "呢", "吧"}
    return [w.strip() for w in words if len(w.strip()) >= 2 and w.strip() not in stop]


class RAGEngine:
    """粗趣知识库问答引擎"""

    def __init__(self):
        self.chunks: list[dict] = []
        self.doc_vectors: list[Counter] = []  # TF vectors per chunk
        self.idf: dict[str, float] = {}       # IDF weights
        self.ready = False
        self._load_lock = threading.Lock()

    # ── 公开方法 ──

    def load_knowledge_base(self, force=False) -> bool:
        """加载知识库：扫描文件 → 分块 → 计算 TF-IDF"""
        with self._load_lock:
            if self.ready and not force:
                return True

            if not force and INDEX_CACHE.exists():
                try:
                    with open(INDEX_CACHE, "rb") as f:
                        data = pickle.load(f)
                    self.chunks = data["chunks"]
                    self.doc_vectors = data["doc_vectors"]
                    self.idf = data["idf"]
                    self.ready = True
                    print(f"[RAG] 从缓存加载: {len(self.chunks)} 个片段")
                    return True
                except Exception:
                    pass

            files = self._scan_files()
            all_chunks = []
            for f in files:
                try:
                    chunks = self._chunk_file(f)
                    all_chunks.extend(chunks)
                except Exception as e:
                    print(f"[RAG] 跳过 {f.name}: {e}")

            self.chunks = all_chunks
            print(f"[RAG] 知识库扫描: {len(files)} 个文件, {len(all_chunks)} 个片段")

            if all_chunks:
                self._build_index()
                self.ready = True
                try:
                    with open(INDEX_CACHE, "wb") as f:
                        pickle.dump({
                            "chunks": self.chunks,
                            "doc_vectors": self.doc_vectors,
                            "idf": self.idf,
                        }, f)
                except Exception:
                    pass

            return self.ready

    def query(self, question: str, top_k: int = 5) -> dict:
        """问答入口"""
        if not self.ready and not self.load_knowledge_base():
            return {"ok": False, "error": "知识库加载失败"}

        # 计算问题向量
        q_tokens = _tokenize(question)
        q_tf = Counter(q_tokens)
        q_vec = {}
        for word, tf in q_tf.items():
            if word in self.idf:
                q_vec[word] = (1 + math.log(tf)) * self.idf[word]

        # 余弦相似度
        scores = []
        q_norm = math.sqrt(sum(v * v for v in q_vec.values()))
        if q_norm == 0:
            return {"ok": True, "answer": "问题太短或不明确，请详细描述你想了解的粗趣信息。", "sources": []}

        for doc_vec in self.doc_vectors:
            dot = sum(q_vec.get(w, 0) * doc_vec.get(w, 0) for w in set(q_vec) & set(doc_vec))
            d_norm = math.sqrt(sum(v * v for v in doc_vec.values()))
            if d_norm == 0:
                scores.append(0)
            else:
                scores.append(dot / (q_norm * d_norm))

        # 取 top_k
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        # 过滤低分
        context_parts = []
        seen_sources = set()
        for idx in top_indices:
            if scores[idx] < 0.05:
                continue
            chunk = self.chunks[idx]
            source_short = "/".join(Path(chunk["source"]).parts[-3:])
            context_parts.append(f"【{chunk['title']}】\n{chunk['content']}")
            seen_sources.add(source_short)

        if not context_parts:
            return {"ok": True, "answer": "知识库中暂未找到相关信息，你可以换个问法试试。", "sources": []}

        context = "\n\n---\n\n".join(context_parts)

        result = self._call_llm(question, context)

        if result.get("ok"):
            return {
                "ok": True,
                "answer": result["content"],
                "sources": list(seen_sources)[:3],
            }
        return {"ok": False, "error": result.get("error", "LLM 调用失败")}

    def status(self) -> dict:
        return {"ready": self.ready, "chunks": len(self.chunks)}

    # ── 索引 ──

    def _build_index(self):
        """构建 TF-IDF 索引"""
        # 所有文档的分词结果
        all_tokens = []
        for chunk in self.chunks:
            tokens = _tokenize(chunk["content"])
            all_tokens.append(tokens)

        # 计算 IDF
        n_docs = len(all_tokens)
        word_df: Counter = Counter()
        for tokens in all_tokens:
            word_df.update(set(tokens))

        self.idf = {}
        for word, df in word_df.items():
            self.idf[word] = math.log((n_docs + 1) / (df + 1)) + 1

        # 计算每篇文档的 TF-IDF 向量
        self.doc_vectors = []
        for tokens in all_tokens:
            tf = Counter(tokens)
            vec = {}
            for word, freq in tf.items():
                if word in self.idf:
                    vec[word] = (1 + math.log(freq)) * self.idf[word]
            self.doc_vectors.append(vec)

    # ── 文件扫描与分块 ──

    def _scan_files(self) -> list[Path]:
        files = []
        cuxi_dir = CUXI_KB_DIR / "粗趣"
        if cuxi_dir.is_dir():
            for f in sorted(cuxi_dir.rglob("*.md")):
                if "分析报告" in str(f) or "过程文件" in str(f):
                    continue
                files.append(f)
        notes_dir = CUXI_KB_DIR / "粗趣丨蛋仔小助手_笔记"
        if notes_dir.is_dir():
            for f in sorted(notes_dir.rglob("*.txt")):
                files.append(f)
            for f in sorted(notes_dir.rglob("正文.md")):
                files.append(f)
        skill_file = cuxi_dir / "创作指南.skill" / "SKILL.md" if cuxi_dir.is_dir() else None
        if skill_file and skill_file.is_file():
            files.append(skill_file)
        faq = cuxi_dir / "粗趣答疑帖.md"
        if faq.is_file():
            files.append(faq)
        return files

    def _chunk_file(self, filepath: Path) -> list[dict]:
        text = filepath.read_text(encoding="utf-8", errors="replace")
        chunks = []
        if filepath.suffix in (".txt",):
            text = text.strip()
            if len(text) > 30:
                chunks.append({"content": text, "source": str(filepath), "title": filepath.stem})
            return chunks
        lines = text.split("\n")
        file_title = ""
        for line in lines:
            if line.startswith("# ") and not line.startswith("## "):
                file_title = line.lstrip("# ").strip()
                break
        current_header = ""
        current_lines = []
        for line in lines:
            if line.startswith("## ") and current_lines:
                self._save_chunk(current_lines, current_header, file_title, filepath, chunks)
                current_header = line.lstrip("## ").strip()
                current_lines = [line]
            else:
                current_lines.append(line)
        if current_lines:
            self._save_chunk(current_lines, current_header, file_title, filepath, chunks)
        return chunks

    def _save_chunk(self, lines, header, file_title, filepath, chunks):
        text = "\n".join(lines).strip()
        if len(text) < 50:
            return
        title = f"{file_title} - {header}" if header else file_title
        chunks.append({"content": text, "source": str(filepath), "title": title})

    # ── LLM 调用 ──

    def _call_llm(self, question: str, context: str) -> dict:
        import requests as req
        spider_dir = ROOT_DIR / "工具类" / "博主蒸馏" / "spider_xhs"
        env_path = spider_dir / ".env"
        api_key = ""
        base_url = "https://api.deepseek.com/v1"
        if env_path.is_file():
            content = env_path.read_text(encoding="utf-8")
            m = re.search(r'^LLM_API_KEY\s*=\s*(.+)$', content, re.MULTILINE)
            if m:
                api_key = m.group(1).strip().strip("'\"").strip()
            m = re.search(r'^LLM_API_BASE\s*=\s*(.+)$', content, re.MULTILINE)
            if m:
                base_url = m.group(1).strip().strip("'\"").strip()
        if not api_key:
            return {"ok": False, "error": "API Key 未配置"}
        system_prompt = """你是一个粗趣品牌知识助手。粗趣是深圳本地社交活动平台，提供桌游、派对、户外等线下社交活动。

请根据以下知识库内容回答用户的问题。要求：
1. 只基于知识库内容回答，不要编造信息
2. 如果知识库中找不到相关信息，请说"知识库中没有相关信息"
3. 回答简洁、口语化
4. 适当引用具体的数据或例子"""
        try:
            resp = req.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": "deepseek-v4-flash",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"知识库内容：\n{context}\n\n用户问题：{question}"},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000,
                },
                timeout=60,
            )
            if resp.status_code == 401:
                return {"ok": False, "error": "API Key 无效或已过期"}
            resp.raise_for_status()
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {"ok": True, "content": content}
        except Exception as e:
            return {"ok": False, "error": str(e)}


# ── 全局单例 ──
_engine = None
_engine_lock = threading.Lock()


def get_engine() -> RAGEngine:
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = RAGEngine()
    return _engine
