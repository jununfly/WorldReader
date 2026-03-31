"""
GitHub 仓库评分器
对 GitHub 仓库进行多维度质量评估
"""

import os
from typing import Dict
from datetime import datetime, timedelta
import requests


class GitHubRepoScorer:
    """GitHub 仓库评分器"""

    def __init__(self, config: Dict = None):
        """
        初始化评分器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.api_token = os.getenv('GITHUB_TOKEN', '')
        self.base_url = 'https://api.github.com'
        self.timeout = self.config.get('content_fetcher', {}).get('timeout', 30)

        # 评分权重
        quality_config = self.config.get('quality_scorer', {})
        self.weights = quality_config.get('github_weights', {
            'technical_depth': 0.30,  # 技术深度
            'activity': 0.25,         # 活跃度
            'completeness': 0.20,     # 完善程度
            'community': 0.15,        # 社区认可
            'timeliness': 0.10        # 时效性
        })

        # 评分阈值
        thresholds = quality_config.get('thresholds', {})
        self.high_quality = thresholds.get('high_quality', 80)
        self.medium_quality = thresholds.get('medium_quality', 60)

    def score(self, repo_url: str) -> Dict:
        """
        对 GitHub 仓库进行评分

        Args:
            repo_url: GitHub 仓库 URL

        Returns:
            评分结果字典
        """
        # 解析仓库 URL
        owner, repo = self._parse_github_url(repo_url)
        if not owner or not repo:
            return {
                'error': 'INVALID_REPO_URL',
                'message': f'无效的 GitHub 仓库 URL: {repo_url}'
            }

        # 收集评估数据
        data = self._collect_data(owner, repo)
        if 'error' in data:
            return data

        # 计算各维度分数
        dimensions = self._calculate_scores(data)

        # 计算综合评分
        overall = self._calculate_weighted_score(dimensions)

        # 生成评分报告
        report = self._generate_report(dimensions, data)

        # 确定质量等级
        level = self._get_quality_level(overall)

        return {
            'overall': round(overall, 2),
            'level': level,
            'dimensions': {k: round(v, 2) for k, v in dimensions.items()},
            'report': report,
            'details': data
        }

    def _parse_github_url(self, url: str) -> tuple:
        """解析 GitHub URL"""
        import re
        url = url.replace('.git', '')
        pattern = r'github\.com/([^/]+)/([^/]+)'
        match = re.search(pattern, url)
        return match.groups() if match else (None, None)

    def _collect_data(self, owner: str, repo: str) -> Dict:
        """收集评估数据"""
        # 设置请求头
        headers = {
            'Accept': 'application/vnd.github.v3+json'
        }

        if self.api_token:
            headers['Authorization'] = f'token {self.api_token}'

        try:
            # 获取仓库信息
            repo_info = self._fetch_with_retry(
                f"{self.base_url}/repos/{owner}/{repo}",
                headers
            )

            # 获取提交统计
            commits = self._fetch_with_retry(
                f"{self.base_url}/repos/{owner}/{repo}/commits?per_page=100",
                headers
            )

            # 获取贡献者
            contributors = self._fetch_with_retry(
                f"{self.base_url}/repos/{owner}/{repo}/contributors",
                headers
            )

            # 检查 README 和关键文件
            readme = self._fetch_with_retry(
                f"{self.base_url}/repos/{owner}/{repo}/readme",
                headers
            )

            # 检查是否有 CI/CD
            has_ci_cd = self._check_ci_cd(owner, repo, headers)

            # 检查是否有 LICENSE
            has_license = repo_info.get('license') is not None

            # 检查是否有 tests 目录
            has_tests = self._check_has_tests(owner, repo, headers)

            return {
                'repo_info': repo_info,
                'commits': commits,
                'contributors': contributors,
                'has_readme': readme is not None,
                'has_ci_cd': has_ci_cd,
                'has_license': has_license,
                'has_tests': has_tests,
                'owner': owner,
                'repo': repo
            }

        except Exception as e:
            return {
                'error': 'FETCH_FAILED',
                'message': f'收集数据失败: {e}'
            }

    def _fetch_with_retry(self, url: str, headers: Dict) -> Dict:
        """带重试的请求"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=self.timeout)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                continue

    def _check_ci_cd(self, owner: str, repo: str, headers: Dict) -> bool:
        """检查是否有 CI/CD 配置"""
        try:
            # 检查常见的 CI/CD 文件
            ci_files = [
                '.github/workflows',
                '.travis.yml',
                '.gitlab-ci.yml',
                'Jenkinsfile'
            ]

            for ci_file in ci_files:
                url = f"{self.base_url}/repos/{owner}/{repo}/contents/{ci_file}"
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    return True

            return False
        except:
            return False

    def _check_has_tests(self, owner: str, repo: str, headers: Dict) -> bool:
        """检查是否有测试"""
        try:
            # 检查常见的测试目录
            test_dirs = ['tests', 'test', '__tests__', 'spec']

            for test_dir in test_dirs:
                url = f"{self.base_url}/repos/{owner}/{repo}/contents/{test_dir}"
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    return True

            # 检查是否有 pytest 测试文件
            url = f"{self.base_url}/search/code?q=repo:{owner}/{repo}+filename:test_*.py"
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('total_count', 0) > 0:
                    return True

            return False
        except:
            return False

    def _calculate_scores(self, data: Dict) -> Dict:
        """计算各维度分数"""
        return {
            'technical_depth': self._evaluate_technical_depth(data),
            'activity': self._evaluate_activity(data),
            'completeness': self._evaluate_completeness(data),
            'community': self._evaluate_community(data),
            'timeliness': self._evaluate_timeliness(data)
        }

    def _evaluate_technical_depth(self, data: Dict) -> float:
        """评估技术深度"""
        score = 0

        # 代码质量 (40分)
        if data.get('has_tests'):
            score += 20
        if data.get('has_ci_cd'):
            score += 15
        if data.get('has_license'):
            score += 5

        # README 完整性 (20分)
        if data.get('has_readme'):
            score += 20

        # 项目结构 (40分)
        # 基于 Stars 和 Forks 间接判断项目质量
        repo_info = data.get('repo_info', {})
        stars = repo_info.get('stargazers_count', 0)
        forks = repo_info.get('forks_count', 0)

        if stars >= 1000:
            score += 20
        elif stars >= 100:
            score += 15
        elif stars >= 10:
            score += 10

        if forks >= 100:
            score += 20
        elif forks >= 10:
            score += 15
        elif forks >= 5:
            score += 10

        return min(score, 100)

    def _evaluate_activity(self, data: Dict) -> float:
        """评估活跃度"""
        score = 0
        commits = data.get('commits', [])
        repo_info = data.get('repo_info', {})

        # 提交频率 (40分)
        if commits:
            # 获取最近 7 天的提交
            seven_days_ago = datetime.now() - timedelta(days=7)
            recent_commits = [
                c for c in commits
                if datetime.strptime(c['commit']['author']['date'][:10], '%Y-%m-%d') >= seven_days_ago
            ]

            if len(recent_commits) >= 10:
                score += 40
            elif len(recent_commits) >= 5:
                score += 30
            elif len(recent_commits) >= 1:
                score += 20
            else:
                # 检查最近 30 天
                thirty_days_ago = datetime.now() - timedelta(days=30)
                recent_commits = [
                    c for c in commits
                    if datetime.strptime(c['commit']['author']['date'][:10], '%Y-%m-%d') >= thirty_days_ago
                ]
                if len(recent_commits) >= 5:
                    score += 15

        # Issue 处理 (30分)
        open_issues = repo_info.get('open_issues_count', 0)
        if open_issues == 0:
            score += 30
        elif open_issues < 10:
            score += 25
        elif open_issues < 50:
            score += 15

        # 贡献者数量 (30分)
        contributors = data.get('contributors', [])
        if len(contributors) >= 10:
            score += 30
        elif len(contributors) >= 5:
            score += 25
        elif len(contributors) >= 2:
            score += 20
        elif len(contributors) == 1:
            score += 10

        return min(score, 100)

    def _evaluate_completeness(self, data: Dict) -> float:
        """评估完善程度"""
        score = 0

        # 文档完整性 (30分)
        if data.get('has_readme'):
            score += 30

        # 测试覆盖 (25分)
        if data.get('has_tests'):
            score += 25

        # CI/CD (25分)
        if data.get('has_ci_cd'):
            score += 25

        # 许可证 (20分)
        if data.get('has_license'):
            score += 20

        return min(score, 100)

    def _evaluate_community(self, data: Dict) -> float:
        """评估社区认可"""
        score = 0
        repo_info = data.get('repo_info', {})

        # Stars 数量 (50分)
        stars = repo_info.get('stargazers_count', 0)
        if stars >= 1000:
            score += 50
        elif stars >= 100:
            score += 40
        elif stars >= 10:
            score += 30
        elif stars >= 1:
            score += 20

        # Forks 数量 (30分)
        forks = repo_info.get('forks_count', 0)
        if forks >= 100:
            score += 30
        elif forks >= 10:
            score += 25
        elif forks >= 1:
            score += 20

        # Watchers 数量 (20分)
        watchers = repo_info.get('watchers_count', 0)
        if watchers >= 100:
            score += 20
        elif watchers >= 10:
            score += 15
        elif watchers >= 1:
            score += 10

        return min(score, 100)

    def _evaluate_timeliness(self, data: Dict) -> float:
        """评估时效性"""
        score = 0
        repo_info = data.get('repo_info', {})

        # 最后更新时间 (50分)
        updated_at = repo_info.get('updated_at', '')
        if updated_at:
            updated_date = datetime.strptime(updated_at[:10], '%Y-%m-%d')
            days_since_update = (datetime.now() - updated_date).days

            if days_since_update <= 7:
                score += 50
            elif days_since_update <= 30:
                score += 40
            elif days_since_update <= 90:
                score += 30
            elif days_since_update <= 180:
                score += 20
            elif days_since_update <= 365:
                score += 10

        # 创建时间 (25分)
        created_at = repo_info.get('created_at', '')
        if created_at:
            created_date = datetime.strptime(created_at[:10], '%Y-%m-%d')
            age_days = (datetime.now() - created_date).days

            if age_days <= 30:
                score += 25
            elif age_days <= 90:
                score += 20
            elif age_days <= 365:
                score += 15

        # 版本发布 (25分)
        # 这里简化处理，实际可以检查 releases
        releases_url = f"{self.base_url}/repos/{data['owner']}/{data['repo']}/releases"
        try:
            response = requests.get(releases_url, timeout=10)
            if response.status_code == 200:
                releases = response.json()
                if releases:
                    score += 25
        except:
            pass

        return min(score, 100)

    def _calculate_weighted_score(self, dimensions: Dict) -> float:
        """计算加权总分"""
        total = 0
        for dim, score in dimensions.items():
            weight = self.weights.get(dim, 0)
            total += score * weight
        return total

    def _get_quality_level(self, score: float) -> str:
        """获取质量等级"""
        if score >= self.high_quality:
            return 'high'
        elif score >= self.medium_quality:
            return 'medium'
        else:
            return 'low'

    def _generate_report(self, dimensions: Dict, data: Dict) -> Dict:
        """生成评分报告"""
        strengths = []
        weaknesses = []
        suggestions = []

        # 技术深度
        tech_score = dimensions.get('technical_depth', 0)
        if tech_score >= 80:
            strengths.append('代码质量高，测试和 CI/CD 完善')
        elif tech_score <= 40:
            weaknesses.append('缺少测试或 CI/CD 配置')
            suggestions.append('添加单元测试和 CI/CD 流程')

        # 活跃度
        activity_score = dimensions.get('activity', 0)
        if activity_score >= 80:
            strengths.append('项目活跃度高，社区参与度高')
        elif activity_score <= 40:
            weaknesses.append('项目活跃度较低')
            suggestions.append('增加提交频率，及时处理 Issues')

        # 完善程度
        completeness_score = dimensions.get('completeness', 0)
        if completeness_score >= 80:
            strengths.append('文档完善，测试覆盖率高')
        elif completeness_score <= 40:
            weaknesses.append('文档或测试不完善')
            suggestions.append('完善 README 文档和测试用例')

        # 社区认可
        community_score = dimensions.get('community', 0)
        if community_score >= 80:
            strengths.append('社区认可度高，关注者众多')
        elif community_score <= 40:
            weaknesses.append('社区关注度较低')
            suggestions.append('增加项目推广，提升社区活跃度')

        # 时效性
        timeliness_score = dimensions.get('timeliness', 0)
        if timeliness_score >= 80:
            strengths.append('项目持续维护，更新及时')
        elif timeliness_score <= 40:
            weaknesses.append('项目可能已停止维护')
            suggestions.append('检查是否需要继续维护该项目')

        return {
            'strengths': strengths,
            'weaknesses': weaknesses,
            'suggestions': suggestions
        }