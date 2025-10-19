"""Terminal reporter for outputting results to console."""

from typing import List, Dict
from collections import defaultdict
from colorama import init, Fore, Style
from ..detectors.base import Issue, IssueSeverity

# Initialize colorama
init(autoreset=True)


class TerminalReporter:
    """Reports analysis results to terminal."""
    
    def __init__(self):
        self.colors = {
            IssueSeverity.CRITICAL: Fore.RED + Style.BRIGHT,
            IssueSeverity.ERROR: Fore.RED,
            IssueSeverity.WARNING: Fore.YELLOW,
            IssueSeverity.INFO: Fore.CYAN,
        }
        self.icons = {
            IssueSeverity.CRITICAL: '🔴',
            IssueSeverity.ERROR: '🔴',
            IssueSeverity.WARNING: '⚠️ ',
            IssueSeverity.INFO: '📝',
        }
    
    def report(self, issues: List[Issue], stats: Dict, viz_path: str = None) -> int:
        """Generate terminal report.
        
        Args:
            issues: List of detected issues
            stats: Dictionary of statistics
            viz_path: Path to visualization file
            
        Returns:
            Number of lines in output
        """
        lines = []
        
        # Header
        lines.append(f"\n{Fore.CYAN}{Style.BRIGHT}{'━' * 50}")
        lines.append(f"🔍 Slop Detector Analysis")
        lines.append(f"{'━' * 50}{Style.RESET_ALL}\n")
        
        # Summary statistics
        lines.append(f"{Style.BRIGHT}📊 Summary:{Style.RESET_ALL}")
        lines.append(f"  Files analyzed: {Fore.CYAN}{stats.get('files_analyzed', 0)}{Style.RESET_ALL}")
        lines.append(f"  Functions/Classes: {Fore.CYAN}{stats.get('entities_found', 0)}{Style.RESET_ALL}")
        lines.append(f"  Issues found: {Fore.YELLOW}{len(issues)}{Style.RESET_ALL}\n")
        
        if not issues:
            lines.append(f"{Fore.GREEN}✓ No issues found! Clean codebase.{Style.RESET_ALL}\n")
            
            if viz_path:
                lines.append(f"📊 Visualization: {Fore.BLUE}{viz_path}{Style.RESET_ALL}\n")
            
            for line in lines:
                print(line)
            return len(lines)
        
        # Group issues by severity and category
        by_severity = defaultdict(list)
        by_category = defaultdict(int)
        
        for issue in issues:
            by_severity[issue.severity].append(issue)
            by_category[issue.category] += 1
        
        # Critical issues summary
        lines.append(f"{Style.BRIGHT}⚠️  Critical Issues:{Style.RESET_ALL}")
        
        critical_count = len(by_severity.get(IssueSeverity.CRITICAL, []))
        error_count = len(by_severity.get(IssueSeverity.ERROR, []))
        warning_count = len(by_severity.get(IssueSeverity.WARNING, []))
        info_count = len(by_severity.get(IssueSeverity.INFO, []))
        
        if critical_count:
            lines.append(f"  {self.icons[IssueSeverity.CRITICAL]} {critical_count} critical issues")
        if error_count:
            lines.append(f"  {self.icons[IssueSeverity.ERROR]} {error_count} errors")
        if warning_count:
            lines.append(f"  {self.icons[IssueSeverity.WARNING]} {warning_count} warnings")
        if info_count:
            lines.append(f"  {self.icons[IssueSeverity.INFO]} {info_count} info")
        
        lines.append("")
        
        # Top issues by category
        lines.append(f"{Style.BRIGHT}📋 Issues by Category:{Style.RESET_ALL}")
        sorted_categories = sorted(by_category.items(), key=lambda x: x[1], reverse=True)
        for category, count in sorted_categories[:10]:
            lines.append(f"  • {category}: {Fore.YELLOW}{count}{Style.RESET_ALL}")
        
        lines.append("")
        
        # Detailed issues (top 20)
        lines.append(f"{Style.BRIGHT}🔍 Detailed Findings (top 20):{Style.RESET_ALL}\n")
        
        # Sort by severity
        sorted_issues = sorted(
            issues,
            key=lambda x: (
                ['info', 'warning', 'error', 'critical'].index(x.severity.value),
                x.file_path,
                x.line
            ),
            reverse=True
        )
        
        for issue in sorted_issues[:20]:
            color = self.colors.get(issue.severity, '')
            icon = self.icons.get(issue.severity, '')
            
            location = f"{issue.file_path}"
            if issue.line:
                location += f":{issue.line}"
            
            lines.append(f"{color}{icon} [{issue.severity.value.upper()}] {issue.category}{Style.RESET_ALL}")
            lines.append(f"   {issue.message}")
            lines.append(f"   {Fore.BLUE}{location}{Style.RESET_ALL}")
            
            if issue.suggestion:
                lines.append(f"   💡 {Fore.GREEN}{issue.suggestion}{Style.RESET_ALL}")
            
            lines.append("")
        
        if len(issues) > 20:
            lines.append(f"{Fore.YELLOW}... and {len(issues) - 20} more issues{Style.RESET_ALL}")
            lines.append(f"{Fore.YELLOW}Run with markdown output for full report{Style.RESET_ALL}\n")
        
        # Circular dependencies
        if stats.get('circular_dependencies'):
            lines.append(f"{Style.BRIGHT}🔄 Circular Dependencies:{Style.RESET_ALL}")
            for cycle in stats['circular_dependencies'][:5]:
                cycle_str = ' → '.join(cycle) + ' → ' + cycle[0]
                lines.append(f"  {Fore.RED}{cycle_str}{Style.RESET_ALL}")
            lines.append("")
        
        # Stranded files
        if stats.get('stranded_files'):
            lines.append(f"{Style.BRIGHT}📂 Stranded Files:{Style.RESET_ALL}")
            for file in stats['stranded_files'][:10]:
                lines.append(f"  {Fore.RED}• {file}{Style.RESET_ALL}")
            if len(stats['stranded_files']) > 10:
                lines.append(f"  ... and {len(stats['stranded_files']) - 10} more")
            lines.append("")
        
        # Visualization link
        if viz_path:
            lines.append(f"📊 Visualization: {Fore.BLUE}{viz_path}{Style.RESET_ALL}\n")
        
        # Print all lines
        for line in lines:
            print(line)
        
        return len(lines)

