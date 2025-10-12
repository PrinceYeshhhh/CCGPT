#!/usr/bin/env python3
"""
Test coverage analysis script for CustomerCareGPT
Analyzes test coverage and identifies gaps
"""

import os
import sys
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple, Any
import argparse

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


class CoverageAnalyzer:
    """Analyzes test coverage and identifies gaps"""
    
    def __init__(self, backend_dir: Path):
        self.backend_dir = backend_dir
        self.app_dir = backend_dir / "app"
        self.coverage_file = backend_dir / "coverage.xml"
        self.html_coverage_dir = backend_dir / "htmlcov"
        
        self.coverage_data = {}
        self.file_coverage = {}
        self.missing_lines = {}
        self.critical_gaps = []
    
    def analyze_coverage(self) -> Dict[str, Any]:
        """Analyze test coverage and generate report"""
        print("📊 Analyzing Test Coverage...")
        print("=" * 50)
        
        # Parse coverage data
        self._parse_coverage_xml()
        
        # Analyze file coverage
        self._analyze_file_coverage()
        
        # Identify critical gaps
        self._identify_critical_gaps()
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        # Create report
        report = {
            "overall_coverage": self._calculate_overall_coverage(),
            "file_coverage": self.file_coverage,
            "missing_lines": self.missing_lines,
            "critical_gaps": self.critical_gaps,
            "recommendations": recommendations,
            "summary": self._generate_summary()
        }
        
        return report
    
    def _parse_coverage_xml(self):
        """Parse coverage XML file"""
        if not self.coverage_file.exists():
            print("❌ Coverage file not found. Run tests with coverage first.")
            return
        
        try:
            tree = ET.parse(self.coverage_file)
            root = tree.getroot()
            
            # Extract overall coverage
            self.coverage_data = {
                "line_rate": float(root.attrib.get("line-rate", 0)),
                "branch_rate": float(root.attrib.get("branch-rate", 0)),
                "lines_covered": int(root.attrib.get("lines-covered", 0)),
                "lines_valid": int(root.attrib.get("lines-valid", 0)),
                "branches_covered": int(root.attrib.get("branches-covered", 0)),
                "branches_valid": int(root.attrib.get("branches-valid", 0))
            }
            
            # Parse individual file coverage
            for package in root.findall("packages/package"):
                for class_elem in package.findall("classes/class"):
                    filename = class_elem.attrib["filename"]
                    if filename.startswith("app/"):
                        self._parse_file_coverage(class_elem, filename)
            
            print("✅ Coverage data parsed successfully")
            
        except Exception as e:
            print(f"❌ Error parsing coverage file: {e}")
    
    def _parse_file_coverage(self, class_elem, filename: str):
        """Parse coverage for a specific file"""
        file_data = {
            "filename": filename,
            "line_rate": float(class_elem.attrib.get("line-rate", 0)),
            "branch_rate": float(class_elem.attrib.get("branch-rate", 0)),
            "lines_covered": int(class_elem.attrib.get("lines-covered", 0)),
            "lines_valid": int(class_elem.attrib.get("lines-valid", 0)),
            "missing_lines": [],
            "partial_lines": []
        }
        
        # Parse line coverage
        for line in class_elem.findall("lines/line"):
            line_number = int(line.attrib["number"])
            hits = int(line.attrib.get("hits", 0))
            
            if hits == 0:
                file_data["missing_lines"].append(line_number)
            elif line.attrib.get("condition-coverage") and "0%" in line.attrib["condition-coverage"]:
                file_data["partial_lines"].append(line_number)
        
        self.file_coverage[filename] = file_data
    
    def _analyze_file_coverage(self):
        """Analyze coverage for each file"""
        print("\n📁 File Coverage Analysis:")
        print("-" * 30)
        
        for filename, data in self.file_coverage.items():
            coverage_pct = data["line_rate"] * 100
            status = "✅" if coverage_pct >= 80 else "⚠️" if coverage_pct >= 60 else "❌"
            
            print(f"{status} {filename}: {coverage_pct:.1f}% ({data['lines_covered']}/{data['lines_valid']} lines)")
            
            if data["missing_lines"]:
                self.missing_lines[filename] = data["missing_lines"]
    
    def _identify_critical_gaps(self):
        """Identify critical coverage gaps"""
        print("\n🔍 Identifying Critical Gaps...")
        print("-" * 30)
        
        critical_files = [
            "app/api/api_v1/endpoints/auth.py",
            "app/api/api_v1/endpoints/documents.py",
            "app/api/api_v1/endpoints/chat.py",
            "app/services/auth.py",
            "app/services/document_service.py",
            "app/services/chat.py",
            "app/services/vector_service.py",
            "app/middleware/security.py",
            "app/utils/error_handling.py",
            "app/core/database.py"
        ]
        
        for filename in critical_files:
            if filename in self.file_coverage:
                data = self.file_coverage[filename]
                coverage_pct = data["line_rate"] * 100
                
                if coverage_pct < 80:
                    gap = {
                        "file": filename,
                        "coverage": coverage_pct,
                        "missing_lines": len(data["missing_lines"]),
                        "priority": "HIGH" if coverage_pct < 60 else "MEDIUM"
                    }
                    self.critical_gaps.append(gap)
                    print(f"❌ {filename}: {coverage_pct:.1f}% coverage (Priority: {gap['priority']})")
                else:
                    print(f"✅ {filename}: {coverage_pct:.1f}% coverage")
    
    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate recommendations for improving coverage"""
        recommendations = []
        
        # Sort critical gaps by priority and coverage
        sorted_gaps = sorted(self.critical_gaps, key=lambda x: (x["priority"], x["coverage"]))
        
        for gap in sorted_gaps:
            file_path = self.backend_dir / gap["file"]
            if file_path.exists():
                # Analyze the file to suggest specific improvements
                suggestions = self._analyze_file_for_suggestions(file_path, gap)
                recommendations.append({
                    "file": gap["file"],
                    "priority": gap["priority"],
                    "current_coverage": gap["coverage"],
                    "missing_lines": gap["missing_lines"],
                    "suggestions": suggestions
                })
        
        return recommendations
    
    def _analyze_file_for_suggestions(self, file_path: Path, gap: Dict[str, Any]) -> List[str]:
        """Analyze a file to suggest specific improvements"""
        suggestions = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Check for common patterns that need testing
            for i, line in enumerate(lines, 1):
                line = line.strip()
                
                # Error handling
                if "except" in line and "pass" in line:
                    suggestions.append(f"Line {i}: Add test for exception handling")
                
                # Edge cases
                if "if not" in line and "return" in line:
                    suggestions.append(f"Line {i}: Add test for edge case condition")
                
                # Database operations
                if "db." in line and ("add" in line or "delete" in line or "update" in line):
                    suggestions.append(f"Line {i}: Add test for database operation")
                
                # API endpoints
                if "@router." in line or "@app." in line:
                    suggestions.append(f"Line {i}: Add integration test for endpoint")
                
                # Security functions
                if "hash" in line.lower() or "verify" in line.lower() or "validate" in line.lower():
                    suggestions.append(f"Line {i}: Add security test for function")
        
        except Exception as e:
            suggestions.append(f"Could not analyze file: {e}")
        
        return suggestions[:5]  # Limit to 5 suggestions per file
    
    def _calculate_overall_coverage(self) -> Dict[str, float]:
        """Calculate overall coverage statistics"""
        if not self.coverage_data:
            return {"line_coverage": 0.0, "branch_coverage": 0.0}
        
        return {
            "line_coverage": self.coverage_data["line_rate"] * 100,
            "branch_coverage": self.coverage_data["branch_rate"] * 100,
            "lines_covered": self.coverage_data["lines_covered"],
            "lines_total": self.coverage_data["lines_valid"],
            "branches_covered": self.coverage_data["branches_covered"],
            "branches_total": self.coverage_data["branches_valid"]
        }
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate coverage summary"""
        total_files = len(self.file_coverage)
        files_above_80 = sum(1 for data in self.file_coverage.values() if data["line_rate"] * 100 >= 80)
        files_above_60 = sum(1 for data in self.file_coverage.values() if data["line_rate"] * 100 >= 60)
        
        return {
            "total_files": total_files,
            "files_above_80_percent": files_above_80,
            "files_above_60_percent": files_above_60,
            "files_below_60_percent": total_files - files_above_60,
            "critical_gaps_count": len(self.critical_gaps),
            "high_priority_gaps": len([g for g in self.critical_gaps if g["priority"] == "HIGH"]),
            "medium_priority_gaps": len([g for g in self.critical_gaps if g["priority"] == "MEDIUM"])
        }
    
    def print_report(self, report: Dict[str, Any]):
        """Print coverage report"""
        print("\n" + "=" * 60)
        print("📊 TEST COVERAGE ANALYSIS REPORT")
        print("=" * 60)
        
        # Overall coverage
        overall = report["overall_coverage"]
        print(f"\n📈 Overall Coverage:")
        print(f"  Line Coverage: {overall['line_coverage']:.1f}% ({overall['lines_covered']}/{overall['lines_total']} lines)")
        print(f"  Branch Coverage: {overall['branch_coverage']:.1f}% ({overall['branches_covered']}/{overall['branches_total']} branches)")
        
        # Summary
        summary = report["summary"]
        print(f"\n📋 Summary:")
        print(f"  Total Files: {summary['total_files']}")
        print(f"  Files ≥80% Coverage: {summary['files_above_80_percent']}")
        print(f"  Files ≥60% Coverage: {summary['files_above_60_percent']}")
        print(f"  Files <60% Coverage: {summary['files_below_60_percent']}")
        print(f"  Critical Gaps: {summary['critical_gaps_count']}")
        print(f"  High Priority Gaps: {summary['high_priority_gaps']}")
        print(f"  Medium Priority Gaps: {summary['medium_priority_gaps']}")
        
        # Critical gaps
        if report["critical_gaps"]:
            print(f"\n❌ Critical Coverage Gaps:")
            for gap in report["critical_gaps"]:
                print(f"  {gap['priority']} - {gap['file']}: {gap['coverage']:.1f}% ({gap['missing_lines']} missing lines)")
        
        # Recommendations
        if report["recommendations"]:
            print(f"\n💡 Recommendations:")
            for rec in report["recommendations"][:5]:  # Show top 5
                print(f"  {rec['priority']} - {rec['file']}:")
                for suggestion in rec["suggestions"][:3]:  # Show top 3 suggestions
                    print(f"    • {suggestion}")
        
        # Coverage status
        if overall["line_coverage"] >= 80:
            print(f"\n🎉 EXCELLENT COVERAGE! ({overall['line_coverage']:.1f}%)")
        elif overall["line_coverage"] >= 60:
            print(f"\n⚠️  GOOD COVERAGE, but needs improvement ({overall['line_coverage']:.1f}%)")
        else:
            print(f"\n❌ POOR COVERAGE - immediate action required ({overall['line_coverage']:.1f}%)")
        
        print("=" * 60)
    
    def save_report(self, report: Dict[str, Any], output_file: str = "coverage_analysis.json"):
        """Save coverage analysis report"""
        output_path = self.backend_dir / output_file
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Coverage analysis saved to: {output_path}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Analyze test coverage for CustomerCareGPT")
    parser.add_argument("--coverage-file", default="coverage.xml", help="Coverage XML file path")
    parser.add_argument("--output", "-o", default="coverage_analysis.json", help="Output file for analysis")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Get backend directory
    backend_dir = Path(__file__).parent.parent
    
    # Create coverage analyzer
    analyzer = CoverageAnalyzer(backend_dir)
    
    # Set custom coverage file if specified
    if args.coverage_file != "coverage.xml":
        analyzer.coverage_file = Path(args.coverage_file)
    
    # Analyze coverage
    report = analyzer.analyze_coverage()
    
    # Print report
    analyzer.print_report(report)
    
    # Save report
    analyzer.save_report(report, args.output)


if __name__ == "__main__":
    main()
