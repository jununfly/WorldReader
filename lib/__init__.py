# WorldReader Library

"""
WorldReader - 智能知识库阅读器
用于自动获取、处理、评分和存储来自各种信源的内容
"""

__version__ = "1.0.0"
__author__ = "AI Knowledge Base Team"

from .worldreader import WorldReader
from .parsers.subscription_parser import SubscriptionParser
from .fetchers.content_fetcher import ContentFetcher
from .generators.article_generator import ArticleGenerator
from .scorers.quality_scorer import QualityScorer

__all__ = [
    "WorldReader",
    "SubscriptionParser",
    "ContentFetcher",
    "ArticleGenerator",
    "QualityScorer",
]