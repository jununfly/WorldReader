"""
订阅清单解析器
用于解析订阅清单文档，生成信源列表
"""

import os
from typing import List, Dict, Optional

try:
    from ..utils import (
        compute_sha256_hash,
        load_json,
        save_json,
        ensure_directory,
        generate_id,
    )
except ImportError:
    # 支持直接运行
    import hashlib
    import json
    import os
    from datetime import datetime
    import uuid

    def compute_sha256_hash(content: str) -> str:
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

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


class SubscriptionParser:
    """订阅清单解析器"""

    def __init__(self, cache_dir: str = "./cache"):
        """
        初始化解析器

        Args:
            cache_dir: 缓存目录
        """
        self.cache_dir = cache_dir
        self.sources_dir = os.path.join(cache_dir, "sources")
        self.hashes_file = os.path.join(cache_dir, "subscription_hashes.json")

        # 确保目录存在
        ensure_directory(self.sources_dir)

    def parse(self, doc_url: str, content: str) -> Dict:
        """
        解析订阅清单文档

        Args:
            doc_url: 订阅清单文档 URL
            content: 文档内容

        Returns:
            解析结果字典
        """
        # 计算当前内容的 hash
        current_hash = compute_sha256_hash(content)

        # 检查缓存
        cached_data = self._get_cached_sources(doc_url)

        if cached_data is not None:
            cached_hash = cached_data.get('content_hash')

            # 如果 hash 相同，直接返回缓存
            if cached_hash == current_hash:
                return {
                    "sources": cached_data.get('sources', []),
                    "cache_status": {
                        "hash": current_hash,
                        "updated_at": cached_data.get('updated_at'),
                        "is_cached": True,
                        "is_changed": False
                    }
                }

        # hash 不同或没有缓存，重新解析
        sources = self._parse_content(content)

        # 保存到缓存
        self._cache_sources(doc_url, current_hash, sources)

        return {
            "sources": sources,
            "cache_status": {
                "hash": current_hash,
                "updated_at": self._get_current_timestamp(),
                "is_cached": False,
                "is_changed": True
            }
        }

    def _parse_content(self, content: str) -> List[Dict]:
        """
        解析文档内容，提取信源列表

        Args:
            content: 文档内容

        Returns:
            信源列表
        """
        sources = []

        # 这里实现具体的解析逻辑
        # 目前支持 Markdown 表格格式

        lines = content.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i]

            # 检测表格开始
            if line.startswith('|') and '公众号' in line or '网站' in line or '仓库' in line:
                # 跳过表头和分隔线
                i += 2

                # 解析表格行
                while i < len(lines) and lines[i].startswith('|'):
                    source = self._parse_table_row(lines[i])
                    if source:
                        sources.append(source)
                    i += 1

                break

            i += 1

        # 如果没有找到表格，尝试其他格式
        if not sources:
            sources = self._parse_markdown_list(content)

        return sources

    def _parse_table_row(self, line: str) -> Optional[Dict]:
        """
        解析表格行

        Args:
            line: 表格行

        Returns:
            信源字典，解析失败返回 None
        """
        try:
            # 移除首尾的 |
            parts = line.strip('|').split('|')

            if len(parts) < 3:
                return None

            # 清理空白字符
            parts = [p.strip() for p in parts]

            # 根据表格结构解析
            # 假设格式: | 公众号 | 特点 | 适合人群 |
            # 或: | 网站 | 领域 | 特点 |

            name = parts[0]
            description = parts[1] if len(parts) > 1 else ""

            # 判断信源类型
            source_type = self._detect_source_type(name, description)

            return {
                "id": generate_id(),
                "name": name,
                "type": source_type,
                "url": "",  # 需要手动配置
                "category": self._detect_category(description),
                "enabled": True,
                "metadata": {
                    "description": description,
                    "update_frequency": "unknown"
                }
            }
        except Exception:
            return None

    def _parse_markdown_list(self, content: str) -> List[Dict]:
        """
        解析 Markdown 列表格式

        Args:
            content: 文档内容

        Returns:
            信源列表
        """
        sources = []
        lines = content.split('\n')

        for line in lines:
            # 检测列表项
            if line.strip().startswith('- ') or line.strip().startswith('* '):
                name = line.strip()[2:].strip()

                # 移除多余标记
                if '⭐' in name:
                    name = name.split('⭐')[1].strip()

                if name:
                    source_type = self._detect_source_type(name, "")

                    sources.append({
                        "id": generate_id(),
                        "name": name,
                        "type": source_type,
                        "url": "",
                        "category": "unknown",
                        "enabled": True,
                        "metadata": {
                            "description": "",
                            "update_frequency": "unknown"
                        }
                    })

        return sources

    def _detect_source_type(self, name: str, description: str) -> str:
        """
        检测信源类型

        Args:
            name: 信源名称
            description: 描述

        Returns:
            信源类型
        """
        # 关键词映射
        keywords = {
            "wechat": ["公众号", "微信"],
            "website": ["网站", "博客", "Blog"],
            "github": ["GitHub", "仓库", "repository"],
            "youtube": ["YouTube", "油管"],
            "bilibili": ["B站", "Bilibili"],
        }

        combined = f"{name} {description}".lower()

        for source_type, keys in keywords.items():
            if any(key.lower() in combined for key in keys):
                return source_type

        return "custom"

    def _detect_category(self, description: str) -> str:
        """
        检测信源类别

        Args:
            description: 描述

        Returns:
            类别
        """
        if not description:
            return "unknown"

        # 关键词映射
        keywords = {
            "全局资讯": ["资讯", "新闻", "行业"],
            "大模型": ["LLM", "大模型", "GPT", "Transformer"],
            "AIGC": ["AIGC", "生成", "多模态"],
            "工程化": ["工程", "部署", "MLOps"],
            "学术": ["学术", "论文", "研究"],
            "CV": ["视觉", "CV", "图像"],
        }

        desc_lower = description.lower()

        for category, keys in keywords.items():
            if any(key.lower() in desc_lower for key in keys):
                return category

        return "unknown"

    def _get_cached_sources(self, doc_url: str) -> Optional[Dict]:
        """
        获取缓存的信源列表

        Args:
            doc_url: 订阅清单文档 URL

        Returns:
            缓存数据，不存在返回 None
        """
        hashes = load_json(self.hashes_file)

        if not hashes:
            return None

        url_hash = compute_sha256_hash(doc_url)

        if url_hash not in hashes:
            return None

        cache_file = hashes[url_hash].get('cache_file')

        if not cache_file or not os.path.exists(cache_file):
            return None

        return load_json(cache_file)

    def _cache_sources(self, doc_url: str, content_hash: str, sources: List[Dict]) -> None:
        """
        缓存信源列表

        Args:
            doc_url: 订阅清单文档 URL
            content_hash: 内容 hash
            sources: 信源列表
        """
        url_hash = compute_sha256_hash(doc_url)
        cache_file = os.path.join(self.sources_dir, f"{url_hash}.json")

        # 保存信源列表
        cache_data = {
            "url": doc_url,
            "content_hash": content_hash,
            "updated_at": self._get_current_timestamp(),
            "sources": sources
        }

        save_json(cache_data, cache_file)

        # 更新 hash 索引
        hashes = load_json(self.hashes_file) or {}

        hashes[url_hash] = {
            "url": doc_url,
            "cache_file": cache_file
        }

        save_json(hashes, self.hashes_file)

    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'