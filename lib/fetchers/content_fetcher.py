"""
内容获取器基类
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime

try:
    from ..utils import load_json, save_json, ensure_directory, generate_id, format_date, parse_date
except ImportError:
    # 支持直接运行
    import os
    import json
    import hashlib
    from datetime import datetime

    def load_json(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None

    def save_json(data, file_path):
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False

    def ensure_directory(path):
        os.makedirs(path, exist_ok=True)

    def generate_id():
        import uuid
        return str(uuid.uuid4())

    def format_date(date):
        return date.strftime('%Y-%m-%d')

    def parse_date(date_str):
        return datetime.strptime(date_str, '%Y-%m-%d')


class ContentFetcher(ABC):
    """内容获取器基类"""

    def __init__(self, config: Dict = None):
        """
        初始化获取器

        Args:
            config: 配置字典
        """
        self.config = config or {}

    @abstractmethod
    def fetch(self, source: Dict, date: str) -> List[Dict]:
        """
        获取指定日期的内容

        Args:
            source: 信源配置字典
            date: 日期字符串 (YYYY-MM-DD)

        Returns:
            内容列表
        """
        pass

    def _filter_by_date(self, contents: List[Dict], date: str) -> List[Dict]:
        """
        按日期过滤内容

        Args:
            contents: 原始内容列表
            date: 目标日期 (YYYY-MM-DD)

        Returns:
            过滤后的内容列表
        """
        filtered = []

        for content in contents:
            published_at = content.get('published_at')

            if not published_at:
                continue

            try:
                # 尝试解析日期
                if isinstance(published_at, str):
                    pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                else:
                    pub_date = published_at

                # 格式化为 YYYY-MM-DD 进行比较
                pub_date_str = pub_date.strftime('%Y-%m-%d')

                if pub_date_str == date:
                    filtered.append(content)

            except Exception:
                # 日期解析失败，跳过
                continue

        return filtered

    def _extract_title(self, content: Dict) -> str:
        """
        提取标题

        Args:
            content: 内容字典

        Returns:
            标题字符串
        """
        return content.get('title') or ''

    def _extract_url(self, content: Dict) -> str:
        """
        提取 URL

        Args:
            content: 内容字典

        Returns:
            URL 字符串
        """
        return content.get('url') or content.get('link') or ''

    def _extract_content(self, content: Dict) -> str:
        """
        提取正文

        Args:
            content: 内容字典

        Returns:
            正文内容
        """
        # 尝试多个字段
        body = content.get('body') or content.get('content') or content.get('description') or ''
        return str(body) if body else ''

    def _extract_author(self, content: Dict) -> str:
        """
        提取作者

        Args:
            content: 内容字典

        Returns:
            作者字符串
        """
        return content.get('author') or content.get('creator') or ''

    def _extract_tags(self, content: Dict) -> List[str]:
        """
        提取标签

        Args:
            content: 内容字典

        Returns:
            标签列表
        """
        tags = content.get('tags') or []

        if isinstance(tags, str):
            return [tags]
        elif isinstance(tags, list):
            return tags
        else:
            return []

    def _normalize_content(self, content: Dict, source: Dict) -> Dict:
        """
        标准化内容格式

        Args:
            content: 原始内容
            source: 信源配置

        Returns:
            标准化的内容字典
        """
        return {
            'id': content.get('id', ''),
            'title': self._extract_title(content),
            'url': self._extract_url(content),
            'content': self._extract_content(content),
            'author': self._extract_author(content),
            'tags': self._extract_tags(content),
            'published_at': content.get('published_at', ''),
            'source_id': source.get('id', ''),
            'source_name': source.get('name', ''),
        }