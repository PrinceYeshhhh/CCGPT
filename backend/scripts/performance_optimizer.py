#!/usr/bin/env python3
"""
Performance Optimization Script
Automated performance analysis and optimization recommendations
"""

import asyncio
import argparse
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add the backend directory to the Python path
sys.path.append('/app')

from app.core.config import settings
from app.services.performance_service import performance_service
from app.services.query_optimizer import db_optimizer
from app.services.cache_service import cache_service
from app.core.database import db_manager

class PerformanceOptimizerCLI:
    """Command-line interface for performance optimization"""
    
    def __init__(self):
        self.performance_service = performance_service
        self.db_optimizer = db_optimizer
        self.cache_service = cache_service
    
    async def analyze_performance(self, hours: int = 24) -> Dict[str, Any]:
        """Analyze current performance"""
        print(f"🔍 Analyzing performance for the last {hours} hours...")
        
        # Get performance dashboard
        dashboard = await self.performance_service.get_performance_dashboard()
        
        # Get query performance analysis
        query_analysis = await self.db_optimizer.analyze_query_performance()
        
        # Get database stats
        db_stats = await self.db_optimizer.get_database_stats()
        
        # Get cache stats
        cache_stats = await self.cache_service.get_stats()
        
        return {
            "dashboard": dashboard,
            "query_analysis": query_analysis,
            "database_stats": db_stats,
            "cache_stats": cache_stats,
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    async def get_recommendations(self) -> List[Dict[str, Any]]:
        """Get optimization recommendations"""
        print("📋 Generating optimization recommendations...")
        
        recommendations = await self.performance_service.optimizer.analyze_performance()
        
        return [
            {
                "category": rec.category,
                "priority": rec.priority,
                "title": rec.title,
                "description": rec.description,
                "impact": rec.impact,
                "effort": rec.effort,
                "current_value": rec.current_value,
                "recommended_value": rec.recommended_value,
                "estimated_improvement": rec.estimated_improvement
            }
            for rec in recommendations
        ]
    
    async def optimize_database(self, apply_changes: bool = False) -> Dict[str, Any]:
        """Optimize database performance"""
        print("🗄️ Analyzing database performance...")
        
        # Get connection pool analysis
        pool_analysis = await self.db_optimizer.optimize_connection_pool()
        
        # Get index suggestions
        index_suggestions = await self.db_optimizer.suggest_indexes()
        
        # Get query performance
        query_performance = await self.db_optimizer.analyze_query_performance()
        
        optimization_results = {
            "connection_pool": pool_analysis,
            "index_suggestions": index_suggestions,
            "query_performance": query_performance,
            "optimization_timestamp": datetime.now().isoformat()
        }
        
        if apply_changes:
            print("⚠️  Applying database optimizations...")
            # Here you would implement actual optimization application
            # For now, we'll just log what would be done
            print("   - Connection pool optimizations would be applied")
            print("   - Index suggestions would be implemented")
            print("   - Query optimizations would be applied")
        
        return optimization_results
    
    async def optimize_cache(self, clear_cache: bool = False) -> Dict[str, Any]:
        """Optimize cache performance"""
        print("💾 Analyzing cache performance...")
        
        # Get cache statistics
        cache_stats = await self.cache_service.get_stats()
        
        # Get cache recommendations
        recommendations = []
        
        if cache_stats.get("hit_rate", 0) < 0.7:
            recommendations.append({
                "type": "low_hit_rate",
                "description": f"Cache hit rate is {cache_stats.get('hit_rate', 0):.1%}, below optimal 70%",
                "action": "Review cache TTL settings and key patterns"
            })
        
        if cache_stats.get("total_requests", 0) > 10000 and cache_stats.get("hits", 0) < 5000:
            recommendations.append({
                "type": "inefficient_caching",
                "description": "High request volume with low cache hits",
                "action": "Implement more aggressive caching strategies"
            })
        
        optimization_results = {
            "cache_stats": cache_stats,
            "recommendations": recommendations,
            "optimization_timestamp": datetime.now().isoformat()
        }
        
        if clear_cache:
            print("🧹 Clearing cache...")
            success = await self.cache_service.clear()
            optimization_results["cache_cleared"] = success
            print(f"   Cache cleared: {'Success' if success else 'Failed'}")
        
        return optimization_results
    
    async def generate_report(self, output_file: str = None) -> str:
        """Generate comprehensive performance report"""
        print("📊 Generating comprehensive performance report...")
        
        # Collect all performance data
        performance_data = await self.analyze_performance()
        recommendations = await self.get_recommendations()
        db_optimization = await self.optimize_database()
        cache_optimization = await self.optimize_cache()
        
        # Generate report
        report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "analyzer_version": "1.0.0",
                "environment": settings.ENVIRONMENT
            },
            "performance_analysis": performance_data,
            "optimization_recommendations": recommendations,
            "database_optimization": db_optimization,
            "cache_optimization": cache_optimization,
            "summary": self._generate_summary(recommendations, performance_data)
        }
        
        # Save report
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"📄 Report saved to {output_file}")
        
        return json.dumps(report, indent=2, default=str)
    
    def _generate_summary(self, recommendations: List[Dict], performance_data: Dict) -> Dict[str, Any]:
        """Generate performance summary"""
        total_recommendations = len(recommendations)
        high_priority = len([r for r in recommendations if r["priority"] == "high"])
        medium_priority = len([r for r in recommendations if r["medium"] == "medium"])
        
        # Get current metrics
        current_metrics = performance_data.get("dashboard", {}).get("current_metrics", {})
        
        # Calculate performance score
        performance_score = 100
        if current_metrics.get("cpu_percent", 0) > 80:
            performance_score -= 20
        if current_metrics.get("memory_percent", 0) > 85:
            performance_score -= 20
        if current_metrics.get("response_time_p95", 0) > 2.0:
            performance_score -= 30
        if current_metrics.get("error_rate", 0) > 0.05:
            performance_score -= 30
        
        performance_score = max(0, performance_score)
        
        return {
            "performance_score": performance_score,
            "total_recommendations": total_recommendations,
            "high_priority_issues": high_priority,
            "medium_priority_issues": medium_priority,
            "critical_issues": high_priority,
            "performance_status": "excellent" if performance_score >= 90 else "good" if performance_score >= 70 else "needs_attention" if performance_score >= 50 else "critical"
        }
    
    async def run_optimization_cycle(self, apply_changes: bool = False) -> Dict[str, Any]:
        """Run a complete optimization cycle"""
        print("🚀 Starting performance optimization cycle...")
        
        results = {}
        
        # 1. Analyze current performance
        results["analysis"] = await self.analyze_performance()
        
        # 2. Get recommendations
        results["recommendations"] = await self.get_recommendations()
        
        # 3. Optimize database
        results["database_optimization"] = await self.optimize_database(apply_changes)
        
        # 4. Optimize cache
        results["cache_optimization"] = await self.optimize_cache(apply_changes)
        
        # 5. Generate summary
        results["summary"] = self._generate_summary(
            results["recommendations"], 
            results["analysis"]
        )
        
        print("✅ Optimization cycle completed!")
        return results

async def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="Performance Optimization Tool")
    parser.add_argument("--analyze", action="store_true", help="Analyze current performance")
    parser.add_argument("--recommendations", action="store_true", help="Get optimization recommendations")
    parser.add_argument("--optimize-db", action="store_true", help="Optimize database performance")
    parser.add_argument("--optimize-cache", action="store_true", help="Optimize cache performance")
    parser.add_argument("--optimize-all", action="store_true", help="Run complete optimization cycle")
    parser.add_argument("--apply-changes", action="store_true", help="Apply optimization changes")
    parser.add_argument("--clear-cache", action="store_true", help="Clear cache during optimization")
    parser.add_argument("--hours", type=int, default=24, help="Hours of data to analyze")
    parser.add_argument("--output", type=str, help="Output file for report")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format")
    
    args = parser.parse_args()
    
    optimizer = PerformanceOptimizerCLI()
    
    try:
        if args.analyze:
            result = await optimizer.analyze_performance(args.hours)
            print(json.dumps(result, indent=2, default=str))
        
        elif args.recommendations:
            result = await optimizer.get_recommendations()
            print(json.dumps(result, indent=2, default=str))
        
        elif args.optimize_db:
            result = await optimizer.optimize_database(args.apply_changes)
            print(json.dumps(result, indent=2, default=str))
        
        elif args.optimize_cache:
            result = await optimizer.optimize_cache(args.clear_cache)
            print(json.dumps(result, indent=2, default=str))
        
        elif args.optimize_all:
            result = await optimizer.run_optimization_cycle(args.apply_changes)
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(result, f, indent=2, default=str)
                print(f"Report saved to {args.output}")
            else:
                print(json.dumps(result, indent=2, default=str))
        
        else:
            # Default: generate comprehensive report
            report = await optimizer.generate_report(args.output)
            if not args.output:
                print(report)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
