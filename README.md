# 小红书工具箱

小红书生态工具集合，Web 界面统一操作。支持博主分析、帖子深挖、关键词搜索、文案改写、RAG 知识问答等。

## 功能

| 工具 | 说明 |
|------|------|
| **博主分析** | 采集小红书博主笔记 → 数据分析 → 生成风格报告 + 创作指南 |
| **自我诊断** | 分析自己的小红书账号风格和内容表现 |
| **帖子深挖** | 分析单条帖子的评论区情感、观点和用户画像 |
| **关键词搜索** | 按关键词搜索笔记，批量获取正文、博主信息和评论 |
| **文案改写** | 按照选定品牌风格（粗趣/薯岛/取伙/粗门）改写文案，基于 DeepSeek |
| **粗趣问答** | RAG 问答系统，基于粗趣品牌知识库（jieba 分词 + TF-IDF + DeepSeek） |

## 快速开始

### 前置依赖

- **Python 3.8+** — [python.org](https://python.org)
- **Node.js** — [nodejs.org](https://nodejs.org)（小红书 API 加密签名需要）
- **小红书 Cookie** — 浏览器登录 xiaohongshu.com 后从开发者工具 Network 中复制
- **DeepSeek API Key**（可选，用于文案改写和 RAG 问答）— [platform.deepseek.com](https://platform.deepseek.com)

### Windows 一键启动

```bash
# 1. 安装依赖
setup.bat

# 2. 配置环境
#    将 .env.example 重命名为 .env，填入 Cookie 和 API Key

# 3. 启动
start.bat
# 或
python app.py
```

浏览器打开 **http://localhost:5001**

### macOS / Linux

```bash
pip install -r requirements.txt
cd 工具类/博主蒸馏/spider_xhs && npm install && cd ../..
python app.py
```

## 项目结构

```
cq工具箱-xhs/
├── app.py                     # Web 入口（Flask，端口 5001）
├── templates/index.html       # 前端界面
├── requirements.txt           # Python 依赖
├── setup.bat / start.bat      # Windows 一键安装/启动
├── .env.example               # 环境配置模板
│
├── 工具类/
│   ├── rag_engine.py          # RAG 问答引擎（jieba + TF-IDF + DeepSeek）
│   ├── 博主蒸馏/              # 博主数据采集 + 分析脚本
│   │   ├── scripts/           #   keyword_search.py 等
│   │   └── spider_xhs/        #   小红书爬虫（含 API 封装 + JS 签名）
│   ├── 帖子深挖/              # 单条帖子评论分析
│   ├── 文案改写/              # 品牌风格改写指南
│   └── 博主分析/              # 博主风格分析
│
├── 素材库/                    # 品牌知识库（RAG 数据源 + 风格参考）
│   ├── 自我参数/              #   自有品牌资料
│   └── 博主风格/              #   竞品/参考博主分析
│
└── output/                    # 所有工具的输出结果
    ├── 关键词搜索/
    ├── 帖子深挖/
    └── 博主分析/
```

## 配置说明

在 `.env` 文件中配置（参考 `.env.example`）：

| 变量 | 必需 | 说明 |
|------|------|------|
| `COOKIES` | 是 | 小红书登录 Cookie，用于爬虫数据采集 |
| `LLM_API_KEY` | 否 | DeepSeek API Key，文案改写和 RAG 需要 |
| `LLM_API_BASE` | 否 | API 地址，默认 `https://api.deepseek.com/v1` |

## 技术栈

- **后端**: Flask, jieba (分词), TF-IDF (向量检索)
- **前端**: 原生 JS + SSE 流式日志
- **LLM**: DeepSeek API（OpenAI 兼容接口）
- **爬虫**: spider_xhs（Python + Node.js 签名）
