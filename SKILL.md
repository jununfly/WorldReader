---
name: worldreader
description: 智能阅读各种文章、视频、代码仓库等内容，生成知识库文章并进行质量评分
version: 1.0.0
metadata:
  {
    "openclaw":
      {
        "requires": { "bins": ["python3"] },
        "install":
          [
            {
              "id": "python",
              "kind": "python",
              "packages": ["requests", "feedparser", "beautifulsoup4", "pyyaml", "markdown"],
              "label": "Install Python dependencies",
            },
          ],
      },
  }
---

# WorldReader - 智能知识库阅读器

WorldReader 是一个智能内容阅读和管理工具，用于自动获取、处理、评分和存储来自各种信源的内容，生成高质量的知识库文章。

## 核心功能

### 1. 订阅清单解析与缓存管理

- 支持解析飞书文档、Markdown 等格式的订阅清单
- 使用 SHA256 hash 智能检测文档变更
- 自动缓存信源列表，减少重复解析

### 2. 内容获取与知识库文章生成

- 支持多种信源类型：微信公众号、网站/博客、GitHub仓库、RSS订阅
- 自动提取内容、生成摘要、添加元数据
- 输出标准化的 Markdown 格式文章

### 3. 内容质量评分

- 5维度评分：完整性、准确性、可读性、原创性、时效性
- 支持自定义评分标准
- 生成详细的评分报告

### 4. 信源内容列表输出

- 按日期、信源组织内容
- 关联文章与质量评分
- 提供统计信息（总数、平均分、分级统计）

## 使用方法

### 解析订阅清单

```bash
python3 scripts/worldreader.py parse-subscription \
  --doc-url "https://zcnd9g0cgdok.feishu.cn/wiki/Al3xwSfMkibfFJkj1bycEYsqnKe"
```

### 获取指定信源内容

```bash
python3 scripts/worldreader.py fetch-content \
  --source-id "source_001" \
  --date "2026-03-27"
```

### 评分文章

```bash
python3 scripts/worldreader.py score-article \
  --article-path "./knowledge_base/2026-03-27/source_001/article_001.md"
```

### 获取每日文章列表

```bash
python3 scripts/worldreader.py get-daily-articles \
  --date "2026-03-27"
```

## 配置文件

在 `config.yaml` 中配置：

- 缓存设置
- 知识库路径
- 内容获取器配置
- 质量评分权重

## 扩展新信源类型

1. 继承 `ContentFetcher` 基类
2. 实现 `fetch()` 方法
3. 注册到 `WorldReader` 实例

## 数据存储

```
worldreader/
├── cache/              # 缓存目录
│   ├── subscription_hashes.json
│   └── sources/
├── knowledge_base/     # 知识库文章
│   └── {date}/{source_id}/
├── quality_scores/     # 质量评分
│   └── {date}/{source_id}/
└── config.yaml         # 配置文件
```

## 依赖项

- Python 3.10+
- requests: HTTP 请求
- feedparser: RSS 解析
- beautifulsoup4: HTML 解析
- pyyaml: 配置文件解析
- markdown: Markdown 处理

## 错误处理

所有操作都包含完善的错误处理，常见错误类型：

- `ERR_SUBSCRIPTION_DOC_NOT_FOUND`: 订阅清单文档不存在
- `ERR_CACHE_INVALID`: 缓存文件损坏
- `ERR_SOURCE_NOT_FOUND`: 信源不存在
- `ERR_CONTENT_FETCH_FAILED`: 内容获取失败
- `ERR_QUALITY_DOC_NOT_FOUND`: 评分标准文档不存在

## 详细文档

完整的技术规格文档请参考 [SPEC.md](./SPEC.md)