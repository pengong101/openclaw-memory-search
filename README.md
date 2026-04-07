# Memory Search 技能

**语义记忆搜索技能** - 支持 BGE embedding 模型的中文语义搜索。

## 功能

- 🔍 **语义搜索**：基于 BGE embedding 的语义相似度搜索
- 🔑 **关键词搜索**：BM25 简化版降级方案
- 🔀 **混合搜索**：语义 + 关键词融合
- 👥 **多智能体支持**：自动加载所有智能体记忆

## 安装

### 方式 1：ClawHub 自动安装（推荐）

```
/openclaw skill install memory-search
```

### 方式 2：手动安装

```bash
# 下载技能包
wget https://github.com/pengong101/openclaw-memory-search/archive/refs/tags/v3.1.0.tar.gz

# 解压到 skills 目录
tar -xzf v3.1.0.tar.gz
mv memory-search-v3.1.0 /root/.openclaw/skills/memory-search
```

## 使用

### Python API

```python
import sys
sys.path.insert(0, '/root/.openclaw/skills/memory-search')
from memory_search import search_memory, load_all_memories

# 自动加载并搜索（推荐）
results = search_memory('智能体工作', top_k=5)

# 手动控制
memories = load_all_memories()
results = search_memory('查询', memory_chunks=memories, top_k=5)
```

### 命令行

```bash
python3 memory_search.py
# 输出测试结果
```

## 配置

### BGE 服务

技能依赖 BGE embedding 服务运行在 `http://172.17.0.1:5000`。

```bash
# 检查服务状态
curl http://172.17.0.1:5000/health
```

返回 `{"status": "healthy", "model": "BAAI/bge-small-zh-v1.5", "loaded": true}` 即正常。

### 模型信息

- **模型**：BAAI/bge-small-zh-v1.5
- **维度**：512
- **语言**：中文优化

## 记忆来源

自动加载以下记忆：

| 智能体 | 路径 | 数量 |
|--------|------|------|
| 主智能体 | `workspace/memory/*.md` | 29个 |
| content | `workspace-content/MEMORY.md` | 1个 |
| research | `workspace-research/MEMORY.md` | 1个 |
| code | `workspace-code/MEMORY.md` | 1个 |
| ops | `workspace-ops/MEMORY.md` | 1个 |
| review | `workspace-review/MEMORY.md` | 1个 |

## 依赖

- Python 3.7+
- BGE embedding 服务（或降级到关键词搜索）

## 许可证

MIT License

## 作者

[pengong101](https://github.com/pengong101)
