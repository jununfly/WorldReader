"""
微信公众号内容获取器
通过 RSSHub API 获取公众号文章
"""

import requests
from typing import List, Dict
from datetime import datetime

from .content_fetcher import ContentFetcher


class WeChatFetcher(ContentFetcher):
    """微信公众号内容获取器"""

    def __init__(self, config: Dict = None):
        """
        初始化获取器

        Args:
            config: 配置字典，包含 RSSHub 配置
        """
        super().__init__(config)

        rsshub_config = self.config.get('rsshub', {})
        self.rsshub_base_url = rsshub_config.get('base_url', 'https://rsshub.app')
        self.timeout = self.config.get('timeout', 30)

    def fetch(self, source: Dict, date: str) -> List[Dict]:
        """
        获取指定日期的公众号文章

        Args:
            source: 信源配置，应包含公众号名称或原始 ID
            date: 日期字符串 (YYYY-MM-DD)

        Returns:
            文章列表
        """
        try:
            # 构造 RSSHub URL
            account_name = source.get('name')
            if not account_name:
                return []

            # RSSHub 公众号订阅格式: /wechat/mp/{account_name}
            rss_url = f"{self.rsshub_base_url}/wechat/mp/{account_name}"

            # 获取 RSS 订阅
            response = requests.get(rss_url, timeout=self.timeout)
            response.raise_for_status()

            # 解析 RSS
            import feedparser
            feed = feedparser.parse(response.text)

            # 提取文章
            contents = []
            for entry in feed.entries:
                # 获取发布日期
                published_at = entry.get('published')
                if published_at:
                    try:
                        pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                        pub_date_str = pub_date.strftime('%Y-%m-%d')

                        # 只保留指定日期的文章
                        if pub_date_str != date:
                            continue
                    except Exception:
                        continue

                content = {
                    'id': entry.get('id', ''),
                    'title': entry.get('title', ''),
                    'url': entry.get('link', ''),
                    'content': self._extract_content(entry),
                    'author': entry.get('author', ''),
                    'tags': [tag.term for tag in entry.get('tags', [])],
                    'published_at': published_at,
                }

                contents.append(content)

            # 标准化并返回
            return [self._normalize_content(c, source) for c in contents]

        except requests.RequestException as e:
            print(f"获取公众号文章失败: {e}")
            return []
        except Exception as e:
            print(f"解析 RSS 失败: {e}")
            return []

    def _extract_content(self, entry: Dict) -> str:
        """
        提取文章正文

        Args:
            entry: RSS entry

        Returns:
            正文内容
        """
        # 优先使用 content
        if 'content' in entry and entry['content']:
            content = entry['content'][0].value
            # 移除 HTML 标签
            import re
            return re.sub(r'<[^>]+>', '', content)

        # 其次使用 description
        if 'description' in entry:
            import re
            return re.sub(r'<[^>]+>', '', entry['description'])

        return ''