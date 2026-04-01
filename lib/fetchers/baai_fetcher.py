"""
智源社区内容获取器 v3
支持从 hub.baai.ac.cn 获取用户主页的文章内容
使用 requests + BeautifulSoup + JavaScript 解析
"""

import re
import json
import html
from typing import List, Dict, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup

try:
    from .content_fetcher import ContentFetcher
except ImportError:
    from content_fetcher import ContentFetcher


class BaaFetcher(ContentFetcher):
    """智源社区内容获取器（完整版本）"""

    def __init__(self, config: Dict = None):
        """
        初始化获取器

        Args:
            config: 配置字典
        """
        super().__init__(config)
        self.base_url = 'https://hub.baai.ac.cn'
        self.timeout = self.config.get('timeout', 30)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }

    def fetch(self, source: Dict, date: str) -> List[Dict]:
        """
        获取指定日期的内容

        Args:
            source: 信源配置字典
            date: 日期字符串 (YYYY-MM-DD)

        Returns:
            内容列表
        """
        url = source.get('url', '')
        if not url:
            print(f"  ⚠️  信源未配置 URL")
            return []

        print(f"  🔄 正在获取: {url}")

        try:
            # 1. 获取用户主页，提取文章列表
            articles = self._fetch_articles_from_user_page(url, source, date)

            print(f"  ✅ 找到 {len(articles)} 篇目标日期的文章")

            # 2. 获取每篇文章的详细内容
            final_articles = []
            for i, article in enumerate(articles, 1):
                print(f"  📄 [{i}/{len(articles)}] {article.get('title', '无标题')}")
                article_detail = self._fetch_article_detail(article)
                if article_detail:
                    final_articles.append(article_detail)
                else:
                    print(f"     ⚠️  获取详情失败")

            return final_articles

        except Exception as e:
            print(f"  ❌ 获取失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _fetch_articles_from_user_page(self, url: str, source: Dict, date: str) -> List[Dict]:
        """
        从用户主页获取文章列表

        Args:
            url: 用户主页 URL
            source: 信源配置
            date: 目标日期

        Returns:
            文章列表
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()

            html = response.text

            # 尝试从 HTML 中提取文章数据
            articles = []

            # 方法1: 从 Nuxt.js 的 __NUXT__ 中提取
            nuxt_data = self._extract_nuxt_data(html)
            if nuxt_data:
                articles = self._parse_articles_from_nuxt_data(nuxt_data, source, date)

            # 方法2: 从 HTML 链接中提取
            if not articles:
                soup = BeautifulSoup(html, 'html.parser')
                articles = self._parse_articles_from_html(soup, source, date)

            return articles

        except requests.RequestException as e:
            print(f"  ❌ 请求失败: {e}")
            return []
        except Exception as e:
            print(f"  ❌ 解析失败: {e}")
            return []

    def _extract_nuxt_data(self, html: str) -> Optional[dict]:
        """
        提取 Nuxt.js 数据

        Args:
            html: HTML 内容

        Returns:
            Nuxt.js 数据字典
        """
        # 查找 __NUXT__ script 标签（Nuxt 2）
        pattern = r'<script id="__NUXT__"[^>]*>(.+?)</script>'
        match = re.search(pattern, html, re.DOTALL)

        if not match:
            return None

        try:
            json_str = match.group(1)
            # HTML 实体解码
            json_str = html.unescape(json_str)
            data = json.loads(json_str)
            return data
        except json.JSONDecodeError as e:
            print(f"  ⚠️  解析 __NUXT__ 失败: {e}")
            return None

    def _parse_articles_from_nuxt_data(self, nuxt_data: dict, source: Dict, date: str) -> List[Dict]:
        """
        从 Nuxt.js 数据中解析文章

        Args:
            nuxt_data: Nuxt.js 数据
            source: 信源配置
            date: 目标日期

        Returns:
            文章列表
        """
        articles = []

        try:
            # Nuxt 2 的数据结构通常是 __NUXT__.data[0].stories
            data = nuxt_data.get('data', [])

            if not data:
                return []

            # 获取第一个数据对象
            first_data = data[0] if isinstance(data, list) else data

            # 尝试可能的路径
            possible_paths = [
                'stories',
                'articles',
                'posts',
                'user.stories',
                'user.articles',
            ]

            article_list = None
            for path in possible_paths:
                parts = path.split('.')
                current = first_data
                try:
                    for part in parts:
                        current = current[part]
                    article_list = current
                    break
                except (KeyError, TypeError):
                    continue

            # 如果还是没找到，直接从整个数据中搜索文章ID
            if not article_list:
                json_str = json.dumps(first_data)
                article_ids = re.findall(r'"id":(\d+)', json_str)
                print(f"  ⚠️  找到 {len(article_ids)} 个可能的文章ID，但无法提取详细信息")

            if not article_list:
                return []

            # 解析文章列表
            if isinstance(article_list, list):
                for item in article_list:
                    article = self._parse_article_item(item, source, date)
                    if article:
                        articles.append(article)
            elif isinstance(article_list, dict):
                # 可能是分页数据
                for key, value in article_list.items():
                    if isinstance(value, list):
                        for item in value:
                            article = self._parse_article_item(item, source, date)
                            if article:
                                articles.append(article)

            return articles

        except Exception as e:
            print(f"  ⚠️  从 Nuxt.js 数据解析文章失败: {e}")
            import traceback
            traceback.print_exc()
            return []

            # 尝试可能的路径
            possible_paths = [
                'data',
                'stories',
                'articles',
                'posts',
                'user.stories',
                'user.articles',
            ]

            article_list = None
            for path in possible_paths:
                parts = path.split('.')
                data = page_props
                try:
                    for part in parts:
                        data = data[part]
                    article_list = data
                    break
                except (KeyError, TypeError):
                    continue

            # 如果还是没找到，尝试搜索包含文章ID的数据
            if not article_list:
                json_str = json.dumps(next_data)
                article_ids = re.findall(r'"id":(\d+)', json_str)
                # 如果找到很多数字ID，可能是文章
                if len(article_ids) > 5:
                    print(f"  ⚠️  找到 {len(article_ids)} 个可能的文章ID，但无法提取详细信息")

            if not article_list:
                return []

            # 解析文章列表
            if isinstance(article_list, list):
                for item in article_list:
                    article = self._parse_article_item(item, source, date)
                    if article:
                        articles.append(article)
            elif isinstance(article_list, dict):
                # 可能是分页数据
                for key, value in article_list.items():
                    if isinstance(value, list):
                        for item in value:
                            article = self._parse_article_item(item, source, date)
                            if article:
                                articles.append(article)

            return articles

        except Exception as e:
            print(f"  ⚠️  从 Next.js 数据解析文章失败: {e}")
            return []

    def _parse_article_item(self, item: dict, source: Dict, date: str) -> Optional[Dict]:
        """
        解析单个文章项

        Args:
            item: 文章项字典
            source: 信源配置
            date: 目标日期

        Returns:
            文章字典
        """
        try:
            # 提取文章ID
            article_id = item.get('id') or str(item.get('story_id') or item.get('article_id') or '')

            if not article_id:
                return None

            # 提取标题
            title = item.get('title') or item.get('name') or ''

            # 提取发布时间
            published_at = item.get('created_at') or item.get('published_at') or item.get('time') or ''

            # 格式化时间
            if published_at:
                try:
                    dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    published_at = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass

            # 检查日期
            if not published_at.startswith(date):
                return None

            # 提取内容
            content = item.get('content') or item.get('body') or item.get('summary') or ''

            # 构造文章URL
            url = f"{self.base_url}/view/{article_id}"

            return {
                'id': str(article_id),
                'title': title,
                'url': url,
                'published_at': published_at,
                'content': content,
                'source_id': source.get('id', ''),
                'source_name': source.get('name', ''),
                'tags': source.get('tags', []),
            }

        except Exception as e:
            print(f"  ⚠️  解析文章项失败: {e}")
            return None

    def _parse_articles_from_html(self, soup: BeautifulSoup, source: Dict, date: str) -> List[Dict]:
        """
        从 HTML 中解析文章

        Args:
            soup: BeautifulSoup 对象
            source: 信源配置
            date: 目标日期

        Returns:
            文章列表
        """
        articles = []

        # 查找所有链接
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')

            # 检查是否是文章链接
            if not href.startswith('/view/'):
                continue

            article_url = f"{self.base_url}{href}"
            article_id = href.replace('/view/', '')

            # 从链接文本中提取时间和标题
            text = link.get_text()

            # 提取时间
            time_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', text)
            published_at = time_match.group(1) if time_match else ''

            # 检查日期
            if published_at and not published_at.startswith(date):
                continue

            # 提取标题
            title = self._extract_title_from_link_text(text, published_at)

            articles.append({
                'id': article_id,
                'url': article_url,
                'title': title,
                'published_at': published_at,
                'source_id': source.get('id', ''),
                'source_name': source.get('name', ''),
                'tags': source.get('tags', []),
            })

        return articles

    def _extract_title_from_link_text(self, text: str, published_at: str) -> str:
        """
        从链接文本中提取标题

        Args:
            text: 链接文本
            published_at: 发布时间

        Returns:
            标题
        """
        # 移除时间部分
        if published_at:
            text = text.replace(published_at, '').strip()

        # 移除多余的空格和换行
        title = ' '.join(text.split())

        return title

    def _fetch_article_detail(self, article: Dict) -> Optional[Dict]:
        """
        获取文章详细内容

        Args:
            article: 文章信息字典

        Returns:
            文章详情字典
        """
        url = article.get('url', '')
        if not url:
            return None

        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()

            html = response.text

            # 尝试从 __NUXT__ 提取完整内容
            nuxt_data = self._extract_nuxt_data(html)
            if nuxt_data:
                detail = self._parse_article_detail_from_nuxt_data(nuxt_data, article)
                if detail:
                    return detail

            # 如果 Next.js 数据中没有完整内容，从 HTML 提取
            soup = BeautifulSoup(html, 'html.parser')
            return self._parse_article_detail_from_html(soup, article)

        except Exception as e:
            print(f"     ❌ 获取文章详情失败: {e}")
            return None

    def _parse_article_detail_from_nuxt_data(self, nuxt_data: dict, article: Dict) -> Optional[Dict]:
        """
        从 Nuxt.js 数据解析文章详情

        Args:
            nuxt_data: Nuxt.js 数据
            article: 文章信息

        Returns:
            文章详情
        """
        try:
            data = nuxt_data.get('data', [])

            if not data:
                return None

            # 获取第一个数据对象
            first_data = data[0] if isinstance(data, list) else data

            # 尝试获取完整内容
            content = first_data.get('content') or first_data.get('body') or first_data.get('description') or ''

            # 如果没有内容，返回 None
            if not content:
                return None

            # 更新文章信息
            article['content'] = content

            return article

        except Exception as e:
            return None

    def _parse_article_detail_from_html(self, soup: BeautifulSoup, article: Dict) -> Dict:
        """
        从 HTML 解析文章详情

        Args:
            soup: BeautifulSoup 对象
            article: 文章信息

        Returns:
            文章详情
        """
        # 提取标题
        h1 = soup.find('h1')
        if h1:
            article['title'] = h1.get_text().strip()

        # 提取正文
        main_content = soup.find('main') or soup.find('article') or soup.find(class_=re.compile(r'content', re.I))

        if main_content:
            paragraphs = main_content.find_all(['p', 'div'], recursive=True)
            content_parts = []
            for p in paragraphs:
                text = p.get_text().strip()
                if len(text) > 10:
                    content_parts.append(text)
            article['content'] = '\n\n'.join(content_parts)

        return article