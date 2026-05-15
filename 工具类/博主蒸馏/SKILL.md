---
name: blogger-distiller
description: >
  Use when the user wants to analyze or distill a blogger/account on Xiaohongshu,
  benchmark a target creator, or diagnose their own content strategy.
  Trigger on requests such as “拆解博主””蒸馏博主””分析小红书博主”
  “诊断我的账号””对标账号””内容策略分析””小红书账号分析”
  “分析封面””升级我的skill”.
---

# 博主蒸馏器

> ⚠️ **使用前必读**：本工具仅供学习研究使用，通过本地爬虫 Spider_XHS 获取小红书公开数据（需要有效的小红书 Cookie）。评论者身份默认脱敏（读者1 / 读者2 / 作者），评论正文保留用于研究。完整条款见 [DISCLAIMER.md](./DISCLAIMER.md) · 安全策略见 [SECURITY.md](./SECURITY.md)。

## ⛔ 执行前铁律（优先级高于一切）

触发蒸馏任务前，以下信息必须由用户**明确说出**，缺一不可：
- 模式（A 拆解对标博主 / B 诊断自己账号）
- 采集数量（30 / 50 / 80）
- 模式 A 时：博主主页 URL 或博主 ID

**注意：本工具仅支持小红书，不支持抖音。** 不需要讨论平台选择。

**「跑/分析/拆解 博主X」不等于模式 A。** 即使用户分析的是他人账号，也必须询问模式，不得推断。

用户已明确说出的项可直接采用，未说出的必须逐一询问后再执行。

---

## 你是什么

自动化的博主蒸馏工具（小红书）。**输入一个博主名字，输出两样最终产物：**

1. **HTML 蒸馏报告** — 给人看。浏览器打开，快速理解这个博主的人设、认知层、策略层和内容层。
2. **创作 Skill 文件夹** — 给 AI 用。安装后说"用 XX 风格写一篇笔记"，AI 立刻知道怎么写。

模式 A 用来拆解对标博主（学 TA），模式 B 用来诊断自己的账号（看自己）。

核心理念：**脚本保下限，AI 冲上限。** 脚本负责数据采集和确定性分析，AI 负责蒸馏洞察和生成最终产物。

---

## 能力范围

采集目标博主笔记数据（支持 30 / 50 / 80 三档），三层蒸馏产出：

### 三层蒸馏结构

| 层级 | 回答什么 | 举例 |
|------|---------|------|
|  **认知层** | TA 怎么想？ | 核心信念 / 观点张力 / 价值立场 / 思维模式 |
|  **策略层** | TA 怎么运营？ | 系列规划 / 蹭热点方式 / 运营习惯 / 发布节奏 |
|  **内容层** | TA 怎么写？ | 标题公式 / 开头模板 / CTA / 视觉风格 / 标签策略 |

### 产出物一：HTML 蒸馏报告（10 个模块）

1.  一眼看清（摘要卡片）
2. 人设拆解
3. 认知层：TA 怎么想
4. 策略层：TA 怎么运营
5. TOP10 爆款拆解
6. 内容公式速查
7. 选题灵感 TOP15
8. 数据面板（基础展开，详细折叠）
9. 发展趋势（附置信度标注）
10. 核心结论

### 产出物二：创作 Skill 文件夹

- 模式 A：`{博主名}_创作指南.skill/SKILL.md`
- 模式 B：`{用户名}_创作基因.skill/SKILL.md`
- 8 大章节：使用说明 → 认知层 → 策略层 → 内容层 → 创作禁区 → 对比示例 → 选题灵感 → 局限性+自检清单

### 分工

**脚本做 30%**（保下限）：
- 环境检查、Spider_XHS 数据采集
- 统计分析（11种标题模式、6类CTA、藏赞比、发布频率）
- 认知层粗提取（观点句候选、思维模式统计、价值词）
- 数据底稿 + AI 蒸馏任务生成

**AI 做 70%**（冲上限）：
- 生成 HTML 蒸馏报告
- 生成创作 Skill 文件夹
- 抽取信念、张力、框架、创作禁区、对比示例
- 因果分析、个性化建议、金句总结

---

## 前置要求

- Python 3.10+（Skill 会自动检测，如未安装会提示）
- **本地爬虫**：`spider_xhs/`（项目自带，参考 Spider_XHS）
- **小红书 Cookie**：配置在 `spider_xhs/.env` 文件中
- Node.js（Spider_XHS 签名依赖，需安装）
- 网络连接（用于访问小红书 API）
- **不需要** TikHub Token 或任何第三方 API 费用

---

## 执行流程

### Phase 0: 环境检查

检查以下依赖项：

1. **Python 版本** — 确认 Python 3.10+
2. **Spider_XHS 目录** — 确认 `spider_xhs/` 目录存在
3. **.env Cookie** — 确认 `spider_xhs/.env` 存在且包含有效 Cookie
4. **Node.js** — 确认已安装（Spider_XHS 签名依赖）
5. **python-docx** — 检测到未安装时自动 `pip install python-docx`

> 💡 **Cookie 过期提示**：小红书 Cookie 会定期过期，如采集时返回 401/403，需要更新 `D:\myproj\tools\Spider_XHS\.env` 中的 Cookie。

### Phase 0.5: 前置交互

**⚠️ 缺失信息必须明确询问**：以下信息，用户未在触发指令中明确提供的，必须逐一询问，不得自行推断：
- 模式（A 拆解对标博主 / B 诊断自己账号）
- 采集数量（30 / 50 / 80）
- 模式 A 时：博主主页 URL 或博主 ID

用户已明确提供的信息可以直接采用，无需重复询问。

**注意：本工具使用本地爬虫 Spider_XHS 采集数据，需要小红书 Cookie。目前仅支持小红书，不支持抖音。**

未提供的信息，参照以下交互文案询问：

```text
─────────────────────────────────────
欢迎使用博主蒸馏器！

请选择分析模式：

   A — 拆解对标博主
      采集 TA 的笔记 → 提炼内容公式和思维方式
      → 生成「TA的名字_创作指南.skill/」
      以后写内容时加载它，相当于随时在线的内容教练

  B — 诊断我的账号
      采集你的笔记 → 找到内容基因和增长瓶颈
      → 生成「你的名字_创作基因.skill/」
      让 AI 写出的内容像你自己写的，无缝嵌入创作工作流

   C — 对标 + 借鉴（暂未开放）

请输入 A 或 B：

采集数量（推荐 50 条）：
  ① 30 条 — 快速扫描（约 30 分钟）
  ② 50 条 — 推荐档位（约 45-60 分钟）
  ③ 80 条 — 深度分析（约 60-90 分钟）

每 10 条自动存盘，中断了下次继续。
─────────────────────────────────────
```

**模式 A（拆解对标博主）** — 需要博主主页 URL：
```
打开小红书 PC 端 → 进入博主主页 → 复制浏览器地址栏的完整 URL
URL 格式：https://www.xiaohongshu.com/user/profile/{user_id}
```

如果用户不知道如何获取 URL，可以手动输入博主 ID（19-25位十六进制字符）。

**模式 B（诊断自己账号）** — 无需提供 ID，爬虫会自动获取当前登录账号的信息。

记录变量供后续流程使用：

- `user_mode`：`A` 或 `B`
- `max_notes`：`30` / `50` / `80`
- `user_id`：（模式 A）博主 ID
- `profile_url`：（模式 A）博主主页 URL（可选）

### Phase 1: 数据采集（Spider_XHS 本地爬虫）

**模式 A（拆解对标博主）**：
```bash
python scripts/spider_xhs_adapter.py --url "<profile_url>" --max-notes <max_notes> --output ./data
```

如果只有博主 ID：
```bash
python scripts/spider_xhs_adapter.py --user-id <user_id> --max-notes <max_notes> --output ./data
```

**模式 B（诊断自己账号）**：
```bash
python scripts/spider_xhs_adapter.py --self --max-notes <max_notes> --output ./data
```

**⚠️ 重要约束：**
- 不得修改 `--max-notes` 参数的值，必须沿用用户在 Phase 0.5 选定的数量。
- 必须使用 `scripts/spider_xhs_adapter.py`，不得自行编写替代脚本。
- 请勿在采集过程中手动中断（有 checkpoint 保护）。

**⚠️ 采集失败的常见原因：**
- **Cookie 过期** — 小红书 Cookie 通常有效期约 1-7 天，过期后需更新 `spider_xhs/.env`
- **采集间隔太短** — 爬虫内置 15-60 秒随机延迟，如频繁失败可适当增加
- **用户主页设为私密** — 部分用户可能设置了隐私保护

**自动完成：**

1. **读取 Cookie** — 从 `spider_xhs/.env` 加载小红书 Cookie
2. **获取笔记列表** — 调用小红书 API 获取用户笔记列表（支持翻页）
3. **逐条获取笔记详情** — 含正文、互动数据、标签
4. **获取评论** — 每条笔记的评论区
5. **格式转换** — 自动转换为蒸馏器兼容的 JSON 格式

**采集时间参考**：
- 30 条：约 15-30 分钟（含随机延迟）
- 50 条：约 30-50 分钟
- 80 条：约 50-80 分钟

> 💡 爬虫内置了 15-60 秒的随机延迟以降低风控风险，耐心等待即可。

输出文件（JSON）：
- `{博主名}_notes_details.json` — 全量笔记详情（含评论、互动数据）

### Phase 2: 数据分析 + 认知层提取

运行 `python scripts/analyze.py ./data/<博主名>_notes_details.json -o ./data`

自动完成：

1. **数据清洗** — 解析 JSON，提取标题 / 正文 / 互动数据 / 评论 / 标签
2. **内容分类** — 基于笔记标签和高频关键词动态聚类，不预设任何领域
3. **标签统计** — 提取所有 `#` 话题标签，按频次排序 TOP20
4. **TOP10 + 评论洞察** — 高赞前 10 条的详情 + 热评精选
5. **认知层粗提取** — 观点句候选 / 高频价值词 / 写作结构统计
6. **[可选] 对比分析** — 自己 vs 目标博主的数据差异

输出文件：

- `{博主名}_analysis.json` — 结构化分析数据（含完整笔记列表、分类、观点句候选、高频价值词等）

### Phase 3: 蒸馏 + 产出物生成

#### Step A：生成数据底稿和 AI 蒸馏任务

运行：

```bash
python scripts/deep_analyze.py ./data/<博主名>_analysis.json "<博主名>" \
  -o ./output --details ./data/<博主名>_notes_details.json --mode <user_mode>
```

脚本自动完成：

1. **基础统计面板** — 均赞 / 均藏 / 均评 / 爆款率 / 视频 vs 图文 / 藏赞比
2. **标题模式识别** — 11 种标题策略的使用比例和示例
3. **内容结构分析** — 正文长度分布、列表率、小标题率
4. **CTA 提取**
5. **Emoji 视觉分析**
6. **发布频率**
7. **发展趋势数据**
8. **观点句候选 / 高频价值词 / 写作结构**
9. **TOP10 数据包**
10. **AI 蒸馏任务**

脚本产出：

- `{博主名}_数据底稿.md`
- `{博主名}_AI蒸馏任务.md`

#### Step B：AI 读取蒸馏任务，生成最终产物

AI 必须读取 `AI蒸馏任务.md`，按以下顺序生成最终交付物，**每完成一个立即写入磁盘，不等另一个完成**：

1. **Skill 文件夹**（先）
   - 模式 A：`{博主名}_创作指南.skill/SKILL.md`
   - 模式 B：`{用户名}_创作基因.skill/SKILL.md`
   - 生成完毕后立即写入文件，再继续步骤 2

2. **HTML 报告**（后）
   - 文件名：`{博主名}_蒸馏报告.html`
   - 技术要求：单文件 HTML，手写 CSS（禁止 Tailwind CDN），Google Fonts 引入 Space Mono + Noto Serif SC
   - 设计风格：Archive Terminal（工业档案感）；底色 #CEC9C0，主强调色 #8A3926，正文 #1A1211
   - 无圆角、无阴影、无白色卡片；模块1/8/10 为砖红色反转背景
   - 三个动效：滚动 fadeInUp / 数字 counter / 分割线 draw-in（原生 JS）
   - 折叠面板用 `<details><summary>` 原生 HTML；响应式，移动端断点 768px
   - 字号系统：标签/元数据层 11-13px，正文内容层 14-16px，统计大数字 20px（详见 AI蒸馏任务.md 字号系统表）
   - 详细视觉规格见 `AI蒸馏任务.md` 的"技术要求"章节
   - 生成完毕后立即写入文件

**⚠️ 关键契约：**
- 最终 Skill 不是单个 `.skill.md` 文件
- 最终 Skill 是一个可安装的文件夹
- 文件夹中至少必须有 `SKILL.md`
- 小红书适用以上顺序，不得颠倒

### Phase 4: 质量检查

运行校验时，最终产物应按以下口径验收：

- `{博主名}_蒸馏报告.html`
- `{博主名}_创作指南.skill/SKILL.md`

模式 B 时，将第二项替换为：

- `{用户名}_创作基因.skill/SKILL.md`

如果最终产物缺失、为空、或 AI 仍输出成单个 `.skill.md` 文件，都视为不合格。

---

## Spider_XHS 使用说明

Spider_XHS 是本地爬虫工具，通过小红书 PC API 采集公开数据。无需第三方 API Token，只需要有效的小红书 Cookie。

### Cookie 配置

在 `spider_xhs/.env` 文件中配置：
```
COOKIES=你的小红书Cookie
```

**Cookie 获取方法**：
1. 在浏览器（Chrome/Edge）中登录小红书网页版
2. 按 F12 打开开发者工具 → Network 标签
3. 刷新页面，找到任意 `xiaohongshu.com` 的请求
4. 在 Request Headers 中找到 `Cookie:` 字段，复制完整值

### 采集注意

- **采集间隔**：爬虫内置 15-60 秒随机延迟，避免触发风控
- **Cookie 有效期**：通常 1-7 天，过期后需要重新获取
- **采集耗时**：30 条约 15-30 分钟，50 条约 30-50 分钟，80 条约 50-80 分钟
- **断点恢复**：每 10 条自动保存 checkpoint，意外中断后可以继续

---

## 文件结构

```text
blogger-distiller/
├── SKILL.md                  # 你现在看的这个文件
├── run.py                    # 一键运行入口（串联 Phase 0→4）
├── install.py                # 自动安装脚本
├── scripts/
│   ├── check_env.py            # Phase 0: 环境检查
│   ├── spider_xhs_adapter.py     # Phase 1: 小红书采集（Spider_XHS 本地爬虫）
│   ├── spider_xhs_adapter.py   # Phase 1: 小红书采集（Spider_XHS 版，默认）
│   ├── analyze.py              # Phase 2: 数据分析 + 认知层粗提取
│   ├── deep_analyze.py         # Phase 3: 数据底稿 + AI 蒸馏任务
│   ├── verify.py               # Phase 4: 数据校验模块
│   └── utils/
│       ├── common.py           # 共用工具函数
│       └── quality.py          # 数据质量检查工具
└── references/
    └── 产出物质量标杆.md
```

---

## 使用方式

### 自然语言触发（推荐）

直接对 AI 说：

```text
拆解博主 <目标博主名>
```

AI 必须先执行 Phase 0.5 前置交互，再继续后面的流程。

### 一键运行

```bash
cd blogger-distiller/
python run.py "<博主名>"
```

运行后必须先完成：

1. 模式 A / B 选择
2. 数量 30 / 50 / 80 选择

然后再进入采集、分析、蒸馏。

### 手动分步执行（Spider_XHS 版）

```bash
cd blogger-distiller/

# Phase 0: 环境检查（Python + Cookie + Node.js）
python scripts/check_env.py

# Phase 1: 采集博主数据（Spider_XHS 本地爬虫）
# 模式 A：用博主主页 URL
python scripts/spider_xhs_adapter.py --url "https://www.xiaohongshu.com/user/profile/博主ID" -o ./data --max-notes 50

# 模式 A：用博主 ID
python scripts/spider_xhs_adapter.py --user-id 博主ID -o ./data --max-notes 50

# 模式 B：诊断自己账号
python scripts/spider_xhs_adapter.py --self -o ./data --max-notes 50

# Phase 2: 数据分析
python scripts/analyze.py ./data/<博主名>_notes_details.json -o ./data

# Phase 3 Step A: 生成数据底稿和 AI 蒸馏任务
python scripts/deep_analyze.py ./data/<博主名>_analysis.json "<博主名>" \
  -o ./output --details ./data/<博主名>_notes_details.json --mode <user_mode>
```

**注意：**
- `spider_xhs_adapter.py` 需要同级 `spider_xhs/` 目录（即 Spider_XHS 工具）和有效的 Cookie
- `analyze.py` 和 `deep_analyze.py` 用法不变，仍然可用

---

## 多平台兼容性

| 平台 | 本机运行 | Python | 文件读写 | 测试状态 |
|------|---------|--------|---------|---------|
| Claude Code | ✅ | ✅ | ✅ | ✅ 已验证 |
| OpenClaw (本地) | ✅ | ✅ | ✅ | ✅ 已验证 |

> ⚠️ Spider_XHS 依赖 Node.js（签名）和本地 Cookie，目前仅支持本地/桌面环境运行。

---

## 参考文档

- `references/产出物质量标杆.md` — 可作为产出结构和质量上限参考；若与当前 HTML / Skill 文件夹契约冲突，以本文件和操作手册为准

---

## 拓展玩法（蒸馏完成后可选）

蒸馏完成后，以下进阶分析可按需触发，说出触发词即可执行：

| 玩法 | 触发词 | 说明 |
|------|--------|------|
| 🎨 封面视觉风格分析 | 「分析封面」 | 分析封面色彩、构图、文字风格，给出优化建议（双平台，零额外 API） |
| 📈 关键词趋势洞察 | 「关键词趋势」 | 小红书：热搜匹配+联想词方向 |
| 🔄 已有蒸馏升级 | 「升级我的 skill」 | 在已有蒸馏基础上追加新维度，无需重新采集 |
