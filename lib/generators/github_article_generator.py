"""
GitHub 仓库文章生成器
将 GitHub 仓库转换为结构化的知识库文章
"""

import re
import os
from typing import Dict, Optional
import requests


class GitHubArticleGenerator:
    """GitHub 仓库文章生成器"""

    def __init__(self, config: Dict = None):
        """
        初始化生成器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.api_token = os.getenv('GITHUB_TOKEN', '')
        self.base_url = 'https://api.github.com'
        self.timeout = self.config.get('content_fetcher', {}).get('timeout', 30)

    def generate(self, repo_url: str) -> Dict:
        """
        将 GitHub 仓库转换为知识库文章

        Args:
            repo_url: GitHub 仓库 URL，如 "https://github.com/THU-MAIC/OpenMAIC"

        Returns:
            标准化的文章对象
        """
        # 解析仓库 URL
        owner, repo = self._parse_github_url(repo_url)
        if not owner or not repo:
            return {
                'error': 'INVALID_REPO_URL',
                'message': f'无效的 GitHub 仓库 URL: {repo_url}'
            }

        # 获取仓库信息
        repo_info = self._fetch_repo_info(owner, repo)
        if 'error' in repo_info:
            return repo_info

        # 获取 README 内容
        readme = self._fetch_readme(owner, repo)

        # 分析技术栈
        tech_stack = self._analyze_tech_stack(repo_info, readme)

        # 生成 Markdown 内容
        markdown_content = self._generate_markdown(repo_info, readme, tech_stack)

        # 组装文章对象
        article = {
            'id': f"github_{owner}_{repo}",
            'title': f"{repo_info['name']} - {repo_info.get('description', 'GitHub Project')}",
            'url': repo_info['html_url'],
            'content': markdown_content,
            'author': repo_info['owner']['login'],
            'tags': self._extract_tags(repo_info, tech_stack),
            'published_at': repo_info['created_at'],
            'source': {
                'id': f"github_{owner}_{repo}",
                'name': f"{owner}/{repo}",
                'type': 'github',
                'url': repo_url
            }
        }

        return article

    def _parse_github_url(self, url: str) -> tuple:
        """
        解析 GitHub URL

        Args:
            url: GitHub 仓库 URL

        Returns:
            (owner, repo) 元组
        """
        # 移除 .git 后缀
        url = url.replace('.git', '')

        # 匹配 github.com/owner/repo 格式
        pattern = r'github\.com/([^/]+)/([^/]+)'
        match = re.search(pattern, url)
        if match:
            return match.groups()

        return (None, None)

    def _fetch_repo_info(self, owner: str, repo: str) -> Dict:
        """
        获取仓库基本信息

        Args:
            owner: 仓库所有者
            repo: 仓库名称

        Returns:
            仓库信息字典
        """
        # 设置请求头
        headers = {
            'Accept': 'application/vnd.github.v3+json'
        }

        if self.api_token:
            headers['Authorization'] = f'token {self.api_token}'

        try:
            # 尝试使用 GitHub API
            url = f"{self.base_url}/repos/{owner}/{repo}"
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            # API 失败，返回错误
            return {
                'error': 'FETCH_FAILED',
                'message': f'获取仓库信息失败: {e}'
            }

    def _fetch_readme(self, owner: str, repo: str) -> str:
        """
        获取 README 内容

        Args:
            owner: 仓库所有者
            repo: 仓库名称

        Returns:
            README 内容
        """
        # 设置请求头
        headers = {
            'Accept': 'application/vnd.github.v3+json'
        }

        if self.api_token:
            headers['Authorization'] = f'token {self.api_token}'

        try:
            # 尝试获取 README
            url = f"{self.base_url}/repos/{owner}/{repo}/readme"
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            # README 内容是 base64 编码的
            import base64
            content = base64.b64decode(data['content']).decode('utf-8')
            return content

        except requests.RequestException:
            # 获取失败，返回空字符串
            return ''

    def _analyze_tech_stack(self, repo_info: Dict, readme: str) -> Dict:
        """
        分析技术栈

        Args:
            repo_info: 仓库信息
            readme: README 内容

        Returns:
            技术栈字典
        """
        tech_stack = {
            'languages': repo_info.get('language', ''),
            'language_stats': repo_info.get('languages', {}),
            'topics': repo_info.get('topics', []),
            'frameworks': [],
            'databases': [],
            'tools': []
        }

        # 从 README 中提取技术关键词
        if readme:
            # 常见框架和库
            frameworks = [
                'React', 'Vue', 'Angular', 'Next.js', 'Nuxt.js',
                'Django', 'Flask', 'FastAPI', 'Spring Boot',
                'Express', 'Koa', 'NestJS'
            ]
            for fw in frameworks:
                if fw in readme:
                    if fw not in tech_stack['frameworks']:
                        tech_stack['frameworks'].append(fw)

            # 常见数据库
            databases = ['MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'SQLite']
            for db in databases:
                if db in readme:
                    if db not in tech_stack['databases']:
                        tech_stack['databases'].append(db)

        return tech_stack

    def _extract_tags(self, repo_info: Dict, tech_stack: Dict) -> list:
        """
        提取标签

        Args:
            repo_info: 仓库信息
            tech_stack: 技术栈

        Returns:
            标签列表
        """
        tags = []

        # 添加主题标签
        tags.extend(tech_stack.get('topics', []))

        # 添加主要语言
        if tech_stack.get('languages'):
            tags.append(tech_stack['languages'])

        # 添加框架
        tags.extend(tech_stack.get('frameworks', []))

        # 去重并限制数量
        tags = list(set(tags))
        return tags[:10]

    def _generate_markdown(self, repo_info: Dict, readme: str, tech_stack: Dict) -> str:
        """
        生成 Markdown 内容

        Args:
            repo_info: 仓库信息
            readme: README 内容
            tech_stack: 技术栈

        Returns:
            Markdown 内容
        """
        lines = []

        # 标题
        lines.append(f"# {repo_info['name']} - {repo_info.get('description', 'GitHub Project')}")
        lines.append('')

        # 项目简介
        description = repo_info.get('description', '')
        if description:
            lines.append('## 项目简介')
            lines.append(description)
            lines.append('')

        # 如果有 README，提取主要内容
        if readme:
            # 提取 README 的核心部分（去除 badges 和图片）
            lines.append(self._extract_readme_content(readme))

        # 技术栈
        lines.append('## 技术栈')
        if tech_stack.get('languages'):
            lines.append(f"- **主要语言**: {tech_stack['languages']}")
        if tech_stack.get('frameworks'):
            lines.append(f"- **框架**: {', '.join(tech_stack['frameworks'])}")
        if tech_stack.get('databases'):
            lines.append(f"- **数据库**: {', '.join(tech_stack['databases'])}")
        if tech_stack.get('topics'):
            lines.append(f"- **主题**: {', '.join(tech_stack['topics'][:5])}")
        lines.append('')

        # 项目活跃度
        lines.append('## 项目活跃度')
        lines.append(f"- **Stars**: {repo_info.get('stargazers_count', 0)}")
        lines.append(f"- **Forks**: {repo_info.get('forks_count', 0)}")
        lines.append(f"- **Open Issues**: {repo_info.get('open_issues_count', 0)}")
        lines.append(f"- **Watchers**: {repo_info.get('watchers_count', 0)}")
        lines.append('')

        # 许可证
        license_info = repo_info.get('license', {})
        if license_info and license_info.get('name'):
            lines.append('## 许可证')
            lines.append(f"- **许可证**: {license_info['name']}")
            lines.append('')

        # 相关链接
        lines.append('## 相关链接')
        lines.append(f"- **仓库地址**: {repo_info['html_url']}")
        if repo_info.get('homepage'):
            lines.append(f"- **主页**: {repo_info['homepage']}")
        lines.append('')

        # 总结
        lines.append('## 总结')
        lines.append(f"{repo_info['name']} 是一个开源项目，使用 {tech_stack.get('languages', 'Unknown')} 开发。")
        lines.append(f"该项目已获得 {repo_info.get('stargazers_count', 0)} 个 Stars，")
        lines.append(f"拥有 {repo_info.get('forks_count', 0)} 个 Forks，")
        lines.append(f"当前有 {repo_info.get('open_issues_count', 0)} 个未解决的 Issues。")
        lines.append('')

        return '\n'.join(lines)

    def _extract_readme_content(self, readme: str) -> str:
        """
        从 README 中提取主要内容

        Args:
            readme: README 内容

        Returns:
            提取后的内容
        """
        lines = readme.split('\n')
        extracted_lines = []
        in_code_block = False

        for line in lines:
            # 跳过 badges（图片链接）
            if line.strip().startswith('![') or 'badge' in line.lower():
                continue

            # 跳过空的图片链接
            if '<img' in line or '<a href=' in line:
                continue

            # 处理代码块
            if line.strip().startswith('```'):
                in_code_block = not in_code_block

            # 只保留有意义的标题和内容
            if line.startswith('#') or (line.strip() and not in_code_block):
                extracted_lines.append(line)

        return '\n'.join(extracted_lines)