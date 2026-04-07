# Changelog

## v3.1.0 (2026-04-07)

### Added
- 子智能体记忆自动加载（content, research, code, ops, review）
- `load_all_memories()` 函数自动扫描所有智能体记忆
- `search_memory()` 新增 `auto_load` 参数

### Changed
- 默认 workspace 路径修正为 `/root/.openclaw/workspace`
- 子智能体路径从 `workspace/workspace-{agent}` 修正为 `workspace-{agent}`

### Fixed
- 路径计算错误导致子智能体记忆无法加载

---

## v3.0.0 (2026-04-05)

### Added
- BGE HTTP API 语义搜索
- 关键词搜索降级方案
- 混合搜索模式
- SKILL.md 文档

### Features
- Layer 1: BGE HTTP API (http://172.17.0.1:5000)
- Layer 2: BM25 简化版关键词搜索
