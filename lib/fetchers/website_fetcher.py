"""
网站/博客内容获取器
通过 RSS 或网页抓取获取内容
"""

import requests
from typing import List, Dict
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime

from .content_fetcher import ContentFetcher


class WebsiteFetcher(ContentFetcher):
    """网站内容获取器"""

    def __init__(self, config: Dict = None):
        """
        初始化获取器

        Args:
            config: 配置字典
        """
        super().__init__(config)
        self.timeout = self.config.get('timeout', 30)

    def fetch(self, source: Dict, date: str) -> List[Dict]:
        """
        获取指定日期的网站内容

        Args:
            source: 信源配置，应包含 URL
            date: 日期字符串 (YYYY-MM-DD)

        Returns:
            内容列表
        """
        url = source.get('url')

        if not url:
            return []

        # 判断是否为 RSS feed
        if self._is_rss_feed(url):
            return self._fetch_from_rss(url, source, date)
        else:
            return self._fetch_from_web(url, source, date)

    def _is_rss_feed(self, url: str) -> bool:
        """
        判断是否为 RSS feed

        Args:
            url: URL

        Returns:
            是否为 RSS feed
        """
        return any(ext in url.lower() for ext in ['/feed', '/rss', '/atom', '.xml', '.rss'])

    def _fetch_from_rss(self, url: str, source: Dict, date: str) -> List[Dict]:
        """
        从 RSS feed 获取内容

        Args:
            url: RSS URL
            source: 信源配置
            date: 日期字符串

        Returns:
            内容列表
        """
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()

            feed = feedparser.parse(response.text)

            contents = []
            for entry in feed.entries:
                published_at = entry.get('published')
                if published_at:
                    try:
                        pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                        pub_date_str = pub_date.strftime('%Y-%m-%d')

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

            return [self._normalize_content(c, source) for c in contents]

        except Exception as e:
            print(f"从 RSS 获取内容失败: {e}")
            return []

    def _fetch_from_web(self, url: str, source: Dict, date: str) -> List[Dict]:
        """
        从网页抓取内容

        Args:
            url: 网页 URL
            source: 信源配置
            date: 日期字符串

        Returns:
            内容列表
        """
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 提取标题
            title = self._extract_title_from_page(soup)

            # 提取正文
            content = self._extract_content_from_page(soup)

            # 尝试从页面获取日期
            page_date = self._extract_date_from_page(soup)

            # 如果指定了日期，检查是否匹配
            if date and page_date:
                page_date_str = page_date.strftime('%Y-%m-%d')
                if page_date_str != date:
                    return []

            content_dict = {
                'id': '',
                'title': title,
                'url': url,
                'content': content,
                'author': self._extract_author_from_page(soup),
                'tags': [],
                'published_at': page_date.isoformat() if page_date else '',
            }

            return [self._normalize_content(content_dict, source)]

        except Exception as e:
            print(f"从网页获取内容失败: {e}")
            return []

    def _extract_title_from_page(self, soup: BeautifulSoup) -> str:
        """从页面提取标题"""
        # 尝试多种方式获取标题
        title = soup.find('h1')
        if title:
            return title.get_text(strip=True)

        title = soup.find('title')
        if title:
            return title.get_text(strip=True)

        return ''

    def _extract_content_from_page(self, soup: BeautifulSoup) -> str:
        """从页面提取正文"""
        # 移除不需要的标签
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()

        # 尝试找到主要内容区域
        content_area = soup.find('article') or soup.find('main')

        if content_area:
            return content_area.get_text(separator='\n', strip=True)

        # 如果没有找到，使用 body
        body = soup.find('body')
        if body:
            return body.get_text(separator='\n', strip=True)

        return ''

    def _extract_author_from_page(self, soup: BeautifulSoup) -> str:
        """从页面提取作者"""
        # 查找常见的作者元标签
        meta_author = soup.find('meta', attrs={'name': 'author'})
        if meta_author:
            return meta_author.get('content', '')

        # 查找常见的 author 类
        author_elem = soup.find(class_='author')
        if author_elem:
            return author_elem.get_text(strip=True)

        return ''

    def _extract_date_from_page(self, soup: BeautifulSoup) -> datetime:
        """从页面提取日期"""
        # 查找常见的日期元标签
        meta_date = soup.find('meta', attrs={'name': 'date'})
        if meta_date:
            date_str = meta_date.get('content', '')
            try:
                return datetime.fromisoformat(date_str)
            except:
                pass

        # 查找常见的日期类
        date_elem = soup.find(class_='date') or soup.find(class_='published')
        if date_elem:
            date_str = date_elem.get_text(strip=True)
            try:
                return datetime.fromisoformat(date_str)
            except:
                pass

        return None

    def _extract_content(self, entry: Dict) -> str:
        """提取文章正文"""
        if 'content' in entry and entry['content']:
            content = entry['content'][0].value
            import re
            return re.sub(r'<[^>]+>', '', content)

        if 'description' in entry:
            import re
            return re.sub(r'<[^>]+>', '', entry['description'])

        return ''