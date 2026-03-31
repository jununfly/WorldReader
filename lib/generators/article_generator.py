"""
知识库文章生成器
将获取的内容转换为标准化的知识库文章格式
"""

import os
from typing import Dict
from datetime import datetime
from pathlib import Path

try:
    from ..utils import (
        ensure_directory,
        generate_id,
        format_date,
    )
except ImportError:
    # 支持直接运行
    import os
    from datetime import datetime
    from pathlib import Path
    import uuid

    def ensure_directory(path: str) -> None:
        Path(path).mkdir(parents=True, exist_ok=True)

    def generate_id() -> str:
        return str(uuid.uuid4())

    def format_date(date: datetime) -> str:
        return date.strftime('%Y-%m-%d')


class ArticleGenerator:
    """知识库文章生成器"""

    def __init__(self, config: Dict = None):
        """
        初始化生成器

        Args:
            config: 配置字典
        """
        self.config = config or {}

        kb_config = self.config.get('knowledge_base', {})
        self.kb_dir = kb_config.get('directory', './knowledge_base')
        self.output_format = kb_config.get('format', 'markdown')
        self.auto_save = kb_config.get('auto_save', True)

    def generate(self, content: Dict, source: Dict) -> Dict:
        """
        生成知识库文章

        Args:
            content: 标准化后的内容字典
            source: 信源配置

        Returns:
            文章字典
        """
        article = {
            'id': generate_id(),
            'source_id': source.get('id', ''),
            'title': content.get('title', ''),
            'content': self._format_content(content, source),
            'summary': self._generate_summary(content),
            'published_at': content.get('published_at', ''),
            'metadata': {
                'author': content.get('author', source.get('name', '')),
                'url': content.get('url', ''),
                'tags': content.get('tags', []),
                'source_name': source.get('name', ''),
                'source_type': source.get('type', ''),
                'category': source.get('category', ''),
                'generated_at': datetime.utcnow().isoformat() + 'Z',
            }
        }

        # 自动保存
        if self.auto_save:
            self.save_article(article)

        return article

    def _format_content(self, content: Dict, source: Dict) -> str:
        """
        格式化文章内容为 Markdown（确保始终标注来源）

        Args:
            content: 内容字典
            source: 信源配置

        Returns:
            Markdown 格式的文章
        """
        title = content.get('title', '')
        body = content.get('content', '')
        
        # 确保来源信息完整
        author = content.get('author') or source.get('author') or '未知'
        url = content.get('url') or source.get('url', '')
        tags = content.get('tags', [])
        published_at = content.get('published_at', '')
        source_name = source.get('name', '未知')

        # 构建 Markdown
        md_lines = []

        # 标题
        if title:
            md_lines.append(f"# {title}\n")

        # 元数据 - 始终包含来源信息
        md_lines.append("---")
        md_lines.append(f"**来源**: {source_name}")
        md_lines.append(f"**作者**: {author}")
        md_lines.append(f"**发布时间**: {published_at or '未知'}")
        if url:
            md_lines.append(f"**原文链接**: {url}")
        if tags:
            md_lines.append(f"**标签**: {', '.join(tags)}")
        md_lines.append("---\n")

        # 正文
        if body:
            md_lines.append(body)

        return '\n'.join(md_lines)

    def _generate_summary(self, content: Dict, max_length: int = 200) -> str:
        """
        生成文章摘要

        Args:
            content: 内容字典
            max_length: 最大长度

        Returns:
            摘要文本
        """
        body = content.get('content', '')

        if not body:
            return ''

        # 移除多余空白
        body = ' '.join(body.split())

        # 截取摘要
        if len(body) <= max_length:
            return body

        return body[:max_length] + '...'

    def save_article(self, article: Dict) -> bool:
        """
        保存文章到知识库

        Args:
            article: 文章字典

        Returns:
            成功返回 True，失败返回 False
        """
        try:
            # 解析日期
            published_at = article.get('published_at', '')
            if published_at:
                try:
                    pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    date_str = format_date(pub_date)
                except:
                    date_str = format_date(datetime.utcnow())
            else:
                date_str = format_date(datetime.utcnow())

            source_id = article.get('source_id', '')
            article_id = article.get('id', '')

            # 构造文件路径
            file_path = os.path.join(
                self.kb_dir,
                date_str,
                source_id,
                f"{article_id}.md"
            )

            # 确保目录存在
            ensure_directory(os.path.dirname(file_path))

            # 保存文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(article['content'])

            return True

        except Exception as e:
            print(f"保存文章失败: {e}")
            return False

    def load_article(self, article_id: str, date: str, source_id: str) -> Dict:
        """
        从知识库加载文章

        Args:
            article_id: 文章 ID
            date: 日期 (YYYY-MM-DD)
            source_id: 信源 ID

        Returns:
            文章字典
        """
        try:
            file_path = os.path.join(
                self.kb_dir,
                date,
                source_id,
                f"{article_id}.md"
            )

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                'id': article_id,
                'content': content,
                'file_path': file_path,
            }

        except Exception as e:
            print(f"加载文章失败: {e}")
            return {}