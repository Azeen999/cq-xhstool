#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书帖子深度分析器
输入帖子链接，获取正文和评论，进行情感分析和观点提取
注意：添加了延迟控制，模拟人类正常使用，避免风控
"""

import sys
import os
import re
import json
import argparse
import time
import random
import jieba
from collections import Counter

# Monkey-patch subprocess.Popen 强制 UTF-8，防止 execjs 在 GBK 系统上崩溃
import subprocess
_original_popen_init = subprocess.Popen.__init__
def _patched_popen_init(self, *args, **kwargs):
    if kwargs.get('universal_newlines') or kwargs.get('text'):
        kwargs.setdefault('encoding', 'utf-8')
        kwargs.setdefault('errors', 'replace')
    return _original_popen_init(self, *args, **kwargs)
subprocess.Popen.__init__ = _patched_popen_init

from pathlib import Path

# 添加爬虫路径（指向共享 Spider_XHS）
_SPIDER_DIR = str((Path(__file__).parent.parent.parent / '博主蒸馏' / 'spider_xhs').resolve())
sys.path.insert(0, _SPIDER_DIR)

# 强制 UTF-8 编码，防止 execjs/Node.js 子进程在 GBK 系统上崩溃
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"

from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.cookie_util import trans_cookies


def load_cookies_from_env():
    """从.env文件加载cookie"""
    env_path = os.path.join(_SPIDER_DIR, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            content = f.read()
            # 提取 COOKIES= 后面的内容（可能有引号也可能没有）
            match = re.search(r'^COOKIES\s*=\s*(.+)$', content, re.MULTILINE)
            if match:
                return match.group(1).strip().strip("'\"").strip()
    return None


def human_delay(min_s=2, max_s=5):
    """模拟人类操作的随机延迟"""
    delay = random.uniform(min_s, max_s)
    print(f"  ⏳ 等待 {delay:.1f}s...")
    time.sleep(delay)


def exponential_backoff(attempt, base_delay=1, max_delay=30):
    """指数退避，用于请求失败时重试"""
    delay = min(base_delay * (2 ** attempt), max_delay)
    jitter = random.uniform(0, 0.5 * delay)
    return delay + jitter

# 情感词库
POSITIVE_WORDS = {"好", "棒", "赞", "喜欢", "爱", "美", "棒", "绝", "推荐", "不错", "可以",
                  "值", "划算", "满意", "惊喜", "开心", "舒服", "漂亮", "优秀", "完美",
                  "厉害", "专业", "贴心", "用心", "感动", "温暖", "治愈", "种草", "回购"}

NEGATIVE_WORDS = {"差", "烂", "坑", "垃圾", "恶心", "失望", "后悔", "不值", "贵",
                  "慢", "差", "假", "骗", "糟", "麻烦", "无语", "生气", "愤怒", "投诉",
                  "避雷", "拔草", "踩雷", "翻车", "差评", "问题", "缺陷", "瑕疵", "破损"}


def extract_note_id(url):
    """从帖子链接中提取note_id（支持 /item/, /explore/, noteId= 三种格式）"""
    match = re.search(r'/(?:item|explore)/([a-f0-9]+)', url)
    if match:
        return match.group(1)
    match = re.search(r'noteId=([a-f0-9]+)', url)
    if match:
        return match.group(1)
    return None


def is_valid_comment(comment, min_likes=0, min_length=1):
    """判断评论是否有效（取消所有限制）"""
    content = comment.get("content", "").strip()
    
    # 最小长度过滤（仅过滤空评论）
    if len(content) < min_length:
        return False
    
    # 过滤纯表情评论
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           "]+", flags=re.UNICODE)
    cleaned = emoji_pattern.sub(r'', content)
    if len(cleaned.strip()) < 3:
        return False
    
    # 过滤无意义内容
    meaningless_patterns = [
        r'^\s*[666|hhh|哈哈|嘿嘿|呵呵|嗯嗯|哦哦|好的|是的|谢谢|不客气]\s*$',
        r'^\s*[表情|emoji|贴图]+\s*$',
        r'^\s*[赞|顶|支持|打卡|围观]\s*$'
    ]
    for pattern in meaningless_patterns:
        if re.match(pattern, content):
            return False
    
    return True


def analyze_sentiment(content):
    """简单的情感分析"""
    content_lower = content.lower()
    
    pos_count = sum(1 for word in POSITIVE_WORDS if word in content_lower)
    neg_count = sum(1 for word in NEGATIVE_WORDS if word in content_lower)
    
    if pos_count > neg_count:
        return "正面", max(0.3, pos_count / (pos_count + neg_count + 1))
    elif neg_count > pos_count:
        return "负面", max(0.3, neg_count / (pos_count + neg_count + 1))
    else:
        # 检查是否有疑问词
        question_words = {"？", "?", "吗", "呢", "为什么", "怎么", "如何", "哪个"}
        if any(word in content for word in question_words):
            return "提问", 0.5
        return "中性", 0.5


def extract_keywords(comments, top_n=15):
    """提取关键词（使用 jieba 分词，过滤表情符号）"""
    # 添加自定义词汇
    jieba.add_word('粗门')
    jieba.add_word('主理人')
    jieba.add_word('提现')
    jieba.add_word('客服')
    jieba.add_word('活动')
    jieba.add_word('报名')
    jieba.add_word('退款')
    
    all_text = " ".join(c.get("content", "") for c in comments)
    
    # 调试：打印前200个字符
    print(f"📝 文本预览: {all_text[:200]}...")
    
    # 移除表情符号（简化版，只移除常见emoji）
    all_text = re.sub(r'\[R\]|\[笑哭\]|\[捂脸\]|\[玫瑰\]|\[哭惹\]', '', all_text)
    
    # 使用 jieba 分词
    words = jieba.lcut(all_text)
    
    # 调试：打印分词结果
    print(f"🔤 分词结果（前20个）: {words[:20]}")
    
    # 过滤停用词、短词、纯数字和乱码（简化停用词列表）
    stop_words = {"的", "了", "和", "是", "就", "都", "而", "及", "与", "着", "或",
                  "一个", "没有", "我们", "你们", "他们", "这个", "那个", "这些", "那些",
                  "什么", "怎么", "如何", "为什么", "因为", "所以", "但是", "可是",
                  "如果", "可以", "能", "会", "要", "应该", "觉得", "认为", "知道",
                  "在", "有", "不", "也", "很", "到", "说", "去", "看", "好", "自己",
                  "这", "那", "上", "给", "当", "跟", "对", "使", "么", "比", "从",
                  "所", "然", "后", "过", "天", "下", "可", "出", "只", "又", "再",
                  "本", "把", "自", "己", "无", "被", "中", "更", "吗", "同", "哪", "它", "哦"}
    
    # 过滤（简化版）
    filtered = []
    for w in words:
        # 长度>=2，非纯数字，不在停用词中
        if len(w) >= 2 and not w.isdigit() and w not in stop_words:
            # 只保留中文和英文单词
            if re.search(r'[\u4e00-\u9fa5a-zA-Z]', w):
                filtered.append(w)
    
    counter = Counter(filtered)
    
    # 调试：打印关键词
    keywords_result = [(word, count) for word, count in counter.most_common(top_n)]
    print(f"🔍 提取到的关键词: {keywords_result}")
    
    return keywords_result


def classify_opinions(comments):
    """分类观点"""
    opinions = {
        "正面": [],
        "负面": [],
        "提问": [],
        "建议": [],
        "分享": []
    }
    
    for comment in comments:
        content = comment.get("content", "")
        sentiment, _ = analyze_sentiment(content)
        
        # 进一步分类
        if "建议" in content or "应该" in content or "可以" in content:
            opinions["建议"].append(content[:50])
        elif "分享" in content or "我也" in content or "我的" in content:
            opinions["分享"].append(content[:50])
        elif sentiment == "正面":
            opinions["正面"].append(content[:50])
        elif sentiment == "负面":
            opinions["负面"].append(content[:50])
        else:
            # 检查是否是提问
            if "？" in content or "?" in content or "吗" in content:
                opinions["提问"].append(content[:50])
            else:
                opinions["正面"].append(content[:50])
    
    return opinions


def generate_report(post_info, comments, output_file=None):
    """生成Markdown报告"""
    # 帖子信息
    title = post_info.get("title", "无标题")
    author = post_info.get("user", {}).get("nickname", "未知作者")
    likes = post_info.get("likes", 0)
    collects = post_info.get("collects", 0)
    comment_count = post_info.get("comments", 0)
    content = post_info.get("desc", "")
    
    # 过滤有效评论
    valid_comments = [c for c in comments if is_valid_comment(c)]
    sorted_comments = sorted(valid_comments, key=lambda x: x.get("likes", x.get("like_count", 0)), reverse=True)
    
    # 情感分析
    sentiment_stats = Counter()
    for c in valid_comments:
        sentiment, _ = analyze_sentiment(c.get("content", ""))
        sentiment_stats[sentiment] += 1
    
    # 调试：检查valid_comments
    if valid_comments:
        print(f"📊 有效评论数: {len(valid_comments)}")
        print(f"📝 第一条评论内容: {valid_comments[0].get('content', '')[:50]}...")
    
    # 关键词提取
    keywords = extract_keywords(valid_comments)
    
    # 观点分类
    opinions = classify_opinions(valid_comments)
    
    # 生成报告
    report_lines = []
    report_lines.append(f"# 📋 小红书帖子深度分析报告")
    report_lines.append("")
    report_lines.append(f"---")
    report_lines.append("")
    
    # 帖子信息
    report_lines.append("## 📌 帖子信息")
    report_lines.append(f"- **标题**: {title}")
    report_lines.append(f"- **作者**: {author}")
    report_lines.append(f"- **互动数据**: 👍 {likes} | ⭐ {collects} | 💬 {comment_count}")
    report_lines.append("")
    
    # 帖子正文
    report_lines.append("## 📝 帖子正文")
    report_lines.append(content)
    report_lines.append("")
    
    # 评论分析概览
    report_lines.append("## 📊 评论分析概览")
    total_valid = len(valid_comments)
    report_lines.append(f"- **总评论数**: {comment_count}")
    report_lines.append(f"- **有效评论**: {total_valid}（已过滤无意义评论）")
    
    if total_valid > 0:
        report_lines.append(f"- **情感分布**:")
        for sentiment, count in sentiment_stats.items():
            percentage = round(count / total_valid * 100, 1)
            emoji = "😊" if sentiment == "正面" else "😐" if sentiment == "中性" else "😞" if sentiment == "负面" else "❓"
            report_lines.append(f"  - {emoji} {sentiment}: {count}条 ({percentage}%)")
    report_lines.append("")
    
    # 热门评论TOP10
    report_lines.append("## 💬 热门评论 TOP10")
    for i, comment in enumerate(sorted_comments[:10], 1):
        content = comment.get("content", "")
        likes = comment.get("likes", comment.get("like_count", 0))
        sentiment, _ = analyze_sentiment(content)
        emoji = "😊" if sentiment == "正面" else "😐" if sentiment == "中性" else "😞" if sentiment == "负面" else "❓"
        report_lines.append(f"{i}. {content}")
        report_lines.append(f"   - 👍 {likes} | {emoji} {sentiment}")
        report_lines.append("")
    
    # 热词分析
    report_lines.append("## 🔥 评论热词")
    report_lines.append("| 关键词 | 出现次数 |")
    report_lines.append("|--------|----------|")
    for word, count in keywords:
        report_lines.append(f"| {word} | {count} |")
    report_lines.append("")
    
    # 观点汇总
    report_lines.append("## 🎯 用户观点汇总")
    
    if opinions["正面"]:
        report_lines.append("### 😊 正面观点")
        for i, opinion in enumerate(opinions["正面"][:5], 1):
            report_lines.append(f"- {opinion}")
        report_lines.append("")
    
    if opinions["负面"]:
        report_lines.append("### 😞 负面观点")
        for i, opinion in enumerate(opinions["负面"][:5], 1):
            report_lines.append(f"- {opinion}")
        report_lines.append("")
    
    if opinions["提问"]:
        report_lines.append("### ❓ 用户提问")
        for i, opinion in enumerate(opinions["提问"][:5], 1):
            report_lines.append(f"- {opinion}")
        report_lines.append("")
    
    if opinions["建议"]:
        report_lines.append("### 💡 改进建议")
        for i, opinion in enumerate(opinions["建议"][:5], 1):
            report_lines.append(f"- {opinion}")
        report_lines.append("")
    
    report = "\n".join(report_lines)
    
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"✅ 报告已保存到: {output_file}")
    
    return report


def main():
    parser = argparse.ArgumentParser(description="小红书帖子深度分析器")
    parser.add_argument("url", help="小红书帖子链接")
    parser.add_argument("-o", "--output", help="输出文件路径")
    parser.add_argument("--slow", action="store_true", help="启用慢速模式，更安全")
    args = parser.parse_args()
    
    # 加载cookie
    cookies_str = load_cookies_from_env()
    if not cookies_str:
        print("❌ 未找到cookie配置，请检查 .env 文件")
        sys.exit(1)
    
    # 保存当前目录，切换到Spider_XHS目录（解决crypto-js模块查找问题）
    original_cwd = os.getcwd()
    spider_xhs_dir = _SPIDER_DIR
    os.chdir(spider_xhs_dir)
    print(f"📁 切换工作目录到: {spider_xhs_dir}")
    
    xhs_apis = XHS_Apis()
    
    # 获取帖子信息（带重试机制）
    print("🔍 正在获取帖子信息...")
    post_info = None
    for attempt in range(3):
        try:
            success, msg, post_info = xhs_apis.get_note_info(args.url, cookies_str)
            if success:
                break
            print(f"⚠️ 第 {attempt+1} 次尝试失败: {msg}")
            if attempt < 2:
                delay = exponential_backoff(attempt)
                print(f"  等待 {delay:.1f}s 后重试...")
                time.sleep(delay)
        except Exception as e:
            print(f"⚠️ 第 {attempt+1} 次尝试异常: {e}")
            if attempt < 2:
                delay = exponential_backoff(attempt)
                print(f"  等待 {delay:.1f}s 后重试...")
                time.sleep(delay)
    
    if not post_info or not success:
        print(f"❌ 获取帖子信息失败: {msg}")
        sys.exit(1)
    
    print(f"✅ 获取帖子成功: {post_info.get('title', '无标题')}")
    
    # 模拟人类阅读帖子的延迟
    print("📖 模拟阅读帖子中...")
    read_time = random.uniform(3, 8) if args.slow else random.uniform(1, 3)
    print(f"  ⏳ 阅读中 {read_time:.1f}s...")
    time.sleep(read_time)
    
    # 获取评论（带重试机制）
    print("🔍 正在获取评论...")
    comments = []
    for attempt in range(3):
        try:
            # 评论请求前的延迟
            comment_delay = random.uniform(2, 4) if args.slow else random.uniform(1, 2)
            print(f"  ⏳ 准备获取评论，等待 {comment_delay:.1f}s...")
            time.sleep(comment_delay)
            
            success, msg, comments = xhs_apis.get_note_all_comment(args.url, cookies_str)
            if success:
                break
            print(f"⚠️ 第 {attempt+1} 次获取评论失败: {msg}")
            if attempt < 2:
                delay = exponential_backoff(attempt)
                print(f"  等待 {delay:.1f}s 后重试...")
                time.sleep(delay)
        except Exception as e:
            print(f"⚠️ 第 {attempt+1} 次获取评论异常: {e}")
            if attempt < 2:
                delay = exponential_backoff(attempt)
                print(f"  等待 {delay:.1f}s 后重试...")
                time.sleep(delay)
    
    if not success:
        print(f"⚠️ 获取评论失败: {msg}")
        comments = []
    else:
        # 提取嵌套的二级评论
        all_comments = []
        for comment in comments:
            all_comments.append(comment)
            # 检查是否有二级评论
            if 'sub_comments' in comment and comment['sub_comments']:
                for sub_comment in comment['sub_comments']:
                    # 添加二级评论，标记来源
                    sub_comment['is_sub'] = True
                    all_comments.append(sub_comment)
        comments = all_comments
        print(f"✅ 获取评论成功: {len(comments)}条 (包含二级评论)")
    
    # 恢复原工作目录（确保输出文件路径正确）
    os.chdir(original_cwd)
    print(f"📁 恢复工作目录到: {original_cwd}")
    
    # 生成报告
    print("📝 正在生成分析报告...")
    report = generate_report(post_info, comments, args.output)
    
    # 打印摘要
    print("\n" + "="*60)
    print("📋 分析报告摘要")
    print("="*60)
    # 只打印前20行
    for line in report.split("\n")[:30]:
        print(line)
    if len(report.split("\n")) > 30:
        print("...（更多内容请查看完整报告）")


if __name__ == "__main__":
    main()
