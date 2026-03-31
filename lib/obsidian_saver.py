"""
Obsidian 保存器
将文章保存到 Obsidian Vault
"""

import os
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path

try:
    from ..utils import ensure_directory
except ImportError:
    # 支持直接运行
    import os
    from pathlib import Path

    def ensure_directory(path: str) -> None:
        Path(path).mkdir(parents=True, exist_ok=True)


class ObsidianSaver:
    """Obsidian Vault 保存器"""

    def __init__(self, vault_path: str):
        """
        初始化保存器

        Args:
            vault_path: Obsidian Vault 路径
        """
        self.vault_path = vault_path

    def save_to_periodic(self, article: Dict, score: Dict) -> Optional[str]:
        """
        保存文章到 Periodic 目录

        Args:
            article: 文章字典
            score: 质量评分字典

        Returns:
            成功返回文件路径，失败返回 None
        """
        try:
            # 获取日期
            published_at = article.get('published_at', '')
            if published_at:
                try:
                    pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    year_str = pub_date.strftime('%Y')
                    month_str = pub_date.strftime('%m')
                    date_str = pub_date.strftime('%Y-%m-%d')
                except:
                    year_str = datetime.now().strftime('%Y')
                    month_str = datetime.now().strftime('%m')
                    date_str = datetime.now().strftime('%Y-%m-%d')
            else:
                year_str = datetime.now().strftime('%Y')
                month_str = datetime.now().strftime('%m')
                date_str = datetime.now().strftime('%Y-%m-%d')

            # 构造目录路径：4-Periodic/Daily/YYYY/MM/
            dir_path = os.path.join(
                self.vault_path,
                '4-Periodic',
                'Daily',
                year_str,
                month_str
            )

            # 确保目录存在
            ensure_directory(dir_path)

            # 生成文件名
            title = article.get('title', '').replace('/', '-')
            # 移除或替换文件名中的非法字符
            title = ''.join(c if c.isalnum() or c in (' ', '-', '_', '。', '？', '！') else '_' for c in title)
            file_name = f"{date_str}-{title[:50]}.md"
            file_path = os.path.join(dir_path, file_name)

            # 生成内容
            content = self._format_article_with_score(article, score)

            # 保存文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return file_path

        except Exception as e:
            print(f"保存到 Obsidian 失败: {e}")
            return None

    def _format_article_with_score(self, article: Dict, score: Dict) -> str:
        """
        格式化文章内容（包含评分）

        Args:
            article: 文章字典
            score: 质量评分

        Returns:
            Markdown 格式的文章内容
        """
        title = article.get('title', '')
        content = article.get('content', '')
        author = article.get('metadata', {}).get('author', '')
        url = article.get('metadata', {}).get('url', '')
        published_at = article.get('published_at', '')
        source_name = article.get('metadata', {}).get('source_name', '')
        tags = article.get('metadata', {}).get('tags', [])

        md_lines = []

        # 标题
        if title:
            md_lines.append(f"# {title}\n")

        # 元数据
        md_lines.append("---")
        md_lines.append(f"**来源**: {source_name or '未知'}")
        md_lines.append(f"**作者**: {author or '未知'}")
        md_lines.append(f"**发布时间**: {published_at or '未知'}")
        if url:
            md_lines.append(f"**原文链接**: {url}")
        if tags:
            md_lines.append(f"**标签**: {', '.join(tags)}")
        md_lines.append("---\n")

        # 正文
        if content:
            md_lines.append(content)

        # 质量评分
        md_lines.append("\n---\n")
        md_lines.append("## 质量评分\n")

        overall = score.get('overall', 0)
        level = score.get('level', 'unknown')

        md_lines.append(f"**综合评分**: {overall}/100（{self._level_to_chinese(level)}）\n")

        # 维度评分表
        md_lines.append("| 维度 | 评分 | 权重 |")
        md_lines.append("|------|------|------|")

        weights = {
            'completeness': ('完整性', 0.3),
            'accuracy': ('准确性', 0.25),
            'readability': ('可读性', 0.2),
            'originality': ('原创性', 0.15),
            'timeliness': ('时效性', 0.1),
        }

        dimensions = score.get('dimensions', {})
        for key, (name, weight) in weights.items():
            value = dimensions.get(key, 0)
            md_lines.append(f"| **{name}** | {value}/100 | {int(weight * 100)}% |")

        # 报告
        report = score.get('report', {})

        if report.get('strengths'):
            md_lines.append("\n**优点**：")
            for strength in report['strengths']:
                md_lines.append(f"- ✅ {strength}")

        if report.get('weaknesses'):
            md_lines.append("\n**不足**：")
            for weakness in report['weaknesses']:
                md_lines.append(f"- ❌ {weakness}")

        if report.get('suggestions'):
            md_lines.append("\n**建议**：")
            for suggestion in report['suggestions']:
                md_lines.append(f"- {suggestion}")

        # 评分时间
        scored_at = score.get('scored_at', '')
        if scored_at:
            md_lines.append(f"\n---\n*评分时间：{scored_at}*")

        # 网络来源
        if url:
            md_lines.append(f"*网络来源：{url}*")

        return '\n'.join(md_lines)

    def _level_to_chinese(self, level: str) -> str:
        """将英文等级转换为中文"""
        level_map = {
            'high': '高质量',
            'medium': '中等质量',
            'low': '低质量',
        }
        return level_map.get(level, '未知')