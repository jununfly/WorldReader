# WorldReader FIXME 问题记录

## 测试时间
2026-04-01

## 测试任务
使用 WorldReader 获取订阅列表 `config/sources.yaml` 中昨天的文章（2026-03-31）

## 订阅源
```yaml
- 清华大学人工智能国际治理研究院 (baai)
- Google Brain (baai)
- 极客公园 (baai)
- 量子位 (baai)
- 新智元 (baai)
```

## 发现的问题

### 问题 1: 浏览器端口被占用

**错误信息**:
```
Error: PortInUseError: Port 15311 is already in use.
```

**原因**: 浏览器工具端口 15311 被之前的会话占用

**影响**: 导致 BaaFetcher 无法使用 browser tool 获取页面内容

**临时解决方案**: 清理浏览器会话

**永久解决方案**:
- 在 BaaFetcher 中添加端口冲突检测和重试机制
- 或者使用浏览器工具的重连功能

---

### 问题 2: 批量处理脚本挂起

**现象**: 运行 `batch_process.py` 时，脚本长时间无响应

**命令**:
```bash
python3 scripts/batch_process.py --date 2026-03-31 --sources config/sources.yaml --min-score 60 --json
```

**原因分析**:
1. 可能是 browser tool 等待用户输入
2. 可能是网络请求超时没有正确处理
3. 可能是某个 fetcher 阻塞了

**待验证**:
- 检查是否有交互式提示
- 检查超时设置是否生效
- 检查是否有死循环

---

### 问题 3: batch_process.py 作为模块导入失败

**错误**:
```python
No module named 'batch_process'
```

**原因**: `scripts/batch_process.py` 不在 Python 路径中

**影响**: 无法在其他脚本中复用 batch_process 的功能

**解决方案**:
- 在脚本中正确设置 `sys.path`
- 或者将 batch_process 移到 lib 目录
- 或者添加 `__init__.py` 到 scripts 目录

---

### 问题 4: 质量评分结果为空

**现象**: `quality_scores/2026-03-31/` 目录下没有评分文件

**原因**: 没有成功获取到文章内容

**待调查**:
- BaaFetcher 的解析逻辑是否正确
- 浏览器快照解析是否成功
- 文章内容提取是否有误

---

### 问题 5: cache/sources/ 目录不存在

**现象**: `cache/sources/` 目录为空

**原因**: 订阅清单未使用，直接使用了 `config/sources.yaml`

**说明**: 这是设计上的选择，不是 bug，但文档可能需要更新

---

## 待测试功能

- [ ] BaaFetcher 单独测试（不通过 batch_process）
- [ ] ObsidianSaver 保存功能测试
- [ ] 质量评分功能测试
- [ ] 批量处理超时机制测试
- [ ] 错误处理和日志记录测试

## 建议的改进

1. **添加更详细的日志**: 在每个关键步骤添加日志输出
2. **添加进度显示**: 在批量处理时显示当前进度
3. **添加超时保护**: 确保每个操作都有合理的超时时间
4. **添加错误恢复**: 失败的信源不应阻塞其他信源的处理
5. **添加单元测试**: 为每个模块添加单元测试
6. **文档更新**: 更新 SKILL.md 说明直接使用 config/sources.yaml 的方式

## 测试环境

- Python: 3.x
- WorldReader: main branch (commit 7fe98c1)
- 日期: 2026-04-01