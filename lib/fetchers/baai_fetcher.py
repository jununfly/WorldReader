"""
智源社区内容获取器
支持从 hub.baai.ac.cn 获取用户主页的文章内容
使用 OpenClaw browser tool 处理动态渲染的页面
"""

import re
import json
from typing import List, Dict, Optional
from datetime import datetime
from subprocess import run, PIPE

try:
    from .content_fetcher import ContentFetcher
except ImportError:
    from content_fetcher import ContentFetcher


class BaaFetcher(ContentFetcher):
    """智源社区内容获取器（使用 browser tool）"""

    def __init__(self, config: Dict = None):
        """
        初始化获取器

        Args:
            config: 配置字典
        """
        super().__init__(config)
        self.base_url = 'https://hub.baai.ac.cn'

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
            print(f"错误: 信源未配置 URL")
            return []

        print(f"  正在获取: {url}")

        try:
            # 使用 browser tool 获取页面
            articles = self._fetch_with_browser(url, source, date)
            
            print(f"  找到 {len(articles)} 篇目标日期的文章")
            return articles
        
        except Exception as e:
            print(f"  获取失败: {e}")
            return []

    def _fetch_with_browser(self, url: str, source: Dict, date: str) -> List[Dict]:
        """
        使用 browser tool 获取页面内容

        Args:
            url: 页面 URL
            source: 信源配置
            date: 目标日期

        Returns:
            文章列表
        """
        target_id = None
        try:
            # 调用 openclaw browser open
            result = run(
                ['openclaw', 'browser', 'open', url],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise Exception(f"Browser open 失败: {result.stderr}")
            
            # 解析返回的 targetId（从 stdout 提取）
            target_id = None
            for line in result.stdout.split('\n'):
                if 'opened:' in line and url in line:
                    # 格式: "opened: https://..."
                    parts = line.split()
                    if len(parts) >= 2 and 'id:' in result.stdout:
                        # targetId 在下一行
                        continue
                    if 'id:' in line:
                        id_part = line.split('id:')[-1].strip()
                        target_id = id_part
                        break
                if 'id:' in line:
                    target_id = line.split('id:')[-1].strip()
                    break
            
            # 如果还没找到，尝试从 JSON 行解析
            if not target_id:
                for line in result.stdout.split('\n'):
                    if '"targetId"' in line:
                        try:
                            data = json.loads(line)
                            target_id = data.get('targetId')
                            break
                        except:
                            pass
            
            if not target_id:
                raise Exception("未能获取 targetId")

            # 获取快照
            result = run(
                ['openclaw', 'browser', 'snapshot', '--compact', '--target-id', target_id],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise Exception(f"Browser snapshot 失败: {result.stderr}")
            
            # 解析快照内容
            articles = self._parse_snapshot(result.stdout, source, date)
            
            # 获取每篇文章的详细内容
            final_articles = []
            for article in articles:
                article_detail = self._fetch_article_detail_with_browser(article['url'], source)
                if article_detail:
                    final_articles.append(article_detail)
            
            return final_articles
        
        except Exception as e:
            print(f"  获取失败: {e}")
            return []
        
        finally:
            # 关闭浏览器标签
            if target_id:
                run(['openclaw', 'browser', 'close', target_id], capture_output=True)

    def _parse_snapshot(self, snapshot: str, source: Dict, date: str) -> List[Dict]:
        """
        解析浏览器快照内容

        Args:
            snapshot: 浏览器快照文本
            source: 信源配置
            date: 目标日期

        Returns:
            文章列表
        """
        articles = []
        
        lines = snapshot.split('\n')
        
        for i, line in enumerate(lines):
            # 查找包含文章链接的行
            if '/view/' not in line:
                continue
            
            # 提取文章 URL
            url_match = re.search(r'/view/[^\s"\']+', line)
            if not url_match:
                continue
            
            article_url = url_match.group(0)
            article_id = article_url.replace('/view/', '')
            
            # 提取发布时间（通常是链接前的文本）
            # 格式: "2026-03-31 14:30:27"
            time_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
            if not time_match:
                continue
            
            published_at = time_match.group(1)
            
            # 检查日期
            pub_date = published_at.split()[0]
            if pub_date != date:
                continue
            
            # 提取标题（通常在标题行）
            # 向前查找标题行
            title = ''
            for j in range(i, max(0, i-5), -1):
                title_line = lines[j]
                if 'heading' in title_line and 'level' in title_line:
                    # 提取标题文本（在 heading 后面的部分）
                    title_match = re.search(r'heading[^"]*"[^"]+"([^"]+)"', title_line)
                    if title_match:
                        title = title_match.group(1)
                    break
            
            if not title:
                title = source.get('name', '')  # 使用信源名称作为后备

            articles.append({
                'id': article_id,
                'title': title,
                'url': f"{self.base_url}{article_url}",
                'published_at': published_at,
                'source_id': source.get('id', ''),
                'source_name': source.get('name', ''),
            })

        return articles

    def _fetch_article_detail_with_browser(self, article_url: str, source: Dict) -> Optional[Dict]:
        """
        使用 browser 获取文章详细内容

        Args:
            article_url: 文章 URL
            source: 信源配置

        Returns:
            文章详情字典
        """
        try:
            # 打开文章页面
            result = run(
                ['openclaw', 'browser', 'open', article_url],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return None
            
            target_id = None
            for line in result.stdout.split('\n'):
                if '"targetId"' in line:
                    try:
                        data = json.loads(line)
                        target_id = data.get('targetId')
                        break
                    except:
                        pass
            
            if not target_id:
                return None

            # 获取快照
            result = run(
                ['openclaw', 'browser', 'snapshot', '--compact', '--target-id', target_id],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return None
            
            # 解析内容
            content = self._parse_article_snapshot(result.stdout, source)
            
            if target_id:
                run(['openclaw', 'browser', 'close', target_id], capture_output=True)
            
            return content
        
        except Exception as e:
            print(f"    获取文章详情失败: {e}")
            return None

    def _parse_article_snapshot(self, snapshot: str, source: Dict) -> Optional[Dict]:
        """
        解析文章快照

        Args:
            snapshot: 浏览器快照文本
            source: 信源配置

        Returns:
            文章详情
        """
        lines = snapshot.split('\n')
        
        # 提取标题
        title = source.get('name', '')
        for line in lines[:20]:
            if 'heading' in line and 'level' in line:
                title_match = re.search(r'heading[^"]*"[^"]+"([^"]+)"', line)
                if title_match:
                    title = title_match.group(1)
                    break
        
        # 提取正文内容
        content_parts = []
        in_content = False
        for line in lines:
            # 跳过元数据部分（heading、generic 标签等）
            if 'heading' in line and 'level' in line:
                continue
            if 'generic' in line and ('link' in line or 'paragraph' in line):
                continue
            if 'button' in line or 'separator' in line:
                continue
            
            # 开始提取正文（通常在第一个 heading 之后）
            if in_content or ('heading' in line and 'level' in line and title in line):
                in_content = True
            
            if in_content and line.strip():
                content_parts.append(line.strip())
        
        content = '\n'.join(content_parts)
        
        # 提取标签
        tags = source.get('tags', [])
        
        return {
            'id': source.get('url', '').split('/')[-1],
            'title': title,
            'content': content,
            'url': source.get('url', ''),
            'author': source.get('name', ''),
            'published_at': source.get('published_at', ''),
            'tags': tags,
            'source_id': source.get('id', ''),
            'source_name': source.get('name', ''),
        }