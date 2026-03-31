# WorldReader Skill Specification

## Overview

**Name**: WorldReader
**Version**: 1.0.0
**Purpose**: 智能阅读各种文章、代码仓库等内容，生成知识库文章并进行质量评分

## 功能描述

### 功能1: 订阅清单解析与缓存管理

**输入参数**:
- `subscription_doc_url` (string): 订阅清单文档URL（支持飞书文档、Obsidian Markdown等格式）

**处理流程**:
1. 获取指定订阅清单文档内容
2. 计算文档内容的 SHA256 hash
3. 检查本地缓存目录是否存在该文档的缓存文件
   - 如果不存在：解析文档 → 生成信源列表 → 保存到本地缓存 → 记录 hash
   - 如果存在：比对缓存 hash
     - hash 相同：直接返回缓存的信源列表
     - hash 不同：重新解析文档 → 更新信源列表缓存 → 更新 hash 记录

**输出**:
```json
{
  "sources": [
    {
      "id": "source_001",
      "name": "量子位",
      "type": "wechat",
      "url": "https://mp.weixin.qq.com/...",
      "category": "全局资讯",
      "enabled": true,
      "metadata": {
        "author": "量子位团队",
        "update_frequency": "daily"
      }
    }
  ],
  "cache_status": {
    "hash": "a1b2c3d4...",
    "updated_at": "2026-03-27T14:30:00Z",
    "is_cached": true,
    "is_changed": false
  }
}
```

**信源类型支持**:
- `wechat`: 微信公众号
- `website`: 网站/博客
- `github`: GitHub仓库
- `rss`: RSS订阅
- `custom`: 自定义信源

---

### 功能2: 内容获取与知识库文章生成

**输入参数**:
- `source_id` (string): 信源ID
- `date` (string): 指定日期 (YYYY-MM-DD)

**处理流程**:
1. 根据信源ID获取信源配置
2. 根据信源类型调用对应的内容获取器
   - 微信公众号: 通过 RSSHub API 获取文章列表
   - 网站/博客: 通过 RSS 或网页抓取
   - GitHub: 通过 GitHub API 获取仓库动态
3. 过滤指定日期的内容
4. 生成知识库文章（Markdown格式）
   - 提取标题、正文、关键信息
   - 生成摘要
   - 添加元数据（来源、日期、标签等）

**输出**:
```json
{
  "article": {
    "id": "article_001",
    "source_id": "source_001",
    "title": "OpenAI发布GPT-5，能力提升10倍",
    "content": "# OpenAI发布GPT-5\n\n...",
    "summary": "OpenAI今日宣布...",
    "published_at": "2026-03-27",
    "metadata": {
      "author": "量子位",
      "url": "https://...",
      "tags": ["GPT", "大模型", "AI"]
    }
  }
}
```

---

### 功能3: 内容质量评分

**输入参数**:
- `article` (object): 知识库文章对象
- `quality_doc_url` (string): 内容质量评分标准文档URL

**处理流程**:
1. 获取内容质量评分标准文档
2. 解析评分标准（维度、权重、评分细则）
3. 对文章进行多维度分析
   - **内容完整性** (权重30%): 标题、正文、元数据是否完整
   - **信息准确性** (权重25%): 事实核查、数据来源标注
   - **可读性** (权重20%): 结构清晰、语言流畅、格式规范
   - **原创性** (权重15%): 原创内容占比、引用标注
   - **时效性** (权重10%): 内容新鲜度、信息时效
4. 计算综合评分（0-100分）
5. 生成评分报告

**输出**:
```json
{
  "quality_score": {
    "overall": 85,
    "dimensions": {
      "completeness": 90,
      "accuracy": 80,
      "readability": 85,
      "originality": 85,
      "timeliness": 90
    },
    "report": {
      "strengths": ["标题完整", "结构清晰", "时效性强"],
      "weaknesses": ["部分数据来源未标注"],
      "suggestions": ["补充数据来源链接"]
    }
  }
}
```

---

### 功能4: 输出信源内容列表

**输入参数**:
- `source_id` (string): 信源ID（可选，为空则返回所有信源）
- `date` (string): 指定日期 (YYYY-MM-DD)

**处理流程**:
1. 获取指定信源的配置
2. 调用功能2获取该信源当天的文章列表
3. 对每篇文章调用功能3进行质量评分
4. 组装输出结果

**输出**:
```json
{
  "source": {
    "id": "source_001",
    "name": "量子位",
    "type": "wechat"
  },
  "date": "2026-03-27",
  "articles": [
    {
      "article": { /* 文章对象 */ },
      "quality_score": { /* 评分对象 */ }
    }
  ],
  "statistics": {
    "total_articles": 5,
    "avg_quality_score": 82,
    "high_quality_count": 3,
    "medium_quality_count": 2,
    "low_quality_count": 0
  }
}
```

---

## 数据结构设计

### 1. 缓存文件结构

```
~/.openclaw/workspace/skills/worldreader/cache/
├── subscription_hashes.json
└── sources/
    └── {subscription_doc_hash}.json
```

**subscription_hashes.json**:
```json
{
  "doc_url_hash": {
    "url": "https://...",
    "content_hash": "sha256_hash",
    "updated_at": "2026-03-27T14:30:00Z",
    "cache_file": "sources/{hash}.json"
  }
}
```

### 2. 知识库文章存储

```
~/.openclaw/workspace/skills/worldreader/knowledge_base/
└── {date}/
    └── {source_id}/
        └── {article_id}.md
```

### 3. 质量评分存储

```
~/.openclaw/workspace/skills/worldreader/quality_scores/
└── {date}/
    └── {source_id}/
        └── {article_id}.json
```

---

## 核心组件

### 1. SubscriptionParser

```python
class SubscriptionParser:
    """订阅清单解析器"""

    def parse(self, doc_url: str) -> dict:
        """解析订阅清单文档"""
        pass

    def compute_hash(self, content: str) -> str:
        """计算内容hash"""
        pass

    def get_cached_sources(self, doc_url: str) -> Optional[list]:
        """获取缓存的信源列表"""
        pass

    def cache_sources(self, doc_url: str, sources: list) -> None:
        """缓存信源列表"""
        pass

    def is_cache_valid(self, doc_url: str, current_hash: str) -> bool:
        """检查缓存是否有效"""
        pass
```

### 2. ContentFetcher

```python
class ContentFetcher:
    """内容获取器基类"""

    def fetch(self, source: dict, date: str) -> list:
        """获取指定日期的内容"""
        pass

class WeChatFetcher(ContentFetcher):
    """微信公众号内容获取器"""

    def fetch(self, source: dict, date: str) -> list:
        """通过RSSHub获取公众号文章"""
        pass

class WebsiteFetcher(ContentFetcher):
    """网站内容获取器"""

    def fetch(self, source: dict, date: str) -> list:
        """通过RSS或网页抓取获取内容"""
        pass

class GitHubFetcher(ContentFetcher):
    """GitHub仓库内容获取器"""

    def fetch(self, source: dict, date: str) -> list:
        """通过GitHub API获取仓库动态"""
        pass
```

### 3. ArticleGenerator

```python
class ArticleGenerator:
    """知识库文章生成器"""

    def generate(self, content: dict, source: dict) -> dict:
        """生成知识库文章"""
        pass

    def extract_title(self, content: dict) -> str:
        """提取标题"""
        pass

    def extract_content(self, content: dict) -> str:
        """提取正文"""
        pass

    def generate_summary(self, content: str) -> str:
        """生成摘要"""
        pass

    def save_article(self, article: dict) -> None:
        """保存文章到知识库"""
        pass
```

### 4. QualityScorer

```python
class QualityScorer:
    """内容质量评分器"""

    def score(self, article: dict, quality_standard: dict) -> dict:
        """对文章进行质量评分"""
        pass

    def evaluate_completeness(self, article: dict) -> float:
        """评估内容完整性"""
        pass

    def evaluate_accuracy(self, article: dict) -> float:
        """评估信息准确性"""
        pass

    def evaluate_readability(self, article: dict) -> float:
        """评估可读性"""
        pass

    def evaluate_originality(self, article: dict) -> float:
        """评估原创性"""
        pass

    def evaluate_timeliness(self, article: dict) -> float:
        """评估时效性"""
        pass
```

---

## 配置文件

**config.yaml**:
```yaml
# WorldReader 配置

# 缓存配置
cache:
  enabled: true
  ttl: 86400  # 缓存过期时间（秒）
  directory: "./cache"

# 知识库配置
knowledge_base:
  directory: "./knowledge_base"
  format: "markdown"
  auto_save: true

# 内容获取配置
content_fetcher:
  timeout: 30
  retry_times: 3
  retry_delay: 2

  # RSSHub配置
  rsshub:
    base_url: "https://rsshub.app"
    enabled: true

  # GitHub配置
  github:
    api_token: "${GITHUB_TOKEN}"
    enabled: true

# 质量评分配置
quality_scorer:
  weights:
    completeness: 0.3
    accuracy: 0.25
    readability: 0.2
    originality: 0.15
    timeliness: 0.1
```

---

## 使用示例

### 示例1: 解析订阅清单

```python
from worldreader import WorldReader

reader = WorldReader()

# 解析订阅清单（自动处理缓存）
result = reader.parse_subscription(
    subscription_doc_url="https://zcnd9g0cgdok.feishu.cn/wiki/Al3xwSfMkibfFJkj1bycEYsqnKe"
)

print(f"获取到 {len(result['sources'])} 个信源")
print(f"缓存状态: {result['cache_status']}")
```

### 示例2: 获取指定信源的内容

```python
# 获取量子位今天的内容
articles = reader.fetch_source_content(
    source_id="source_001",
    date="2026-03-27"
)

for article in articles:
    print(f"- {article['title']}")
```

### 示例3: 质量评分

```python
# 对文章进行质量评分
score = reader.score_article(
    article=article,
    quality_doc_url="https://..."
)

print(f"综合评分: {score['overall']}")
print(f"各维度评分: {score['dimensions']}")
```

### 示例4: 输出完整列表

```python
# 获取所有信源今天的内容及评分
result = reader.get_daily_articles(
    date="2026-03-27"
)

print(f"总文章数: {result['statistics']['total_articles']}")
print(f"平均质量分: {result['statistics']['avg_quality_score']}")
```

---

## 扩展性设计

### 1. 支持新信源类型

通过继承 `ContentFetcher` 基类，可以轻松添加新的信源类型支持：

```python
class TikTokFetcher(ContentFetcher):
    """TikTok内容获取器"""

    def fetch(self, source: dict, date: str) -> list:
        # 实现TikTok内容获取逻辑
        pass

# 注册新的获取器
reader.register_fetcher('tiktok', TikTokFetcher())
```

### 2. 自定义评分标准

支持加载自定义评分标准文档：

```yaml
# custom_quality_standard.yaml
dimensions:
  - name: "技术深度"
    weight: 0.2
    criteria:
      - "是否包含代码示例"
      - "是否涉及底层原理"
  - name: "实用性"
    weight: 0.3
    criteria:
      - "是否提供可操作建议"
```

### 3. 输出格式扩展

支持多种输出格式：

- Markdown
- JSON
- HTML
- PDF

---

## 错误处理

### 常见错误类型

| 错误码 | 描述 | 处理方式 |
|--------|------|----------|
| `ERR_SUBSCRIPTION_DOC_NOT_FOUND` | 订阅清单文档不存在 | 返回错误，建议检查URL |
| `ERR_CACHE_INVALID` | 缓存文件损坏 | 删除缓存，重新解析 |
| `ERR_SOURCE_NOT_FOUND` | 信源不存在 | 返回错误，建议检查信源ID |
| `ERR_CONTENT_FETCH_FAILED` | 内容获取失败 | 重试3次，仍失败则跳过 |
| `ERR_QUALITY_DOC_NOT_FOUND` | 评分标准文档不存在 | 使用默认评分标准 |

---

## 性能优化

1. **缓存机制**: 订阅清单和内容获取均支持缓存
2. **并发获取**: 支持多线程并发获取多个信源的内容
3. **增量更新**: 只获取新增或更新的内容
4. **去重机制**: 避免重复处理同一篇文章

---

## 待实现功能

- [ ] 支持代码仓库README解析
- [ ] 支持多语言内容处理
- [ ] 支持内容去重和相似度检测
- [ ] 支持智能摘要生成
- [ ] 支持知识图谱构建

---

## 依赖项

- Python 3.10+
- requests: HTTP请求
- feedparser: RSS解析
- beautifulsoup4: HTML解析
- markdown: Markdown处理
- pyyaml: 配置文件解析
- opencc: 简繁转换（可选）

---

## 许可证

MIT License

---

**文档版本**: 1.0.0
**最后更新**: 2026-03-27
**维护者**: AI知识库团队