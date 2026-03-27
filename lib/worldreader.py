"""
WorldReader 主入口类
"""

import os
from typing import Dict, List, Optional
import yaml

try:
    from .parsers.subscription_parser import SubscriptionParser
    from .fetchers.content_fetcher import ContentFetcher
    from .fetchers.wechat_fetcher import WeChatFetcher
    from .fetchers.website_fetcher import WebsiteFetcher
    from .fetchers.github_fetcher import GitHubFetcher
    from .generators.article_generator import ArticleGenerator
    from .scorers.quality_scorer import QualityScorer
except ImportError:
    # 支持直接运行
    from parsers.subscription_parser import SubscriptionParser
    from fetchers.content_fetcher import ContentFetcher
    from fetchers.wechat_fetcher import WeChatFetcher
    from fetchers.website_fetcher import WebsiteFetcher
    from fetchers.github_fetcher import GitHubFetcher
    from generators.article_generator import ArticleGenerator
    from scorers.quality_scorer import QualityScorer
from ..utils import (
    load_json,
    save_json,
    ensure_directory,
    generate_id,
)


class WorldReader:
    """WorldReader 主类"""

    def __init__(self, config_path: str = "./config.yaml"):
        """
        初始化 WorldReader

        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)

        # 初始化各组件
        self.subscription_parser = SubscriptionParser(
            cache_dir=self.config.get('cache', {}).get('directory', './cache')
        )

        self.article_generator = ArticleGenerator(self.config)
        self.quality_scorer = QualityScorer(self.config)

        # 注册内容获取器
        self.fetchers: Dict[str, ContentFetcher] = {}
        self._register_fetchers()

        # 信源缓存
        self._sources_cache: Dict[str, List[Dict]] = {}

    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        if not os.path.exists(config_path):
            print(f"配置文件不存在: {config_path}，使用默认配置")
            return {}

        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _register_fetchers(self) -> None:
        """注册内容获取器"""
        fetcher_config = self.config.get('content_fetcher', {})

        # 注册各类型获取器
        self.fetchers['wechat'] = WeChatFetcher(fetcher_config)
        self.fetchers['website'] = WebsiteFetcher(fetcher_config)
        self.fetchers['github'] = GitHubFetcher(fetcher_config)
        self.fetchers['rss'] = WebsiteFetcher(fetcher_config)  # RSS 使用网站获取器

    def parse_subscription(self, subscription_doc_url: str, content: str = None) -> Dict:
        """
        解析订阅清单

        Args:
            subscription_doc_url: 订阅清单文档 URL
            content: 文档内容（可选，不提供则尝试获取）

        Returns:
            解析结果字典
        """
        # 如果没有提供内容，尝试获取
        if content is None:
            content = self._fetch_subscription_content(subscription_doc_url)

        if not content:
            return {
                'error': 'ERR_SUBSCRIPTION_DOC_NOT_FOUND',
                'message': '无法获取订阅清单文档内容'
            }

        # 解析订阅清单
        result = self.subscription_parser.parse(subscription_doc_url, content)

        # 缓存信源列表
        url_hash = subscription_doc_url
        self._sources_cache[url_hash] = result['sources']

        return result

    def _fetch_subscription_content(self, doc_url: str) -> Optional[str]:
        """
        获取订阅清单文档内容

        Args:
            doc_url: 文档 URL

        Returns:
            文档内容，失败返回 None
        """
        # 支持飞书文档
        if 'feishu.cn' in doc_url:
            return self._fetch_feishu_doc(doc_url)

        # 支持 Obsidian/Markdown 文件
        if doc_url.endswith('.md'):
            try:
                with open(doc_url, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print(f"读取文件失败: {e}")
                return None

        # 其他 URL，尝试 HTTP 请求
        try:
            import requests
            response = requests.get(doc_url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"获取文档失败: {e}")
            return None

    def _fetch_feishu_doc(self, doc_url: str) -> Optional[str]:
        """
        获取飞书文档内容

        Args:
            doc_url: 飞书文档 URL

        Returns:
            文档内容，失败返回 None
        """
        # 提取 doc_token
        # URL 格式: https://xxx.feishu.cn/wiki/{doc_token}
        parts = doc_url.split('/')
        if not parts:
            return None

        doc_token = parts[-1]

        # 使用 feishu_doc 工具读取
        try:
            from feishu_doc import feishu_doc
            result = feishu_doc({'action': 'read', 'doc_token': doc_token})

            if result.get('success'):
                return result.get('content', '')
            else:
                print(f"读取飞书文档失败: {result.get('error')}")
                return None

        except ImportError:
            print("未安装 feishu_doc 工具，无法读取飞书文档")
            return None
        except Exception as e:
            print(f"读取飞书文档失败: {e}")
            return None

    def fetch_source_content(self, source_id: str, date: str) -> List[Dict]:
        """
        获取指定信源的内容

        Args:
            source_id: 信源 ID
            date: 日期 (YYYY-MM-DD)

        Returns:
            文章列表
        """
        # 从缓存中查找信源
        source = None
        for sources in self._sources_cache.values():
            for s in sources:
                if s['id'] == source_id:
                    source = s
                    break
            if source:
                break

        if not source:
            return []

        # 获取内容
        source_type = source.get('type', 'custom')
        fetcher = self.fetchers.get(source_type)

        if not fetcher:
            print(f"不支持的信源类型: {source_type}")
            return []

        # 调用获取器
        contents = fetcher.fetch(source, date)

        # 生成知识库文章
        articles = []
        for content in contents:
            article = self.article_generator.generate(content, source)
            articles.append(article)

        return articles

    def score_article(self, article: Dict, quality_standard: Dict = None) -> Dict:
        """
        对文章进行质量评分

        Args:
            article: 文章字典
            quality_standard: 自定义评分标准（可选）

        Returns:
            评分结果字典
        """
        return self.quality_scorer.score(article, quality_standard)

    def get_daily_articles(self, date: str, source_id: str = None) -> Dict:
        """
        获取指定日期的文章列表及评分

        Args:
            date: 日期 (YYYY-MM-DD)
            source_id: 信源 ID（可选，为空则获取所有信源）

        Returns:
            结果字典
        """
        if source_id:
            # 获取指定信源
            articles = self.fetch_source_content(source_id, date)
            sources = [s for sources in self._sources_cache.values() for s in sources if s['id'] == source_id]
        else:
            # 获取所有信源
            articles = []
            sources = []

            for source_list in self._sources_cache.values():
                for source in source_list:
                    if not source.get('enabled', True):
                        continue

                    source_articles = self.fetch_source_content(source['id'], date)
                    articles.extend(source_articles)
                    sources.append(source)

        # 对每篇文章进行评分
        articles_with_scores = []
        for article in articles:
            score = self.score_article(article)
            articles_with_scores.append({
                'article': article,
                'quality_score': score
            })

        # 计算统计信息
        statistics = self._calculate_statistics(articles_with_scores)

        return {
            'date': date,
            'source': sources[0] if source_id and sources else None,
            'articles': articles_with_scores,
            'statistics': statistics
        }

    def _calculate_statistics(self, articles_with_scores: List[Dict]) -> Dict:
        """
        计算统计信息

        Args:
            articles_with_scores: 带评分的文章列表

        Returns:
            统计信息字典
        """
        total = len(articles_with_scores)

        if total == 0:
            return {
                'total_articles': 0,
                'avg_quality_score': 0,
                'high_quality_count': 0,
                'medium_quality_count': 0,
                'low_quality_count': 0,
            }

        scores = [a['quality_score']['overall'] for a in articles_with_scores]
        avg_score = sum(scores) / total

        high_count = sum(1 for s in scores if s >= self.quality_scorer.high_quality_threshold)
        medium_count = sum(1 for s in scores if self.quality_scorer.medium_quality_threshold <= s < self.quality_scorer.high_quality_threshold)
        low_count = sum(1 for s in scores if s < self.quality_scorer.medium_quality_threshold)

        return {
            'total_articles': total,
            'avg_quality_score': round(avg_score, 2),
            'high_quality_count': high_count,
            'medium_quality_count': medium_count,
            'low_quality_count': low_count,
        }