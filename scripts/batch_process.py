#!/usr/bin/env python3
"""
WorldReader 批量处理脚本
获取信源内容、评分、过滤、保存到 Obsidian
"""

import sys
import os
import argparse
import json
from datetime import datetime

# 添加 lib 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from worldreader import WorldReader
from scorers.quality_scorer import QualityScorer
from obsidian_saver import ObsidianSaver
import yaml


def filter_by_quality(score: Dict, min_score: int = 60) -> bool:
    """
    根据质量评分过滤文章

    Args:
        score: 评分字典
        min_score: 最低分数阈值

    Returns:
        True 表示通过，False 表示丢弃
    """
    overall = score.get('overall', 0)
    return overall >= min_score


def batch_process(
    sources: list,
    date: str,
    min_score: int = 60,
    save_to_obsidian: bool = False,
    obsidian_vault: str = None,
    config_path: str = './config.yaml'
) -> dict:
    """
    批量处理文章

    Args:
        sources: 信源列表
        date: 目标日期 (YYYY-MM-DD)
        min_score: 最低质量分数
        save_to_obsidian: 是否保存到 Obsidian
        obsidian_vault: Obsidian Vault 路径
        config_path: 配置文件路径

    Returns:
        处理结果统计
    """
    print(f"开始批量处理: {len(sources)} 个信源")
    print(f"目标日期: {date}")
    print(f"最低质量分数: {min_score}")
    
    # 初始化
    reader = WorldReader(config_path=config_path)
    scorer = QualityScorer(yaml.safe_load(open(config_path)))
    
    obsidian_saver = None
    if save_to_obsidian and obsidian_vault:
        obsidian_saver = ObsidianSaver(obsidian_vault)
        print(f"Obsidian Vault: {obsidian_vault}")

    # 统计
    stats = {
        'total': len(sources),
        'fetched': 0,
        'passed': 0,
        'discarded': 0,
        'saved': 0,
        'failed': 0,
        'errors': []
    }

    # 处理每个信源
    for i, source in enumerate(sources, 1):
        print(f"\n[{i}/{len(sources)}] 处理信源: {source.get('name', '未知')}")
        
        try:
            # 获取内容
            articles = reader.fetch_content(source.get('id'), date)
            
            if not articles:
                print(f"  ⚠️  未获取到文章")
                stats['errors'].append({
                    'source': source.get('name'),
                    'error': '未获取到文章'
                })
                continue
            
            stats['fetched'] += len(articles)
            
            # 处理每篇文章
            for article in articles:
                article_title = article.get('title', '无标题')
                print(f"  📄 {article_title}")
                
                try:
                    # 评分
                    score = scorer.score(article)
                    overall = score.get('overall', 0)
                    level = score.get('level', 'unknown')
                    
                    print(f"     评分: {overall}/100 ({level})")
                    
                    # 过滤
                    if not filter_by_quality(score, min_score):
                        print(f"     ❌ 丢弃（低于阈值 {min_score}）")
                        stats['discarded'] += 1
                        continue
                    
                    print(f"     ✅ 通过")
                    stats['passed'] += 1
                    
                    # 保存到 Obsidian
                    if save_to_obsidian and obsidian_saver:
                        file_path = obsidian_saver.save_to_periodic(article, score)
                        if file_path:
                            print(f"     💾 已保存: {file_path}")
                            stats['saved'] += 1
                        else:
                            print(f"     ⚠️  保存失败")
                            stats['errors'].append({
                                'article': article_title,
                                'error': '保存失败'
                            })
                
                except Exception as e:
                    print(f"     ❌ 处理失败: {e}")
                    stats['failed'] += 1
                    stats['errors'].append({
                        'article': article_title,
                        'error': str(e)
                    })
        
        except Exception as e:
            print(f"  ❌ 信源处理失败: {e}")
            stats['failed'] += 1
            stats['errors'].append({
                'source': source.get('name'),
                'error': str(e)
            })

    return stats


def print_summary(stats: dict):
    """打印处理摘要"""
    print("\n" + "=" * 60)
    print("批量处理摘要")
    print("=" * 60)
    print(f"总信源数: {stats['total']}")
    print(f"获取文章: {stats['fetched']}")
    print(f"通过评分: {stats['passed']}")
    print(f"已丢弃: {stats['discarded']}")
    print(f"已保存: {stats['saved']}")
    print(f"处理失败: {stats['failed']}")
    
    if stats['errors']:
        print(f"\n错误列表 ({len(stats['errors'])}):")
        for i, error in enumerate(stats['errors'], 1):
            print(f"  {i}. {error}")
    
    print("=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='WorldReader 批量处理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 批量处理，最低分数 60
  python batch_process.py --date 2026-03-31 --min-score 60

  # 处理并保存到 Obsidian
  python batch_process.py --date 2026-03-31 --min-score 60 --save-to-obsidian --obsidian-vault ~/ObsidianVault/AI-Memory

  # 使用配置文件
  python batch_process.py --config ./config.yaml --date 2026-03-31
        '''
    )
    
    parser.add_argument('--date', required=True, help='目标日期 (YYYY-MM-DD)')
    parser.add_argument('--min-score', type=int, default=60, help='最低质量分数 (默认: 60)')
    parser.add_argument('--save-to-obsidian', action='store_true', help='保存到 Obsidian')
    parser.add_argument('--obsidian-vault', help='Obsidian Vault 路径')
    parser.add_argument('--config', default='./config.yaml', help='配置文件路径 (默认: ./config.yaml)')
    parser.add_argument('--sources', help='信源列表 (JSON 格式，或从文件读取)')
    parser.add_argument('--json', action='store_true', help='以 JSON 格式输出结果')
    
    args = parser.parse_args()
    
    # 加载信源
    if args.sources:
        if os.path.exists(args.sources):
            with open(args.sources, 'r', encoding='utf-8') as f:
                sources = json.load(f)
        else:
            try:
                sources = json.loads(args.sources)
            except json.JSONDecodeError:
                print(f"错误: 无法解析信源列表: {args.sources}")
                sys.exit(1)
    else:
        # 使用默认信源（从配置文件读取）
        print("未指定信源，使用配置文件中的信源列表")
        # 这里可以添加从配置文件读取信源的逻辑
        sources = []
    
    if not sources:
        print("错误: 未找到信源列表")
        print("请使用 --sources 参数指定信源，或确保配置文件中包含信源列表")
        sys.exit(1)
    
    # 批量处理
    stats = batch_process(
        sources=sources,
        date=args.date,
        min_score=args.min_score,
        save_to_obsidian=args.save_to_obsidian,
        obsidian_vault=args.obsidian_vault,
        config_path=args.config
    )
    
    # 输出结果
    if args.json:
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    else:
        print_summary(stats)


if __name__ == '__main__':
    main()