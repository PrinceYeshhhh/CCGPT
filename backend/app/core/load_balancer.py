"""
Load balancer implementation for scaling
"""

import asyncio
import time
import random
from typing import List, Dict, Any, Optional
from enum import Enum
import structlog
import httpx
from datetime import datetime, timedelta

logger = structlog.get_logger()


class LoadBalancingStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    RANDOM = "random"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"


class ServerNode:
    """Represents a server node in the load balancer"""
    
    def __init__(self, url: str, weight: int = 1, health_check_url: str = None):
        self.url = url
        self.weight = weight
        self.health_check_url = health_check_url or f"{url}/health"
        self.active_connections = 0
        self.total_requests = 0
        self.last_health_check = None
        self.is_healthy = True
        self.response_time = 0.0
        self.error_count = 0
        self.last_error_time = None
    
    async def health_check(self) -> bool:
        """Perform health check on this node"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                start_time = time.time()
                response = await client.get(self.health_check_url)
                self.response_time = time.time() - start_time
                
                if response.status_code == 200:
                    self.is_healthy = True
                    self.error_count = 0
                    self.last_health_check = datetime.utcnow()
                    return True
                else:
                    self.is_healthy = False
                    self.error_count += 1
                    self.last_error_time = datetime.utcnow()
                    return False
                    
        except Exception as e:
            logger.warning(f"Health check failed for {self.url}: {e}")
            self.is_healthy = False
            self.error_count += 1
            self.last_error_time = datetime.utcnow()
            return False
    
    def get_score(self) -> float:
        """Get load balancing score for this node"""
        if not self.is_healthy:
            return 0.0
        
        # Lower score is better
        base_score = self.active_connections * 0.7 + self.response_time * 0.3
        
        # Penalize recent errors
        if self.last_error_time:
            time_since_error = (datetime.utcnow() - self.last_error_time).total_seconds()
            if time_since_error < 300:  # 5 minutes
                base_score += 10.0
        
        return base_score


class LoadBalancer:
    """Load balancer with multiple strategies"""
    
    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN):
        self.strategy = strategy
        self.nodes: List[ServerNode] = []
        self.current_index = 0
        self._lock = asyncio.Lock()
        self._health_check_interval = 30  # seconds
        self._health_check_task = None
        self._start_health_checks()
    
    def add_node(self, url: str, weight: int = 1, health_check_url: str = None):
        """Add a server node"""
        node = ServerNode(url, weight, health_check_url)
        self.nodes.append(node)
        logger.info(f"Added node {url} with weight {weight}")
    
    def remove_node(self, url: str):
        """Remove a server node"""
        self.nodes = [node for node in self.nodes if node.url != url]
        logger.info(f"Removed node {url}")
    
    def get_healthy_nodes(self) -> List[ServerNode]:
        """Get list of healthy nodes"""
        return [node for node in self.nodes if node.is_healthy]
    
    async def get_next_node(self) -> Optional[ServerNode]:
        """Get next node based on load balancing strategy"""
        healthy_nodes = self.get_healthy_nodes()
        
        if not healthy_nodes:
            logger.warning("No healthy nodes available")
            return None
        
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return await self._round_robin(healthy_nodes)
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return await self._least_connections(healthy_nodes)
        elif self.strategy == LoadBalancingStrategy.RANDOM:
            return await self._random_selection(healthy_nodes)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return await self._weighted_round_robin(healthy_nodes)
        else:
            return healthy_nodes[0]
    
    async def _round_robin(self, nodes: List[ServerNode]) -> ServerNode:
        """Round robin selection"""
        async with self._lock:
            node = nodes[self.current_index % len(nodes)]
            self.current_index += 1
            return node
    
    async def _least_connections(self, nodes: List[ServerNode]) -> ServerNode:
        """Select node with least active connections"""
        return min(nodes, key=lambda n: n.active_connections)
    
    async def _random_selection(self, nodes: List[ServerNode]) -> ServerNode:
        """Random selection"""
        return random.choice(nodes)
    
    async def _weighted_round_robin(self, nodes: List[ServerNode]) -> ServerNode:
        """Weighted round robin selection"""
        total_weight = sum(node.weight for node in nodes)
        if total_weight == 0:
            return nodes[0]
        
        # Use weighted selection
        random_value = random.uniform(0, total_weight)
        current_weight = 0
        
        for node in nodes:
            current_weight += node.weight
            if random_value <= current_weight:
                return node
        
        return nodes[-1]  # Fallback
    
    async def execute_request(self, method: str, path: str, **kwargs) -> Any:
        """Execute request through load balancer"""
        node = await self.get_next_node()
        if not node:
            raise Exception("No healthy nodes available")
        
        # Increment connection count
        node.active_connections += 1
        node.total_requests += 1
        
        try:
            url = f"{node.url}{path}"
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(method, url, **kwargs)
                return response
        except Exception as e:
            logger.error(f"Request failed on node {node.url}: {e}")
            node.error_count += 1
            node.last_error_time = datetime.utcnow()
            raise
        finally:
            # Decrement connection count
            node.active_connections = max(0, node.active_connections - 1)
    
    def _start_health_checks(self):
        """Start background health check task"""
        if self._health_check_task is None or self._health_check_task.done():
            self._health_check_task = asyncio.create_task(self._health_check_loop())
    
    async def _health_check_loop(self):
        """Background health check loop"""
        while True:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self._health_check_interval)
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(5)  # Short sleep on error
    
    async def _perform_health_checks(self):
        """Perform health checks on all nodes"""
        tasks = [node.health_check() for node in self.nodes]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get load balancer statistics"""
        healthy_nodes = self.get_healthy_nodes()
        
        return {
            'strategy': self.strategy.value,
            'total_nodes': len(self.nodes),
            'healthy_nodes': len(healthy_nodes),
            'nodes': [
                {
                    'url': node.url,
                    'weight': node.weight,
                    'is_healthy': node.is_healthy,
                    'active_connections': node.active_connections,
                    'total_requests': node.total_requests,
                    'response_time': node.response_time,
                    'error_count': node.error_count,
                    'last_health_check': node.last_health_check.isoformat() if node.last_health_check else None
                }
                for node in self.nodes
            ]
        }
    
    def stop(self):
        """Stop the load balancer"""
        if self._health_check_task and not self._health_check_task.done():
            self._health_check_task.cancel()


class ServiceLoadBalancer:
    """Load balancer for specific services"""
    
    def __init__(self):
        self.rag_balancer = LoadBalancer(LoadBalancingStrategy.LEAST_CONNECTIONS)
        self.vector_balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        self.embed_balancer = LoadBalancer(LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN)
    
    def add_rag_node(self, url: str, weight: int = 1):
        """Add RAG service node"""
        self.rag_balancer.add_node(url, weight)
    
    def add_vector_node(self, url: str, weight: int = 1):
        """Add vector service node"""
        self.vector_balancer.add_node(url, weight)
    
    def add_embed_node(self, url: str, weight: int = 1):
        """Add embed service node"""
        self.embed_balancer.add_node(url, weight)
    
    async def execute_rag_request(self, path: str, **kwargs):
        """Execute RAG service request"""
        return await self.rag_balancer.execute_request("POST", path, **kwargs)
    
    async def execute_vector_request(self, path: str, **kwargs):
        """Execute vector service request"""
        return await self.vector_balancer.execute_request("POST", path, **kwargs)
    
    async def execute_embed_request(self, path: str, **kwargs):
        """Execute embed service request"""
        return await self.embed_balancer.execute_request("POST", path, **kwargs)
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all balancers"""
        return {
            'rag_service': self.rag_balancer.get_stats(),
            'vector_service': self.vector_balancer.get_stats(),
            'embed_service': self.embed_balancer.get_stats()
        }
    
    def stop_all(self):
        """Stop all load balancers"""
        self.rag_balancer.stop()
        self.vector_balancer.stop()
        self.embed_balancer.stop()


# Global service load balancer
service_load_balancer = ServiceLoadBalancer()
