# WorldReader FIXME

创建时间：2026-03-31
状态：待处理

---

## 🔴 P0 - 立即修复

### 1. 实现 BilibiliFetcher

**问题**：SPEC.md 声明支持 B站视频，但代码中未实现

**位置**：`lib/fetchers/bilibili_fetcher.py` (需创建)

**实现要点**：
- 使用 yt-dlp 或 bilibili-api 获取视频信息
- 提取视频标题、简介、字幕
- 继承 ContentFetcher 基类
- 实现标准化内容输出

**依赖**：
```bash
pip install yt-dlp bilibili-api
```

**参考代码框架**：
```python
from .content_fetcher import ContentFetcher
import yt_dlp
from typing import List, Dict

class BilibiliFetcher(ContentFetcher):
    def __init__(self, config: Dict = None):
        super().__init__(config)

    def fetch(self, source: Dict, date: str) -> List[Dict]:
        url = source.get('url')
        options = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['zh-CN'],
        }
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
            # 标准化为 ContentFetcher 格式
            return [self._normalize_content(info, source)]
```

**注册到 WorldReader**：
```python
# lib/worldreader.py
def _register_fetchers(self) -> None:
    # ... 现有代码 ...
    self.fetchers['bilibili'] = BilibiliFetcher(self.config.get('content_fetcher', {}))
```

---

### 2. 实现 YouTubeFetcher

**问题**：SPEC.md 声明支持 YouTube，但代码中未实现

**位置**：`lib/fetchers/youtube_fetcher.py` (需创建)

**实现要点**：
- 集成 youtube-transcript skill
- 或使用 YouTube Data API v3
- 处理字幕提取

**依赖**：
```bash
pip install google-api-python-client
```

**注册到 WorldReader**：
```python
self.fetchers['youtube'] = YouTubeFetcher(self.config.get('content_fetcher', {}))
```

---

### 3. 配置文件更新

**位置**：`config.yaml`

**添加内容**：
```yaml
content_fetcher:
  bilibili:
    enabled: true
    api_base: "https://api.bilibili.com"
  youtube:
    enabled: true
    api_key: "${YOUTUBE_API_KEY}"
```

---

## 🟡 P1 - 近期改进

### 4. 创建 RssFetcher

**位置**：`lib/fetchers/rss_fetcher.py` (需创建)

**原因**：当前 RSS 复用 WebsiteFetcher，逻辑不同

**实现要点**：
- 使用 feedparser 库
- 独立的 RSS feed 解析逻辑

**依赖**：
```bash
pip install feedparser
```

---

### 5. 完善错误处理

**位置**：创建 `lib/errors.py`

**内容**：
```python
class WorldReaderError(Exception):
    error_code = "ERR_UNKNOWN"

class ContentFetchFailedError(WorldReaderError):
    error_code = "ERR_CONTENT_FETCH_FAILED"

class SubscriptionNotFoundError(WorldReaderError):
    error_code = "ERR_SUBSCRIPTION_NOT_FOUND"
```

**使用**：
```python
try:
    content = self.fetcher.fetch(source, date)
except ContentFetchFailedError as e:
    self.logger.error(f"Failed to fetch: {e.message}")
    return {"error": e.error_code, "message": str(e)}
```

---

### 6. 添加日志支持

**位置**：`lib/worldreader.py`

**修改**：
```python
import logging

class WorldReader:
    def __init__(self, config_path: str = "./config.yaml"):
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.logger = logging.getLogger(__name__)

    def _setup_logging(self):
        log_config = self.config.get('logging', {})
        logging.basicConfig(
            level=getattr(logging, log_config.get('level', 'INFO')),
            format=log_config.get('format', '%(asctime)s [%(levelname)s] %(name)s: %(message)s'),
            filename=log_config.get('file'),
        )
```

---

## 🟢 P2 - 中期优化

### 7. 插件化架构

**重构目标**：
- 解耦 core 和 plugins
- 支持动态加载 fetcher

**新增文件**：
```
lib/core/registry.py  # Fetcher 注册中心
lib/core/pipeline.py  # 处理管道
```

---

### 8. 配置增强

**新增配置文件**：
```
sources.yaml  # 多信源配置
pipelines.yaml  # 处理流程配置
```

---

### 9. CLI 扩展

**新增命令**：
```bash
worldreader.py batch-process  # 批量处理
worldreader.py configure      # 交互式配置
worldreader.py monitor        # 监控模式
worldreader.py plugin list    # 插件列表
```

---

## 任务跟踪

| 任务 | 优先级 | 状态 | 负责人 | 预计完成 |
|------|--------|------|--------|----------|
| BilibiliFetcher | P0 | ⏳ 待开始 | - | - |
| YouTubeFetcher | P0 | ⏳ 待开始 | - | - |
| 注册新 fetcher | P0 | ⏳ 待开始 | - | - |
| RssFetcher | P1 | ⏳ 待开始 | - | - |
| 错误处理 | P1 | ⏳ 待开始 | - | - |
| 日志支持 | P1 | ⏳ 待开始 | - | - |

---

*最后更新：2026-03-31*