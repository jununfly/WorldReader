#!/usr/bin/env python3
"""
WorldReader 简单测试
"""

import sys
import os

# 添加 lib 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from worldreader import WorldReader

def test_basic():
    """基本功能测试"""
    print("=" * 50)
    print("WorldReader 基本功能测试")
    print("=" * 50)

    # 初始化
    print("\n1. 初始化 WorldReader...")
    reader = WorldReader('./config.yaml')
    print("   ✅ 初始化成功")
    print(f"   ✅ 已注册 {len(reader.fetchers)} 个内容获取器")
    print(f"   ✅ 获取器类型: {list(reader.fetchers.keys())}")

    # 测试订阅清单解析
    print("\n2. 测试订阅清单解析...")
    test_content = """
# 测试订阅清单

## 微信公众号

| 公众号 | 特点 |
|--------|------|
| 量子位 | AI 媒体顶流 |
| 机器之心 | 学术与产业双覆盖 |

## GitHub 仓库

| 仓库 | Stars | 特点 |
|------|-------|------|
| huggingface/transformers | 130k+ | 全球最主流框架 |
"""

    result = reader.parse_subscription("test_url", test_content)
    print(f"   ✅ 解析成功，获取到 {len(result['sources'])} 个信源")

    for source in result['sources'][:3]:
        print(f"   - {source['name']} ({source['type']})")

    print(f"   ✅ 缓存状态: {result['cache_status']['is_changed']}")

    # 测试文章生成
    print("\n3. 测试文章生成...")
    test_content = {
        'id': 'test_001',
        'title': '测试文章',
        'url': 'https://example.com',
        'content': '这是一篇测试文章的内容。',
        'author': '测试作者',
        'tags': ['测试'],
        'published_at': '2026-03-27',
    }

    test_source = {
        'id': 'source_001',
        'name': '测试信源',
        'type': 'website',
    }

    article = reader.article_generator.generate(test_content, test_source)
    print(f"   ✅ 文章生成成功: {article['title']}")
    print(f"   ✅ 摘要: {article['summary'][:50]}...")

    # 测试质量评分
    print("\n4. 测试质量评分...")
    score = reader.score_article(article)
    print(f"   ✅ 评分成功: {score['overall']}")
    print(f"   ✅ 质量等级: {score['level']}")
    print(f"   ✅ 各维度评分:")
    for dim, value in score['dimensions'].items():
        print(f"     - {dim}: {value}")

    print("\n" + "=" * 50)
    print("✅ 所有测试通过！")
    print("=" * 50)

if __name__ == '__main__':
    test_basic()