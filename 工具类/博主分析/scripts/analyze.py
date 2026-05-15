#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
博主风格分析模块
分析博主的标题模式、正文结构、标签策略等
"""
import re
from collections import Counter
import jieba

# 添加自定义词汇
jieba.add_word('小红书')
jieba.add_word('干货')
jieba.add_word('分享')
jieba.add_word('教程')
jieba.add_word('测评')
jieba.add_word('vlog')
jieba.add_word('ootd')
jieba.add_word('探店')

def analyze_blogger_style(notes):
    """
    分析博主风格
    
    Args:
        notes: 笔记列表
    
    Returns:
        分析结果字典
    """
    result = {
        'profile': {
            'total_notes': len(notes),
            'avg_likes': 0,
            'avg_comments': 0,
            'avg_collections': 0
        },
        'title_analysis': {
            'patterns': [],
            'keywords': [],
            'question_ratio': 0,
            'emoji_ratio': 0
        },
        'content_analysis': {
            'avg_length': 0,
            'paragraph_count': [],
            'common_structures': []
        },
        'tag_analysis': {
            'top_tags': [],
            'tag_count_dist': []
        },
        'style_summary': {
            'persona': '',
            'tone': '',
            'visual_style': ''
        }
    }

    if not notes:
        return result

    # 基础数据统计
    likes = [int(n.get('liked_count', 0)) for n in notes]
    comments = [int(n.get('comment_count', 0)) for n in notes]
    collections = [int(n.get('collected_count', 0)) for n in notes]
    
    result['profile']['avg_likes'] = int(sum(likes) / len(likes)) if likes else 0
    result['profile']['avg_comments'] = int(sum(comments) / len(comments)) if comments else 0
    result['profile']['avg_collections'] = int(sum(collections) / len(collections)) if collections else 0

    # 标题分析
    titles = [n.get('title', '') for n in notes if n.get('title')]
    result['title_analysis']['question_ratio'] = sum(1 for t in titles if '？' in t or '?' in t) / len(titles) if titles else 0
    result['title_analysis']['emoji_ratio'] = sum(1 for t in titles if re.search(r'[\u2600-\u26FF\u2700-\u27BF\U0001F300-\U0001F5FF]', t)) / len(titles) if titles else 0
    
    # 提取标题关键词
    title_keywords = []
    for title in titles:
        words = jieba.lcut(title)
        title_keywords.extend([w for w in words if len(w) >= 2 and not w.isdigit()])
    
    result['title_analysis']['keywords'] = [(k, v) for k, v in Counter(title_keywords).most_common(20)]
    
    # 识别标题模式
    result['title_analysis']['patterns'] = identify_title_patterns(titles)

    # 正文分析
    descs = [n.get('desc', '') for n in notes if n.get('desc')]
    result['content_analysis']['avg_length'] = int(sum(len(d) for d in descs) / len(descs)) if descs else 0
    
    # 标签分析
    all_tags = []
    for note in notes:
        tags = note.get('tags', []) or note.get('tag_list', [])
        if isinstance(tags, list):
            for t in tags:
                if isinstance(t, dict):
                    all_tags.append(t.get('name', ''))
                elif isinstance(t, str):
                    all_tags.append(t)
        elif isinstance(tags, str):
            all_tags.append(tags)
    
    result['tag_analysis']['top_tags'] = [(k, v) for k, v in Counter(all_tags).most_common(20)]

    # 风格总结
    result['style_summary'] = generate_style_summary(result)

    return result

def identify_title_patterns(titles):
    """识别标题模式"""
    patterns = []
    
    pattern_matchers = [
        (r'^如何', '如何式'),
        (r'^为什么', '为什么式'),
        (r'^分享', '分享式'),
        (r'^测评', '测评式'),
        (r'^推荐', '推荐式'),
        (r'^避雷', '避雷式'),
        (r'^干货', '干货式'),
        (r'^保姆级', '保姆级'),
        (r'^新手', '新手向'),
        (r'^教程', '教程式'),
        (r'.*攻略$', '攻略式'),
        (r'.*清单$', '清单式'),
        (r'.*合集$', '合集式'),
        (r'.*vlog$', 'Vlog式'),
        (r'.*OOTD.*', 'OOTD'),
        (r'.*探店.*', '探店'),
        (r'.*好物.*', '好物推荐'),
        (r'^\d+', '数字开头'),
        (r'^【', '括号标题'),
        (r'！$', '感叹结尾'),
        (r'？$', '疑问结尾'),
    ]
    
    for title in titles[:10]:  # 分析前10篇
        matched = []
        for pattern, name in pattern_matchers:
            if re.search(pattern, title):
                matched.append(name)
        if matched:
            patterns.append({'title': title, 'patterns': matched})
    
    return patterns

def generate_style_summary(result):
    """生成风格总结"""
    persona = ""
    tone = ""
    visual_style = ""
    
    keywords = [k[0] for k in result['title_analysis']['keywords'][:10]]
    
    # 确定人设
    if any(k in ['干货', '教程', '保姆级'] for k in keywords):
        persona += "知识干货博主 "
    if any(k in ['测评', '好物', '推荐'] for k in keywords):
        persona += "好物测评博主 "
    if any(k in ['vlog', '日常', '生活'] for k in keywords):
        persona += "生活记录博主 "
    if any(k in ['穿搭', 'OOTD', '时尚'] for k in keywords):
        persona += "时尚穿搭博主 "
    if any(k in ['探店', '美食', '旅行'] for k in keywords):
        persona += "探店/旅行博主 "
    if not persona:
        persona = "综合内容博主"
    
    # 确定语气
    question_ratio = result['title_analysis']['question_ratio']
    emoji_ratio = result['title_analysis']['emoji_ratio']
    
    if emoji_ratio > 0.5:
        tone = "活泼可爱"
    elif question_ratio > 0.3:
        tone = "互动提问"
    else:
        tone = "专业理性"
    
    # 视觉风格（基于笔记类型推断）
    visual_style = "图文结合"
    
    return {
        'persona': persona.strip(),
        'tone': tone,
        'visual_style': visual_style
    }

if __name__ == '__main__':
    # 测试数据
    test_notes = [
        {'title': '干货｜保姆级教程来了！', 'desc': '今天给大家分享一个超实用的技巧...', 'liked_count': 1200, 'comment_count': 89, 'collected_count': 456, 'tags': ['干货', '教程', '保姆级']},
        {'title': '为什么我不推荐这款产品？', 'desc': '用了三个月，说说真实感受...', 'liked_count': 890, 'comment_count': 156, 'collected_count': 234, 'tags': ['测评', '避雷']},
        {'title': '分享我的私藏清单✨', 'desc': '整理了很久的清单，希望对大家有帮助...', 'liked_count': 2300, 'comment_count': 234, 'collected_count': 890, 'tags': ['分享', '清单']}
    ]
    
    result = analyze_blogger_style(test_notes)
    print(json.dumps(result, ensure_ascii=False, indent=2))