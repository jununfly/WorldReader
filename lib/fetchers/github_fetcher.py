"""
GitHub 仓库内容获取器
通过 GitHub API 获取仓库动态
"""

import requests
from typing import List, Dict
from datetime import datetime

from .content_fetcher import ContentFetcher


class GitHubFetcher(ContentFetcher):
    """GitHub 仓库内容获取器"""

    def __init__(self, config: Dict = None):
        """
        初始化获取器

        Args:
            config: 配置字典，包含 GitHub API token
        """
        super().__init__(config)

        github_config = self.config.get('github', {})
        self.api_token = github_config.get('api_token', '')
        self.base_url = github_config.get('base_url', 'https://api.github.com')
        self.timeout = self.config.get('timeout', 30)

    def fetch(self, source: Dict, date: str) -> List[Dict]:
        """
        获取指定日期的 GitHub 仓库动态

        Args:
            source: 信源配置，应包含 owner/repo
            date: 日期字符串 (YYYY-MM-DD)

        Returns:
            内容列表
        """
        repo_url = source.get('url')

        if not repo_url:
            return []

        # 解析 owner/repo
        parts = repo_url.replace('https://github.com/', '').replace('http://github.com/', '').split('/')
        if len(parts) < 2:
            return []

        owner, repo = parts[0], parts[1]

        # 获取仓库动态
        try:
            # 设置请求头
            headers = {
                'Accept': 'application/vnd.github.v3+json'
            }

            if self.api_token:
                headers['Authorization'] = f'token {self.api_token}'

            # 获取 events
            url = f"{self.base_url}/repos/{owner}/{repo}/events"
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            events = response.json()

            # 过滤指定日期的事件
            contents = []
            for event in events:
                created_at = event.get('created_at', '')
                if not created_at:
                    continue

                try:
                    event_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    event_date_str = event_date.strftime('%Y-%m-%d')

                    if event_date_str != date:
                        continue
                except:
                    continue

                content = {
                    'id': event.get('id', ''),
                    'title': self._extract_title_from_event(event),
                    'url': event.get('html_url', ''),
                    'content': self._extract_content_from_event(event),
                    'author': self._extract_actor(event),
                    'tags': [event.get('type', '')],
                    'published_at': created_at,
                }

                contents.append(content)

            return [self._normalize_content(c, source) for c in contents]

        except requests.RequestException as e:
            print(f"从 GitHub 获取内容失败: {e}")
            return []
        except Exception as e:
            print(f"解析 GitHub 事件失败: {e}")
            return []

    def _extract_title_from_event(self, event: Dict) -> str:
        """从事件提取标题"""
        event_type = event.get('type', '')
        actor = self._extract_actor(event)

        # 根据事件类型生成标题
        titles = {
            'PushEvent': f'{actor} 推送了代码',
            'CreateEvent': f'{actor} 创建了分支或标签',
            'DeleteEvent': f'{actor} 删除了分支或标签',
            'WatchEvent': f'{actor} star 了仓库',
            'ForkEvent': f'{actor} fork 了仓库',
            'ReleaseEvent': f'{actor} 发布了新版本',
            'IssuesEvent': f'{actor} 操作了 issue',
            'IssueCommentEvent': f'{actor} 评论了 issue',
            'PullRequestEvent': f'{actor} 操作了 PR',
        }

        return titles.get(event_type, f'{actor} 触发了 {event_type}')

    def _extract_content_from_event(self, event: Dict) -> str:
        """从事件提取内容"""
        event_type = event.get('type', '')

        if event_type == 'PushEvent':
            # 提取 commit 信息
            payload = event.get('payload', {})
            commits = payload.get('commits', [])
            if commits:
                commit_messages = [c.get('message', '') for c in commits]
                return '\n'.join(commit_messages)

        elif event_type == 'ReleaseEvent':
            # 提取 release 信息
            payload = event.get('payload', {})
            release = payload.get('release', {})
            return release.get('body', '')

        elif event_type == 'IssueCommentEvent':
            # 提取评论内容
            payload = event.get('payload', {})
            comment = payload.get('comment', {})
            return comment.get('body', '')

        elif event_type == 'PullRequestEvent':
            # 提取 PR 信息
            payload = event.get('payload', {})
            pr = payload.get('pull_request', {})
            return pr.get('body', '')

        return ''

    def _extract_actor(self, event: Dict) -> str:
        """提取操作者"""
        actor = event.get('actor', {})
        return actor.get('login', '')