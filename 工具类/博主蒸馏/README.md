# 📖 博主蒸馏器

> 小红书博主内容分析工具 — 采集公开笔记 → 结构化分析 → AI 生成创作指南

采集目标博主的公开笔记，通过三层蒸馏（认知层、策略层、内容层）提炼内容公式，最终生成两份产物：

1. **HTML 蒸馏报告** — 给人看，快速理解博主的人设、策略和内容方法论
2. **创作 Skill 文件夹** — 给 AI 用，安装后说"用 XX 风格写"，AI 立刻知道怎么写

## 快速开始

### 前置要求

- **Windows**（Spider_XHS 爬虫目前仅支持 Windows）
- **Python 3.10+** — [下载](https://www.python.org/downloads/)
- **Node.js** — [下载](https://nodejs.org/)（Spider_XHS 签名引擎需要）
- **小红书 Cookie** — 登录网页版后从浏览器开发者工具获取

### 安装

```bash
# 1. 下载项目
git clone https://github.com/YOUR_ORG/blogger-distiller.git
cd blogger-distiller

# 2. 安装依赖
# Windows:
setup.bat

# macOS / Linux:
chmod +x setup.sh && ./setup.sh
```

### 配置 Cookie

1. 浏览器打开 https://www.xiaohongshu.com 并登录
2. F12 → Network → 刷新页面 → 找到任意 `xiaohongshu.com` 请求
3. 复制 Request Headers 中的 `Cookie` 完整值
4. 编辑 `spider_xhs/.env`：

```
COOKIES=你的完整 Cookie 值
```

### 启动 Web 界面

```bash
python app.py
```

打开浏览器访问 **http://localhost:5000**，三步走：

1. **采集** — 输入博主主页 URL → 选数量 → 开始采集
2. **分析** — 结构化分析笔记数据
3. **深度蒸馏** — 生成数据底稿 + AI 任务

完成后，AI 蒸馏任务文件包含了完整的分析数据，可配合 Claude Code 等 AI 工具生成最终的 HTML 报告和 Skill。

### 命令行快速运行

```bash
# 一键运行（交互式选择模式和数量）
python run.py "博主名"

# 手动分步
python scripts/spider_xhs_adapter.py --url "https://www.xiaohongshu.com/user/profile/博主ID" -o ./data --max-notes 50
python scripts/analyze.py ./data/*_notes_details.json -o ./data
python scripts/deep_analyze.py ./data/*_analysis.json "博主名" -o ./output --details ./data/*_notes_details.json --mode A
```

## 项目结构

```
blogger-distiller/
├── app.py                          # Web 界面（Flask）
├── run.py                          # 命令行一键运行
├── setup.bat / setup.sh            # 自动安装脚本
├── sanitize_data.py                # 数据脱敏工具（上传 GitHub 前使用）
├── requirements.txt                # Python 依赖
├── spider_xhs/                     # Spider_XHS 爬虫引擎（已内置）
│   ├── apis/                       #   小红书 API 封装
│   ├── static/                     #   JS 签名文件
│   ├── xhs_utils/                  #   工具函数
│   └── .env                        #   ← 你的 Cookie 配置在此
├── scripts/
│   ├── spider_xhs_adapter.py       # Phase 1: 数据采集
│   ├── analyze.py                  # Phase 2: 数据分析
│   ├── deep_analyze.py             # Phase 3: 深度蒸馏
│   └── utils/                      #   工具库
├── data/                           # 采集数据目录（gitignored）
└── output/                         # 产出物目录（gitignored）
```

## 功能说明

### 支持的操作

| 功能 | 说明 |
|------|------|
| 拆解对标博主 | 输入 URL，分析 TA 的内容公式和思维方式 |
| 诊断自己账号 | 采集自己的笔记，找到内容基因和增长瓶颈 |
| 分析评论 | 每条笔记自动采集评论（评论者身份脱敏） |

### 三层蒸馏框架

| 层级 | 回答的问题 |
|------|-----------|
| **认知层** | TA 怎么想？核心信念、价值立场、思维模式 |
| **策略层** | TA 怎么运营？系列规划、蹭热点、发布节奏 |
| **内容层** | TA 怎么写？标题公式、开头模板、视觉风格 |

### 安全与隐私

- 评论者身份默认脱敏（读者1/读者2/作者），[privacy.py](scripts/utils/privacy.py)
- Cookie 配置在 `.env` 文件中，**永远不会被提交到 git**
- 数据文件在 `data/` 和 `output/` 中，已被 `.gitignore` 排除
- 如需将示例数据上传 GitHub，先用脱敏工具：

```bash
python sanitize_data.py --output ./sanitized_demo
```

## 许可证

MIT License — 详见 [LICENSE](LICENSE)

## 免责声明

本工具仅供学习研究使用，通过 Spider_XHS 本地爬虫获取小红书**公开**数据。使用者需自行承担使用责任。完整条款见 [DISCLAIMER.md](DISCLAIMER.md)。
