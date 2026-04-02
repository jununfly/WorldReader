<<<<<<< HEAD
# ClawTrade
=======
# WorldReader

WorldReader - 智能知识库阅读器

## Version
1.0.0

## Description
智能阅读各种文章、代码仓库等内容，生成知识库文章并进行质量评分

## Features
- 订阅清单解析与智能缓存管理
- 多信源内容获取（微信公众号、网站、GitHub等）
- 知识库文章生成（Markdown格式）
- 多维度内容质量评分
- 完整的命令行工具

## Installation
```bash
# 安装依赖
pip install requests feedparser beautifulsoup4 pyyaml markdown
```

## Usage

### 解析订阅清单
```bash
python3 scripts/worldreader.py parse-subscription \
  --doc-url "https://zcnd9g0cgdok.feishu.cn/wiki/Al3xwSfMkibfFJkj1bycEYsqnKe"
```

### 获取信源内容
```bash
python3 scripts/worldreader.py fetch-content \
  --source-id "source_001" \
  --date "2026-03-27"
```

### 评分文章
```bash
python3 scripts/worldreader.py score-article \
  --article-path "./article.json"
```

### 获取每日文章
```bash
python3 scripts/worldreader.py get-daily-articles \
  --date "2026-03-27" \
  --doc-url "https://..."
```

## Configuration
编辑 `config.yaml` 文件配置缓存、知识库路径、API等信息

## Structure
```
worldreader/
├── lib/                    # 核心库
│   ├── parsers/           # 解析器
│   ├── fetchers/          # 内容获取器
│   ├── generators/        # 文章生成器
│   ├── scorers/           # 评分器
│   └── worldreader.py     # 主入口
├── scripts/               # 命令行工具
├── cache/                 # 缓存目录
├── knowledge_base/        # 知识库
├── quality_scores/        # 质量评分
├── config.yaml            # 配置文件
├── SKILL.md               # 技能文档
└── SPEC.md                # 技术规格
```

## License
MIT
>>>>>>> 6599d9dcee7fb48fe604b1fbee302e087f1998d5
