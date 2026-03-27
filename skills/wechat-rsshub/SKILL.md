---
name: wechat-rsshub
description: 通过 RSSHub 获取微信公众号文章内容
author: Mose
version: 1.0.0
triggers:
  - "微信公众号"
  - "公众号文章"
  - "wechat"
  - "rsshub"
metadata: {"clawdbot":{"requires":{"bins":["curl","python3"]}}}
---

# 微信公众号 RSSHub 集成

通过本地 RSSHub 服务获取微信公众号文章内容。

## RSSHub 地址

```bash
RSSHub_URL="http://127.0.0.1:12000"
```

## 使用方法

### 1. 获取公众号文章列表

```bash
# 公众号需要 ID（不是名称）
curl "http://127.0.0.1:12000/wechat/mp/msgbox/公众号 ID"
```

### 2. 获取公众号 ID

可以通过以下方式获取：
- 公众号主页 URL 中的 `__biz` 参数
- 使用搜狗微信搜索

### 3. Python 调用示例

```python
import requests
import feedparser

RSSHub_URL = "http://127.0.0.1:12000"

def get_wechat_articles(mp_id):
    """获取公众号文章"""
    url = f"{RSSHub_URL}/wechat/mp/msgbox/{mp_id}"
    response = requests.get(url)
    feed = feedparser.parse(response.content)
    
    articles = []
    for entry in feed.entries:
        articles.append({
            'title': entry.title,
            'link': entry.link,
            'published': entry.published,
            'summary': entry.summary
        })
    return articles

# 使用示例
articles = get_wechat_articles("MjM5MTQzMTY3")
for article in articles:
    print(f"标题：{article['title']}")
    print(f"链接：{article['link']}")
    print("---")
```

## 获取公众号 ID 方法

### 方法 1：从公众号主页
1. 打开公众号任意文章
2. 查看 URL 中的 `__biz` 参数
3. 复制该值即为公众号 ID

### 方法 2：搜狗微信搜索
```bash
# 搜索公众号名称
curl "https://weixin.sogou.com/weixin?type=1&query=公众号名称"
```

## 保存到 Obsidian

```python
def save_to_obsidian(articles, output_path):
    """保存文章到 Obsidian"""
    for article in articles:
        filename = f"{output_path}/{article['published'][:10]}-{article['title']}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# {article['title']}\n\n")
            f.write(f"发布时间：{article['published']}\n")
            f.write(f"原文链接：{article['link']}\n\n")
            f.write(f"## 摘要\n\n{article['summary']}\n")
```

## 定时任务配置

```json
{
  "name": "每日公众号文章",
  "schedule": {
    "kind": "cron",
    "expr": "0 9 * * *",
    "tz": "Asia/Shanghai"
  },
  "payload": {
    "kind": "agentTurn",
    "message": "获取指定公众号最新文章并保存到 Obsidian"
  },
  "sessionTarget": "isolated"
}
```

## 注意事项

1. RSSHub 需要保持运行状态
2. 部分公众号可能有反爬限制
3. 建议配置 User-Agent 避免被封
4. 定期更新 RSSHub 镜像获取最新路由
