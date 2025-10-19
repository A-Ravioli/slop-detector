"""Markdown reporter for generating detailed reports."""

from typing import List, Dict
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter
from ..detectors.base import Issue, IssueSeverity


class MarkdownReporter:
    """Generates detailed markdown reports."""
    
    def __init__(self):
        self.severity_order = {
            IssueSeverity.CRITICAL: 0,
            IssueSeverity.ERROR: 1,
            IssueSeverity.WARNING: 2,
            IssueSeverity.INFO: 3,
        }
    
    def report(self, issues: List[Issue], stats: Dict, output_path: str, viz_path: str = None) -> str:
        """Generate markdown report.
        
        Args:
            issues: List of detected issues
            stats: Dictionary of statistics
            output_path: Path to output markdown file
            viz_path: Path to visualization file
            
        Returns:
            Path to generated markdown file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        lines = []
        
        # Header
        lines.append("# Slop Detector Analysis Report\n")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append("---\n")
        
        # Executive Summary
        lines.append("## Executive Summary\n")
        lines.append(f"- **Files Analyzed:** {stats.get('files_analyzed', 0)}")
        lines.append(f"- **Functions/Classes Found:** {stats.get('entities_found', 0)}")
        lines.append(f"- **Total Issues:** {len(issues)}")
        
        if issues:
            by_severity = defaultdict(int)
            for issue in issues:
                by_severity[issue.severity] += 1
            
            lines.append(f"  - Critical: {by_severity.get(IssueSeverity.CRITICAL, 0)}")
            lines.append(f"  - Errors: {by_severity.get(IssueSeverity.ERROR, 0)}")
            lines.append(f"  - Warnings: {by_severity.get(IssueSeverity.WARNING, 0)}")
            lines.append(f"  - Info: {by_severity.get(IssueSeverity.INFO, 0)}")
        
        lines.append("")
        
        # Visualization link
        if viz_path:
            lines.append(f"**[View Interactive Visualization]({viz_path})**\n")
        
        lines.append("---\n")
        
        # Critical Issues
        if stats.get('circular_dependencies'):
            lines.append("## Circular Dependencies\n")
            lines.append("The following circular dependencies were detected:\n")
            for i, cycle in enumerate(stats['circular_dependencies'], 1):
                cycle_str = ' → '.join(cycle) + ' → ' + cycle[0]
                lines.append(f"{i}. `{cycle_str}`")
            lines.append("")
        
        # Stranded Files
        if stats.get('stranded_files'):
            lines.append("## Stranded Files\n")
            lines.append("These files are never imported and may be dead code:\n")
            for file in stats['stranded_files']:
                lines.append(f"- `{file}`")
            lines.append("")
        
        # Issues by Category
        if issues:
            lines.append("## Issues by Category\n")
            
            by_category = defaultdict(list)
            for issue in issues:
                by_category[issue.category].append(issue)
            
            # Sort categories by count
            sorted_categories = sorted(by_category.items(), key=lambda x: len(x[1]), reverse=True)
            
            for category, category_issues in sorted_categories:
                lines.append(f"### {category} ({len(category_issues)} issues)\n")
                
                # Group by severity
                by_severity = defaultdict(list)
                for issue in category_issues:
                    by_severity[issue.severity].append(issue)
                
                # Sort by severity
                for severity in sorted(by_severity.keys(), key=lambda s: self.severity_order[s]):
                    severity_issues = by_severity[severity]
                    
                    for issue in severity_issues[:10]:  # Limit per category
                        lines.append(f"#### {self._get_severity_emoji(issue.severity)} {issue.message}\n")
                        lines.append(f"**File:** `{issue.file_path}`")
                        if issue.line:
                            lines.append(f" (Line {issue.line})")
                        lines.append("\n")
                        
                        if issue.suggestion:
                            lines.append(f"**Suggestion:** {issue.suggestion}\n")
                        
                        if issue.code_snippet:
                            lines.append("**Code:**")
                            lines.append("```")
                            lines.append(issue.code_snippet)
                            lines.append("```\n")
                
                if len(category_issues) > 10:
                    lines.append(f"*... and {len(category_issues) - 10} more issues in this category*\n")
        
        # Files with Most Issues
        if issues:
            lines.append("## Files with Most Issues\n")
            
            by_file = defaultdict(list)
            for issue in issues:
                by_file[issue.file_path].append(issue)
            
            sorted_files = sorted(by_file.items(), key=lambda x: len(x[1]), reverse=True)
            
            lines.append("| File | Issues | Critical | Errors | Warnings |")
            lines.append("|------|--------|----------|--------|----------|")
            
            for file_path, file_issues in sorted_files[:20]:
                critical = sum(1 for i in file_issues if i.severity == IssueSeverity.CRITICAL)
                errors = sum(1 for i in file_issues if i.severity == IssueSeverity.ERROR)
                warnings = sum(1 for i in file_issues if i.severity == IssueSeverity.WARNING)
                
                file_display = file_path
                if len(file_display) > 50:
                    file_display = "..." + file_display[-47:]
                
                lines.append(f"| `{file_display}` | {len(file_issues)} | {critical} | {errors} | {warnings} |")
            
            lines.append("")
        
        # Recommendations
        lines.append("## Recommendations\n")
        lines.append(self._generate_recommendations(issues, stats))
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        return str(output_path)
    
    def _get_severity_emoji(self, severity: IssueSeverity) -> str:
        """Get emoji for severity."""
        emojis = {
            IssueSeverity.CRITICAL: '🔴',
            IssueSeverity.ERROR: '❌',
            IssueSeverity.WARNING: '⚠️',
            IssueSeverity.INFO: 'ℹ️',
        }
        return emojis.get(severity, '•')
    
    def _generate_recommendations(self, issues: List[Issue], stats: Dict) -> str:
        """Generate recommendations based on findings."""
        recommendations = []
        
        # Count issue types
        by_category = defaultdict(int)
        for issue in issues:
            by_category[issue.category] += 1
        
        if by_category.get('Unused Code', 0) > 0:
            recommendations.append(
                "1. **Remove Dead Code**: Found unused functions and classes. "
                "Consider removing them to reduce codebase complexity."
            )
        
        if by_category.get('Stranded File', 0) > 0:
            recommendations.append(
                "2. **Clean Up Stranded Files**: Several files are never imported. "
                "Remove them or add proper entry points if they're meant to be used."
            )
        
        if stats.get('circular_dependencies'):
            recommendations.append(
                "3. **Resolve Circular Dependencies**: Circular dependencies make code harder to "
                "understand and maintain. Refactor to break these cycles."
            )
        
        if by_category.get('Duplicate Code', 0) > 0:
            recommendations.append(
                "4. **Extract Common Functions**: Found duplicate code blocks. "
                "Extract these into shared utility functions."
            )
        
        if by_category.get('Long Function', 0) > 0:
            recommendations.append(
                "5. **Break Down Large Functions**: Some functions are too long. "
                "Break them into smaller, more focused functions."
            )
        
        if by_category.get('Deep Nesting', 0) > 0:
            recommendations.append(
                "6. **Reduce Nesting Depth**: Deep nesting makes code hard to read. "
                "Use early returns or extract functions to reduce complexity."
            )
        
        if by_category.get('Placeholder Comment', 0) > 0 or by_category.get('Obsolete Code', 0) > 0:
            recommendations.append(
                "7. **Address TODOs and Legacy Code**: Complete pending implementations "
                "and remove or update deprecated code."
            )
        
        if by_category.get('Empty Exception Handler', 0) > 0:
            recommendations.append(
                "8. **Improve Error Handling**: Empty exception handlers hide errors. "
                "Add proper error handling or at least logging."
            )
        
        if not recommendations:
            recommendations.append("No major issues found. Keep up the good work!")
        
        return '\n\n'.join(recommendations) + "\n"

