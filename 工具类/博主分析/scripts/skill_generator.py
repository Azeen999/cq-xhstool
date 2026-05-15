#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创作指南生成模块
生成供 AI 使用的创作 Skill
"""
from pathlib import Path

def generate_skill(analysis_result, output_dir):
    """
    生成创作指南 Skill
    
    Args:
        analysis_result: 分析结果
        output_dir: 输出目录
    
    Returns:
        Skill 目录路径
    """
    style = analysis_result['style_summary']
    title_keywords = [k[0] for k in analysis_result['title_analysis']['keywords'][:10]]
    top_tags = [t[0] for t in analysis_result['tag_analysis']['top_tags'][:10]]
    
    # 生成 Skill 名称
    skill_name = f"{style['persona'].replace('博主', '')}_创作指南"
    skill_dir = output_dir / f"{skill_name}.skill"
    skill_dir.mkdir(exist_ok=True)
    
    # 生成 SKILL.md
    skill_content = f"""---
name: {skill_name}
description: >
  {style['persona']}风格创作指南。模仿该博主的标题风格、内容结构和标签策略进行创作。
  触发词：「写一篇{style['persona']}风格的帖子」「模仿{style['persona']}」
---

# {style['persona']}创作指南

## 一、人设定位

### 核心人设
- **定位**: {style['persona']}
- **语气**: {style['tone']}
- **视觉风格**: {style['visual_style']}

## 二、标题公式

### 常用标题模式
{''.join(f"- {pattern['patterns'][0]}：{pattern['title']}" for pattern in analysis_result['title_analysis']['patterns'][:5])}

### 高频关键词
{', '.join(title_keywords)}

### 标题技巧
- 提问式标题占比: {int(analysis_result['title_analysis']['question_ratio'] * 100)}%
- 表情符号使用: {int(analysis_result['title_analysis']['emoji_ratio'] * 100)}%

## 三、内容结构

### 正文长度
平均字数: {analysis_result['content_analysis']['avg_length']} 字

### 结构模板
1. **开头钩子**: 直接点明主题，引发好奇心
2. **正文内容**: 分点阐述，逻辑清晰
3. **结尾引导**: 引导互动或关注

## 四、标签策略

### 必带标签
{', '.join(top_tags[:5])}

### 推荐标签组合
- 主标签: {top_tags[0] if top_tags else ''}
- 辅标签: {', '.join(top_tags[1:4])}
- 话题标签: #小红书 #干货分享

## 五、发布建议

### 互动数据参考
- 平均点赞: {analysis_result['profile']['avg_likes']:,}
- 平均评论: {analysis_result['profile']['avg_comments']:,}
- 平均收藏: {analysis_result['profile']['avg_collections']:,}

### 内容方向建议
基于分析，建议创作以下类型内容：
{''.join(f"- {kw}相关内容" for kw in title_keywords[:5])}

## 六、创作示例

### 标题示例
{''.join(f"- {pattern['title']}" for pattern in analysis_result['title_analysis']['patterns'][:3])}

### 正文模板
```
【开头】直接点明主题，引发兴趣

【正文】分点阐述核心内容
- 要点一：详细说明
- 要点二：具体案例
- 要点三：总结升华

【结尾】引导互动，增加粘性
```

---

*本指南基于博主数据分析自动生成*
"""
    
    with open(skill_dir / 'SKILL.md', 'w', encoding='utf-8') as f:
        f.write(skill_content)
    
    # 生成模板文件
    template_content = f"""{{{{
  "title_patterns": {[pattern['title'] for pattern in analysis_result['title_analysis']['patterns'][:5]]},
  "keywords": {title_keywords[:10]},
  "tags": {top_tags[:10]},
  "persona": "{style['persona']}",
  "tone": "{style['tone']}"
}}}}"""
    
    with open(skill_dir / 'template.json', 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    return skill_dir

if __name__ == '__main__':
    # 测试
    test_result = {
        'profile': {'total_notes': 3, 'avg_likes': 1463, 'avg_comments': 159, 'avg_collections': 527},
        'title_analysis': {'question_ratio': 0.33, 'emoji_ratio': 0.33, 'keywords': [('干货', 2), ('教程', 2), ('分享', 1)], 'patterns': [{'title': '干货｜保姆级教程来了！', 'patterns': ['干货式', '保姆级']}]},
        'tag_analysis': {'top_tags': [('干货', 2), ('教程', 1), ('测评', 1)]},
        'content_analysis': {'avg_length': 500},
        'style_summary': {'persona': '知识干货博主', 'tone': '专业理性', 'visual_style': '图文结合'}
    }
    
    generate_skill(test_result, Path('./'))