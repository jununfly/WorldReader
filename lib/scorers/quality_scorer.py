"""
内容质量评分器
对文章进行多维度质量评分
"""

import os
import re
from typing import Dict, List
from datetime import datetime

try:
    from ..utils import (
        load_json,
        save_json,
        ensure_directory,
        generate_id,
    )
except ImportError:
    # 支持直接运行
    import os
    import re
    import json
    from datetime import datetime
    import uuid

    def load_json(file_path: str):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None

    def save_json(data: dict, file_path: str) -> bool:
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False

    def ensure_directory(path: str) -> None:
        os.makedirs(path, exist_ok=True)

    def generate_id() -> str:
        return str(uuid.uuid4())


class QualityScorer:
    """内容质量评分器"""

    def __init__(self, config: Dict = None):
        """
        初始化评分器

        Args:
            config: 配置字典
        """
        self.config = config or {}

        scorer_config = self.config.get('quality_scorer', {})
        self.weights = scorer_config.get('weights', {
            'completeness': 0.3,
            'accuracy': 0.25,
            'readability': 0.2,
            'originality': 0.15,
            'timeliness': 0.1,
        })

        thresholds = scorer_config.get('thresholds', {
            'high_quality': 80,
            'medium_quality': 60,
            'low_quality': 0,
        })

        self.high_quality_threshold = thresholds.get('high_quality', 80)
        self.medium_quality_threshold = thresholds.get('medium_quality', 60)

        # 质量评分存储目录
        self.scores_dir = "./quality_scores"

    def score(self, article: Dict, quality_standard: Dict = None) -> Dict:
        """
        对文章进行质量评分

        Args:
            article: 文章字典
            quality_standard: 自定义评分标准（可选）

        Returns:
            评分结果字典
        """
        # 使用自定义评分标准或默认标准
        weights = quality_standard.get('weights') if quality_standard else self.weights

        # 各维度评分
        completeness = self.evaluate_completeness(article)
        accuracy = self.evaluate_accuracy(article)
        readability = self.evaluate_readability(article)
        originality = self.evaluate_originality(article)
        timeliness = self.evaluate_timeliness(article)

        # 计算综合评分
        overall = (
            completeness * weights.get('completeness', 0.3) +
            accuracy * weights.get('accuracy', 0.25) +
            readability * weights.get('readability', 0.2) +
            originality * weights.get('originality', 0.15) +
            timeliness * weights.get('timeliness', 0.1)
        )

        # 生成评分报告
        report = self._generate_report(article, {
            'completeness': completeness,
            'accuracy': accuracy,
            'readability': readability,
            'originality': originality,
            'timeliness': timeliness,
        })

        # 构造结果
        result = {
            'article_id': article.get('id', ''),
            'overall': round(overall, 2),
            'dimensions': {
                'completeness': round(completeness, 2),
                'accuracy': round(accuracy, 2),
                'readability': round(readability, 2),
                'originality': round(originality, 2),
                'timeliness': round(timeliness, 2),
            },
            'level': self._get_quality_level(overall),
            'report': report,
            'scored_at': datetime.utcnow().isoformat() + 'Z',
        }

        # 保存评分
        self._save_score(result, article)

        return result

    def evaluate_completeness(self, article: Dict) -> float:
        """
        评估内容完整性 (0-100)

        Args:
            article: 文章字典

        Returns:
            完整性得分
        """
        score = 0
        total_checks = 5

        # 检查标题
        if article.get('title') and len(article['title']) > 5:
            score += 20

        # 检查正文长度
        content = article.get('content', '')
        if content and len(content) > 200:
            score += 20

        # 检查元数据
        metadata = article.get('metadata', {})
        if metadata.get('author'):
            score += 20
        if metadata.get('url'):
            score += 20
        if metadata.get('tags'):
            score += 20

        return score

    def evaluate_accuracy(self, article: Dict) -> float:
        """
        评估信息准确性 (0-100)

        Args:
            article: 文章字典

        Returns:
            准确性得分
        """
        score = 50  # 基础分

        content = article.get('content', '')

        # 检查是否有数据引用
        if re.search(r'来源|引用|数据|研究|报告', content):
            score += 20

        # 检查是否有链接
        if article.get('metadata', {}).get('url'):
            score += 20

        # 检查是否有具体数据（数字、百分比等）
        if re.search(r'\d+[%。，,]', content):
            score += 10

        return min(score, 100)

    def evaluate_readability(self, article: Dict) -> float:
        """
        评估可读性 (0-100)

        Args:
            article: 文章字典

        Returns:
            可读性得分
        """
        score = 0
        content = article.get('content', '')

        if not content:
            return 0

        # 检查段落结构
        paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
        if len(paragraphs) >= 3:
            score += 30

        # 检查句子长度
        sentences = re.split(r'[。！？.!?]', content)
        avg_sentence_length = sum(len(s) for s in sentences) / len(sentences) if sentences else 0

        if 10 <= avg_sentence_length <= 100:
            score += 30

        # 检查是否有标题层级
        if re.search(r'^#+\s', content, re.MULTILINE):
            score += 20

        # 检查是否有列表
        if re.search(r'^[\*\-\+]\s', content, re.MULTILINE):
            score += 20

        return score

    def evaluate_originality(self, article: Dict) -> float:
        """
        评估原创性 (0-100)

        Args:
            article: 文章字典

        Returns:
            原创性得分
        """
        score = 50  # 基础分

        content = article.get('content', '')

        # 检查是否有原创表述
        if '我认为' in content or '个人观点' in content or '我的看法' in content:
            score += 20

        # 检查是否有深度分析
        if re.search(r'分析|解读|深入|探讨', content):
            score += 15

        # 检查是否有具体案例
        if re.search(r'案例|例子|实践', content):
            score += 15

        return min(score, 100)

    def evaluate_timeliness(self, article: Dict) -> float:
        """
        评估时效性 (0-100)

        Args:
            article: 文章字典

        Returns:
            时效性得分
        """
        score = 0

        published_at = article.get('published_at', '')

        if not published_at:
            return 0

        try:
            # 解析发布日期
            pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))

            # 计算文章发布距今的天数
            now = datetime.utcnow()
            delta = (now - pub_date).days

            # 根据天数评分
            if delta <= 1:
                score = 100
            elif delta <= 7:
                score = 90
            elif delta <= 30:
                score = 70
            elif delta <= 90:
                score = 50
            elif delta <= 180:
                score = 30
            else:
                score = 10

        except Exception:
            score = 0

        return score

    def _generate_report(self, article: Dict, scores: Dict) -> Dict:
        """
        生成评分报告

        Args:
            article: 文章字典
            scores: 各维度评分

        Returns:
            报告字典
        """
        strengths = []
        weaknesses = []
        suggestions = []

        # 分析各维度
        if scores['completeness'] >= 80:
            strengths.append("内容结构完整")
        elif scores['completeness'] < 60:
            weaknesses.append("内容结构不完整")
            suggestions.append("补充标题、正文和元数据")

        if scores['accuracy'] >= 80:
            strengths.append("信息来源可靠")
        elif scores['accuracy'] < 60:
            weaknesses.append("缺乏数据来源标注")
            suggestions.append("补充数据来源链接")

        if scores['readability'] >= 80:
            strengths.append("文章结构清晰")
        elif scores['readability'] < 60:
            weaknesses.append("可读性较差")
            suggestions.append("优化段落结构和句子长度")

        if scores['originality'] >= 80:
            strengths.append("原创性强")
        elif scores['originality'] < 60:
            weaknesses.append("原创性不足")
            suggestions.append("增加个人观点和深度分析")

        if scores['timeliness'] >= 80:
            strengths.append("内容时效性强")
        elif scores['timeliness'] < 60:
            weaknesses.append("内容时效性较差")

        return {
            'strengths': strengths,
            'weaknesses': weaknesses,
            'suggestions': suggestions,
        }

    def _get_quality_level(self, score: float) -> str:
        """
        获取质量等级

        Args:
            score: 综合评分

        Returns:
            质量等级 (high/medium/low)
        """
        if score >= self.high_quality_threshold:
            return 'high'
        elif score >= self.medium_quality_threshold:
            return 'medium'
        else:
            return 'low'

    def _save_score(self, score_result: Dict, article: Dict) -> None:
        """
        保存评分结果

        Args:
            score_result: 评分结果
            article: 文章字典
        """
        try:
            # 解析日期
            published_at = article.get('published_at', '')
            if published_at:
                try:
                    pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    date_str = pub_date.strftime('%Y-%m-%d')
                except:
                    date_str = datetime.utcnow().strftime('%Y-%m-%d')
            else:
                date_str = datetime.utcnow().strftime('%Y-%m-%d')

            source_id = article.get('source_id', '')
            article_id = article.get('id', '')

            # 构造文件路径
            file_path = os.path.join(
                self.scores_dir,
                date_str,
                source_id,
                f"{article_id}.json"
            )

            # 确保目录存在
            ensure_directory(os.path.dirname(file_path))

            # 保存文件
            save_json(score_result, file_path)

        except Exception as e:
            print(f"保存评分失败: {e}")

    def load_score(self, article_id: str, date: str, source_id: str) -> Dict:
        """
        加载评分结果

        Args:
            article_id: 文章 ID
            date: 日期 (YYYY-MM-DD)
            source_id: 信源 ID

        Returns:
            评分结果字典
        """
        try:
            file_path = os.path.join(
                self.scores_dir,
                date,
                source_id,
                f"{article_id}.json"
            )

            return load_json(file_path) or {}

        except Exception as e:
            print(f"加载评分失败: {e}")
            return {}