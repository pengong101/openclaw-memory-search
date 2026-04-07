#!/usr/bin/env python3
"""
Memory Search v3.0 - 消息搜索技能
支持语义搜索（BGE HTTP API）、关键词搜索、混合搜索

Author: pengong101
Updated: 2026-04-07
License: MIT
Version: 3.1.0

架构：
  Layer 1: BGE HTTP API (bge-embedding 容器，172.17.0.1:5000)
  Layer 2: 关键词搜索（BM25 简化版，始终可用）

更新 (v3.1.0)：
  - 新增 load_all_memories() 函数，自动加载所有智能体记忆
  - 支持主智能体 memory/*.md + 子智能体 MEMORY.md
"""

import json
import os
import glob
import urllib.request
import urllib.error
from typing import List, Dict, Optional
from dataclasses import dataclass

# BGE 服务地址（host.docker.internal 或 Docker 网关 IP）
BGE_API = "http://172.17.0.1:5000"

@dataclass
class SearchResult:
    """搜索结果"""
    content: str
    score: float
    source: str
    timestamp: Optional[str] = None
    metadata: Dict = None


def _call_bge_api(endpoint: str, payload: dict, timeout: float = 30.0) -> Optional[dict]:
    """调用 BGE HTTP API"""
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            f"{BGE_API}{endpoint}",
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, Exception) as e:
        return None


def _is_bge_available() -> bool:
    """检查 BGE 服务是否可用"""
    try:
        req = urllib.request.Request(
            f"{BGE_API}/health",
            headers={'Content-Type': 'application/json'},
            method='GET'
        )
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            return resp.status == 200
    except Exception:
        return False


class MemorySearchV3:
    """消息搜索 v3.0"""
    
    def __init__(self):
        self._bge_available = None  # 缓存健康状态
    
    def is_semantic_available(self) -> bool:
        """检查语义搜索是否可用"""
        if self._bge_available is None:
            self._bge_available = _is_bge_available()
        return self._bge_available
    
    def search(self, query: str, memory_chunks: List[Dict], 
               top_k: int = 5, min_score: float = 0.3) -> List[SearchResult]:
        """
        语义搜索（优先 BGE API，降级关键词搜索）
        
        Args:
            query: 搜索查询
            memory_chunks: 记忆片段列表 [{content, source, timestamp, ...}, ...]
            top_k: 返回结果数量
            min_score: 最低分数阈值
            
        Returns:
            搜索结果列表
        """
        if not memory_chunks:
            return []
        
        # 尝试 BGE 语义搜索
        if self.is_semantic_available():
            try:
                documents = [chunk.get('content', '') for chunk in memory_chunks]
                result = _call_bge_api('/search', {
                    'query': query,
                    'documents': documents,
                    'top_k': top_k * 2  # 多取一些，过滤低于阈值的
                }, timeout=30.0)
                
                if result and 'results' in result:
                    search_results = []
                    for r in result['results']:
                        idx = r.get('index', -1)
                        score = r.get('score', 0)
                        if score >= min_score and 0 <= idx < len(memory_chunks):
                            chunk = memory_chunks[idx]
                            search_results.append(SearchResult(
                                content=chunk.get('content', ''),
                                score=float(score),
                                source=chunk.get('source', 'unknown'),
                                timestamp=chunk.get('timestamp'),
                                metadata=chunk
                            ))
                    if search_results:
                        return search_results[:top_k]
            except Exception:
                self._bge_available = False  # 缓存失败状态
        
        # 降级到关键词搜索
        return self.keyword_search(query, memory_chunks, top_k)
    
    def keyword_search(self, query: str, memory_chunks: List[Dict],
                      top_k: int = 5) -> List[SearchResult]:
        """
        关键词搜索（BM25 简化版）
        
        Args:
            query: 搜索查询
            memory_chunks: 记忆片段列表
            top_k: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        if not memory_chunks:
            return []
        
        query_terms = set(query.lower().split())
        
        results = []
        for chunk in memory_chunks:
            content = chunk.get('content', '').lower()
            content_terms = set(content.split())
            overlap = len(query_terms & content_terms)
            score = overlap / max(len(query_terms), 1)
            
            if score > 0:
                results.append(SearchResult(
                    content=chunk.get('content', ''),
                    score=score,
                    source=chunk.get('source', 'unknown'),
                    timestamp=chunk.get('timestamp'),
                    metadata=chunk
                ))
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def hybrid_search(self, query: str, memory_chunks: List[Dict],
                     top_k: int = 5, semantic_weight: float = 0.7) -> List[SearchResult]:
        """
        混合搜索（语义 + 关键词）
        
        Args:
            query: 搜索查询
            memory_chunks: 记忆片段列表
            top_k: 返回结果数量
            semantic_weight: 语义搜索权重
            
        Returns:
            搜索结果列表
        """
        semantic_results = self.search(query, memory_chunks, top_k=top_k * 2)
        keyword_results = self.keyword_search(query, memory_chunks, top_k=top_k * 2)
        
        merged = {}
        for r in semantic_results:
            merged[r.content] = (r, r.score * semantic_weight)
        
        for r in keyword_results:
            if r.content in merged:
                existing = merged[r.content]
                new_score = existing[1] + r.score * (1 - semantic_weight)
                merged[r.content] = (r, new_score)
            else:
                merged[r.content] = (r, r.score * (1 - semantic_weight))
        
        results = sorted(merged.values(), key=lambda x: x[1], reverse=True)
        return [r[0] for r in results[:top_k]]
    
    def contextual_search(self, query: str, context: List[str],
                         memory_chunks: List[Dict], top_k: int = 5) -> List[SearchResult]:
        """
        上下文感知搜索
        
        Args:
            query: 当前查询
            context: 对话上下文
            memory_chunks: 记忆片段列表
            top_k: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        expanded_query = " ".join(context[-3:]) + " " + query
        return self.search(expanded_query, memory_chunks, top_k=top_k)


# 全局实例
_searcher = None

def get_searcher() -> MemorySearchV3:
    """获取搜索器实例"""
    global _searcher
    if _searcher is None:
        _searcher = MemorySearchV3()
    return _searcher

def load_all_memories(workspace_path: str = '/root/.openclaw/workspace') -> List[Dict]:
    """
    加载所有智能体的记忆文件
    
    包括：
    1. 主智能体 workspace_path/memory/*.md
    2. 子智能体 /root/.openclaw/workspace-{agent}/MEMORY.md (content, research, code, ops, review)
    
    Args:
        workspace_path: 工作区路径，默认 /root/.openclaw/workspace
        
    Returns:
        记忆片段列表 [{content, source}, ...]
    """
    memory_chunks = []
    
    # 1. 主智能体 memory/ 目录
    memory_dir = os.path.join(workspace_path, 'memory')
    if os.path.isdir(memory_dir):
        for f in sorted(glob.glob(os.path.join(memory_dir, '*.md'))):
            try:
                with open(f) as fp:
                    memory_chunks.append({
                        'content': fp.read(),
                        'source': f'memory/{os.path.basename(f)}'
                    })
            except Exception:
                pass
    
    # 2. 子智能体 MEMORY.md（在 /root/.openclaw/workspace-{agent}/）
    base_dir = os.path.dirname(workspace_path.rstrip('/'))  # /root/.openclaw
    sub_agents = ['content', 'research', 'code', 'ops', 'review']
    for agent in sub_agents:
        mem_file = os.path.join(base_dir, f'workspace-{agent}', 'MEMORY.md')
        try:
            if os.path.isfile(mem_file):
                with open(mem_file) as fp:
                    memory_chunks.append({
                        'content': fp.read(),
                        'source': f'workspace-{agent}/MEMORY.md'
                    })
        except Exception:
            pass
    
    return memory_chunks


def search_memory(query: str, memory_chunks: List[Dict] = None, 
                 top_k: int = 5, min_score: float = 0.3,
                 auto_load: bool = True) -> List[Dict]:
    """
    搜索记忆（兼容旧接口）
    
    Args:
        query: 搜索查询
        memory_chunks: 记忆片段列表（如果为 None，自动加载所有记忆）
        top_k: 返回结果数量
        min_score: 最低分数阈值
        auto_load: 是否自动加载记忆（当 memory_chunks 为 None 时）
        
    Returns:
        搜索结果列表
    """
    # 自动加载所有记忆
    if memory_chunks is None and auto_load:
        memory_chunks = load_all_memories()
    
    searcher = get_searcher()
    results = searcher.search(query, memory_chunks or [], top_k=top_k, min_score=min_score)
    return [
        {
            'content': r.content,
            'score': r.score,
            'source': r.source,
            'timestamp': r.timestamp,
            **r.metadata
        }
        for r in results
    ]

if __name__ == "__main__":
    print("🔍 Memory Search v3.0")
    print("=" * 50)
    
    searcher = MemorySearchV3()
    
    # 检查 BGE 状态
    print(f"\nBGE 服务状态: {'✅ 可用' if searcher.is_semantic_available() else '❌ 不可用（使用关键词搜索）'}")
    
    # 测试数据
    memories = [
        {'content': 'OpenClaw 配置文件在 /root/.openclaw/openclaw.json', 'source': 'config'},
        {'content': 'SearXNG 端口是 8081', 'source': 'search'},
        {'content': 'Clash 代理端口是 7890', 'source': 'proxy'},
        {'content': 'BGE 模型部署在 Docker 容器中，端口 5000', 'source': 'embedding'},
    ]
    
    # 语义搜索
    print("\n1. 语义搜索:")
    results = searcher.search("OpenClaw 配置在哪里？", memories, top_k=2)
    for r in results:
        print(f"  [{r.score:.3f}] {r.content}")
    
    # 关键词搜索
    print("\n2. 关键词搜索:")
    results = searcher.keyword_search("端口", memories, top_k=3)
    for r in results:
        print(f"  [{r.score:.3f}] {r.content}")
    
    # 混合搜索
    print("\n3. 混合搜索:")
    results = searcher.hybrid_search("端口", memories, top_k=3)
    for r in results:
        print(f"  [{r.score:.3f}] {r.content}")
    
    print("\n✅ 测试完成")
