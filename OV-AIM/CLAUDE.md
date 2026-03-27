# AI 记忆配置

## 📍 当前上下文
- **用户**: [用户名]
- **时区**: Asia/Shanghai (北京时间)
- **语言**: 中文
- **渠道**: 飞书 (Feishu)

## 📚 记忆同步规则

### 何时保存笔记
1. **对话结束时** - 如果讨论了重要内容，保存到 `0-Inbox/Session-Logs/`
2. **发现知识点** - 遇到有价值的信息，保存到 `1-Topics/`
3. **每日简报** - 自动保存到 `0-Inbox/AI-Briefs/`
4. **个人笔记** - 用户自己写到 `5-Personal/`

### 保存到哪个目录
| 内容类型 | 保存路径 | 格式 |
|---------|---------|------|
| 对话摘要 | `0-Inbox/Session-Logs/` | `YYYY-MM-DD-主题.md` |
| AI 新闻简报 | `0-Inbox/AI-Briefs/YYYY/MM/` | `YYYY-MM-DD.md` |
| 知识点 | `1-Topics/分类/` | `主题名.md` |
| 模板 | `3-Templates/` | `模板名.md` |
| 月度总结 | `4-Periodic/Monthly/` | `YYYY-MM.md` |
| 用户个人笔记 | `5-Personal/` | 用户自定义 |