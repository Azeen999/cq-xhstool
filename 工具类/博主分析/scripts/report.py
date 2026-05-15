#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML报告生成模块
生成可视化的博主分析报告
"""
def generate_html_report(analysis_result, notes, output_path):
    """
    生成HTML分析报告
    
    Args:
        analysis_result: 分析结果
        notes: 原始笔记数据
        output_path: 输出路径
    
    Returns:
        输出路径
    """
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>博主风格分析报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; padding: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #ff6b6b 0%, #ee5a9b 100%); padding: 40px; color: white; text-align: center; }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .header p {{ opacity: 0.9; }}
        .section {{ padding: 30px; border-bottom: 1px solid #eee; }}
        .section:last-child {{ border-bottom: none; }}
        .section-title {{ color: #333; font-size: 1.4em; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #ee5a9b; display: inline-block; }}
        .stat-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }}
        .stat-card {{ background: #f8f9fa; padding: 20px; border-radius: 12px; text-align: center; }}
        .stat-value {{ font-size: 2em; font-weight: bold; color: #ee5a9b; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        .tag-cloud {{ display: flex; flex-wrap: wrap; gap: 10px; }}
        .tag {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 8px 16px; border-radius: 20px; font-size: 14px; }}
        .pattern-list {{ list-style: none; }}
        .pattern-item {{ padding: 12px; background: #f8f9fa; margin-bottom: 8px; border-radius: 8px; border-left: 4px solid #ee5a9b; }}
        .note-preview {{ background: #f8f9fa; padding: 20px; border-radius: 12px; margin-bottom: 15px; }}
        .note-title {{ font-weight: bold; color: #333; margin-bottom: 8px; }}
        .note-desc {{ color: #666; line-height: 1.6; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }}
        .stats-row {{ display: flex; gap: 20px; margin-top: 10px; }}
        .stat-badge {{ background: #eee; padding: 4px 12px; border-radius: 12px; font-size: 12px; }}
        .summary-box {{ background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%); padding: 25px; border-radius: 12px; }}
        .summary-title {{ font-weight: bold; margin-bottom: 10px; color: #d63031; }}
        .summary-text {{ color: #636e72; line-height: 1.6; }}
        .keyword-item {{ display: flex; justify-content: space-between; padding: 8px 12px; background: #f8f9fa; margin-bottom: 4px; border-radius: 6px; }}
        .keyword-name {{ flex: 1; }}
        .keyword-count {{ background: #ee5a9b; color: white; padding: 2px 10px; border-radius: 10px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 博主风格分析报告</h1>
            <p>基于 {analysis_result['profile']['total_notes']} 篇笔记分析</p>
        </div>

        <div class="section">
            <h2 class="section-title">📈 基础数据</h2>
            <div class="stat-grid">
                <div class="stat-card">
                    <div class="stat-value">{analysis_result['profile']['total_notes']}</div>
                    <div class="stat-label">笔记总数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{analysis_result['profile']['avg_likes']:,}</div>
                    <div class="stat-label">平均点赞</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{analysis_result['profile']['avg_comments']:,}</div>
                    <div class="stat-label">平均评论</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{analysis_result['profile']['avg_collections']:,}</div>
                    <div class="stat-label">平均收藏</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">👤 博主画像</h2>
            <div class="summary-box">
                <div class="summary-title">🎯 人设定位</div>
                <div class="summary-text"><strong>定位：</strong>{analysis_result['style_summary']['persona']}</div>
                <div class="summary-text"><strong>语气：</strong>{analysis_result['style_summary']['tone']}</div>
                <div class="summary-text"><strong>视觉：</strong>{analysis_result['style_summary']['visual_style']}</div>
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">📝 标题分析</h2>
            <p><strong>提问式标题占比：</strong>{(analysis_result['title_analysis']['question_ratio'] * 100):.1f}%</p>
            <p><strong>带表情标题占比：</strong>{(analysis_result['title_analysis']['emoji_ratio'] * 100):.1f}%</p>
            
            <h3 style="margin: 20px 0 10px; color: #555;">热门关键词</h3>
            <div style="max-height: 200px; overflow-y: auto;">
                {''.join(f'<div class="keyword-item"><span class="keyword-name">{kw[0]}</span><span class="keyword-count">{kw[1]}</span></div>' for kw in analysis_result['title_analysis']['keywords'][:15])}
            </div>

            <h3 style="margin: 20px 0 10px; color: #555;">标题模式</h3>
            <ul class="pattern-list">
                {''.join(f'<li class="pattern-item"><strong>「{p["title"]}」</strong> - {", ".join(p["patterns"])}</li>' for p in analysis_result['title_analysis']['patterns'])}
            </ul>
        </div>

        <div class="section">
            <h2 class="section-title">🏷️ 标签策略</h2>
            <div class="tag-cloud">
                {''.join(f'<span class="tag">{tag[0]} ({tag[1]})</span>' for tag in analysis_result['tag_analysis']['top_tags'][:15])}
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">📄 内容预览</h2>
            {''.join(f'''
            <div class="note-preview">
                <div class="note-title">📌 {note.get('title', '无标题')}</div>
                <div class="note-desc">{note.get('desc', '')}</div>
                <div class="stats-row">
                    <span class="stat-badge">❤️ {note.get('liked_count', 0)}</span>
                    <span class="stat-badge">💬 {note.get('comment_count', 0)}</span>
                    <span class="stat-badge">📚 {note.get('collected_count', 0)}</span>
                </div>
            </div>
            ''' for note in notes[:5])}
        </div>
    </div>
</body>
</html>"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return output_path

if __name__ == '__main__':
    # 测试
    test_result = {
        'profile': {'total_notes': 3, 'avg_likes': 1463, 'avg_comments': 159, 'avg_collections': 527},
        'title_analysis': {'question_ratio': 0.33, 'emoji_ratio': 0.33, 'keywords': [('干货', 2), ('教程', 2), ('分享', 1)], 'patterns': [{'title': '干货｜保姆级教程来了！', 'patterns': ['干货式', '保姆级']}]},
        'tag_analysis': {'top_tags': [('干货', 2), ('教程', 1), ('测评', 1)]},
        'style_summary': {'persona': '知识干货博主', 'tone': '专业理性', 'visual_style': '图文结合'}
    }
    
    test_notes = [
        {'title': '干货｜保姆级教程来了！', 'desc': '今天给大家分享一个超实用的技巧...', 'liked_count': 1200, 'comment_count': 89, 'collected_count': 456},
        {'title': '为什么我不推荐这款产品？', 'desc': '用了三个月，说说真实感受...', 'liked_count': 890, 'comment_count': 156, 'collected_count': 234}
    ]
    
    generate_html_report(test_result, test_notes, './test_report.html')