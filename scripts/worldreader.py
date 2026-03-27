#!/usr/bin/env python3
"""
WorldReader 命令行工具
"""

import sys
import os
import argparse
import json

# 添加 lib 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.worldreader import WorldReader
from lib.utils import load_json, save_json


def parse_subscription(args):
    """解析订阅清单"""
    reader = WorldReader(config_path=args.config)

    # 获取文档内容
    content = None
    if args.content:
        # 从文件读取
        with open(args.content, 'r', encoding='utf-8') as f:
            content = f.read()
    elif args.doc_url:
        # 尝试从 URL 获取
        content = reader._fetch_subscription_content(args.doc_url)
    else:
        print("错误: 必须指定 --doc-url 或 --content")
        sys.exit(1)

    # 解析订阅清单
    result = reader.parse_subscription(args.doc_url, content)

    # 输出结果
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"获取到 {len(result.get('sources', []))} 个信源")
        print(f"缓存状态: {result.get('cache_status')}")


def fetch_content(args):
    """获取信源内容"""
    reader = WorldReader(config_path=args.config)

    articles = reader.fetch_source_content(args.source_id, args.date)

    if args.json:
        print(json.dumps(articles, ensure_ascii=False, indent=2))
    else:
        print(f"获取到 {len(articles)} 篇文章:")
        for article in articles:
            print(f"- {article['title']}")


def score_article(args):
    """评分文章"""
    reader = WorldReader(config_path=args.config)

    # 加载文章
    article = load_json(args.article_path)
    if not article:
        print(f"错误: 无法加载文章: {args.article_path}")
        sys.exit(1)

    # 评分
    score = reader.score_article(article)

    # 输出结果
    if args.json:
        print(json.dumps(score, ensure_ascii=False, indent=2))
    else:
        print(f"综合评分: {score['overall']}")
        print(f"质量等级: {score['level']}")
        print("\n各维度评分:")
        for dim, value in score['dimensions'].items():
            print(f"  - {dim}: {value}")

        if score['report'].get('strengths'):
            print("\n优点:")
            for strength in score['report']['strengths']:
                print(f"  - {strength}")

        if score['report'].get('weaknesses'):
            print("\n不足:")
            for weakness in score['report']['weaknesses']:
                print(f"  - {weakness}")

        if score['report'].get('suggestions'):
            print("\n建议:")
            for suggestion in score['report']['suggestions']:
                print(f"  - {suggestion}")


def get_daily_articles(args):
    """获取每日文章列表"""
    reader = WorldReader(config_path=args.config)

    # 先解析订阅清单
    if args.doc_url or args.content:
        content = None
        if args.content:
            with open(args.content, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = reader._fetch_subscription_content(args.doc_url)

        reader.parse_subscription(args.doc_url or "", content)

    # 获取每日文章
    result = reader.get_daily_articles(args.date, args.source_id)

    # 输出结果
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        stats = result.get('statistics', {})
        print(f"日期: {result.get('date')}")
        print(f"总文章数: {stats.get('total_articles', 0)}")
        print(f"平均质量分: {stats.get('avg_quality_score', 0)}")
        print(f"高质量: {stats.get('high_quality_count', 0)}")
        print(f"中等质量: {stats.get('medium_quality_count', 0)}")
        print(f"低质量: {stats.get('low_quality_count', 0)}")

        articles = result.get('articles', [])
        if articles:
            print("\n文章列表:")
            for item in articles:
                article = item['article']
                score = item['quality_score']
                print(f"- [{score['level']}] {article['title']} (评分: {score['overall']})")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='WorldReader - 智能知识库阅读器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 解析订阅清单
  %(prog)s parse-subscription --doc-url "https://..."

  # 获取信源内容
  %(prog)s fetch-content --source-id "source_001" --date "2026-03-27"

  # 评分文章
  %(prog)s score-article --article-path "./article.json"

  # 获取每日文章
  %(prog)s get-daily-articles --date "2026-03-27" --doc-url "https://..."
        """
    )

    parser.add_argument('--config', default='./config.yaml',
                        help='配置文件路径 (默认: ./config.yaml)')
    parser.add_argument('--json', action='store_true',
                        help='以 JSON 格式输出')

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # parse-subscription 命令
    ps_parser = subparsers.add_parser('parse-subscription', help='解析订阅清单')
    ps_parser.add_argument('--doc-url', help='订阅清单文档 URL')
    ps_parser.add_argument('--content', help='订阅清单内容文件')

    # fetch-content 命令
    fc_parser = subparsers.add_parser('fetch-content', help='获取信源内容')
    fc_parser.add_argument('--source-id', required=True, help='信源 ID')
    fc_parser.add_argument('--date', required=True, help='日期 (YYYY-MM-DD)')

    # score-article 命令
    sa_parser = subparsers.add_parser('score-article', help='评分文章')
    sa_parser.add_argument('--article-path', required=True, help='文章 JSON 文件路径')

    # get-daily-articles 命令
    gda_parser = subparsers.add_parser('get-daily-articles', help='获取每日文章列表')
    gda_parser.add_argument('--date', required=True, help='日期 (YYYY-MM-DD)')
    gda_parser.add_argument('--source-id', help='信源 ID (可选)')
    gda_parser.add_argument('--doc-url', help='订阅清单文档 URL')
    gda_parser.add_argument('--content', help='订阅清单内容文件')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 执行对应命令
    if args.command == 'parse-subscription':
        parse_subscription(args)
    elif args.command == 'fetch-content':
        fetch_content(args)
    elif args.command == 'score-article':
        score_article(args)
    elif args.command == 'get-daily-articles':
        get_daily_articles(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()