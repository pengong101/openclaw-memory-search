# Memory Search 技能

**版本：** 3.1.0  
**类型：** 工具技能  
**优先级：** 高

## 功能

语义记忆搜索，支持：
- BGE embedding 语义搜索（中文优化）
- 关键词搜索降级
- 混合搜索模式
- **自动加载所有智能体记忆（v3.1.0 新增）**

## 触发条件

当用户询问以下内容时激活：
- "之前是怎么处理的"
- "我的记忆中有"
- "之前做过什么"
- "搜索记忆"
- 任何需要查询历史记忆的场景

## 技术架构

```
Layer 1: BGE HTTP API (http://172.17.0.1:5000)
Layer 2: 关键词搜索（BM25 简化版，始终可用）
```

## 记忆来源

自动加载以下记忆：
1. **主智能体** `workspace/memory/*.md`（29个文件）
2. **子智能体** `workspace-{agent}/MEMORY.md`（5个文件）
   - content, research, code, ops, review

## 使用方式

### 方式 1：自动加载（推荐）
```python
import sys
sys.path.insert(0, '/root/.openclaw/workspace/skills/skills/memory_search')
from memory_search import search_memory

results = search_memory('智能体工作流配置', top_k=5)
# 自动加载所有智能体记忆
```

### 方式 2：手动指定记忆
```python
import sys
sys.path.insert(0, '/root/.openclaw/workspace/skills/skills/memory_search')
from memory_search import MemorySearchV3, load_all_memories

# 加载所有记忆
memories = load_all_memories()

# 搜索
searcher = MemorySearchV3()
results = searcher.search('查询', memories, top_k=5)
```

### 方式 3：指定记忆列表
```python
from memory_search import search_memory

memories = [
    {'content': '记忆内容', 'source': '文件路径'},
]
results = search_memory('查询', memory_chunks=memories, auto_load=False)
```

## 搜索结果格式

```python
@dataclass
class SearchResult:
    content: str      # 记忆内容
    score: float     # 相似度分数
    source: str      # 来源文件
    timestamp: str   # 时间戳（可选）
    metadata: dict   # 元数据（可选）
```

## API 函数

| 函数 | 说明 |
|------|------|
| `search_memory(query, ...)` | 搜索记忆（自动加载） |
| `load_all_memories()` | 加载所有智能体记忆 |
| `MemorySearchV3().search()` | 语义搜索 |
| `MemorySearchV3().keyword_search()` | 关键词搜索 |
| `MemorySearchV3().hybrid_search()` | 混合搜索 |

## 依赖

- BGE Docker 服务运行在 `http://172.17.0.1:5000`
- 模型：`BAAI/bge-small-zh-v1.5`

## 健康检查

```bash
curl http://172.17.0.1:5000/health
```

返回 `{"status": "healthy", "model": "BAAI/bge-small-zh-v1.5", "loaded": true}` 即正常。
