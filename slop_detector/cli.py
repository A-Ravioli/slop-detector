"""Command-line interface for slop detector."""

import os
import sys
from pathlib import Path
from typing import List, Dict
import click
from .utils.file_scanner import FileScanner
from .utils.config import Config
from .parsers.python_parser import PythonParser
from .parsers.javascript_parser import JavaScriptParser
from .parsers.base import ParsedFile
from .graph.builder import GraphBuilder
from .graph.analyzer import GraphAnalyzer
from .detectors.comments import CommentDetector
from .detectors.unused_code import UnusedCodeDetector
from .detectors.imports import ImportDetector
from .detectors.complexity import ComplexityDetector
from .detectors.duplicates import DuplicateDetector
from .detectors.base import Issue
from .visualizer.graph_renderer import GraphRenderer
from .reporters.terminal import TerminalReporter
from .reporters.markdown import MarkdownReporter


@click.group()
def main():
    """Slop Detector - Codebase visualizer and quality analyzer."""
    pass


@main.command()
@click.argument('directory', type=click.Path(exists=True), default='.')
@click.option('--mode', type=click.Choice(['file', 'entity']), default='file',
              help='Graph mode: file-level or entity-level')
@click.option('--output-dir', type=click.Path(), default='./slop-report',
              help='Output directory for reports')
@click.option('--threshold-lines', type=int, default=50,
              help='Maximum function lines threshold')
@click.option('--threshold-nesting', type=int, default=4,
              help='Maximum nesting depth threshold')
@click.option('--ignore-patterns', multiple=True,
              help='Additional ignore patterns')
@click.option('--config', type=click.Path(exists=True),
              help='Path to configuration file')
@click.option('--no-viz', is_flag=True,
              help='Skip visualization generation')
@click.option('--format', type=click.Choice(['terminal', 'markdown', 'auto']), default='auto',
              help='Report format')
def analyze(directory, mode, output_dir, threshold_lines, threshold_nesting, 
           ignore_patterns, config, no_viz, format):
    """Analyze a codebase for dependencies and code quality issues."""
    
    click.echo(f"🔍 Analyzing codebase in: {directory}\n")
    
    # Load configuration
    config_overrides = {
        'thresholds': {
            'max_function_lines': threshold_lines,
            'max_nesting_depth': threshold_nesting,
        }
    }
    if ignore_patterns:
        config_overrides['ignore_patterns'] = list(ignore_patterns)
    
    cfg = Config(config_path=config, overrides=config_overrides)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Scan files
    click.echo("📂 Scanning files...")
    scanner = FileScanner(directory, additional_ignore=cfg.get('ignore_patterns', []))
    files = scanner.scan()
    
    if not files:
        click.echo("❌ No source files found!")
        sys.exit(1)
    
    click.echo(f"   Found {len(files)} source files\n")
    
    # Step 2: Parse files
    click.echo("🔬 Parsing files...")
    python_parser = PythonParser()
    js_parser = JavaScriptParser()
    
    parsed_files: List[ParsedFile] = []
    entity_count = 0
    
    for file_info in files:
        try:
            if file_info.language == 'python':
                parsed = python_parser.parse_file(file_info.path)
            else:
                parsed = js_parser.parse_file(file_info.path)
            
            parsed_files.append(parsed)
            entity_count += len(parsed.definitions)
        except Exception as e:
            click.echo(f"   Warning: Failed to parse {file_info.path}: {e}")
    
    click.echo(f"   Parsed {len(parsed_files)} files, found {entity_count} entities\n")
    
    # Step 3: Build graphs
    click.echo("🕸️  Building dependency graph...")
    graph_builder = GraphBuilder(directory)
    
    if mode == 'file':
        graph = graph_builder.build_file_graph(parsed_files)
        click.echo(f"   File graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    else:
        graph = graph_builder.build_entity_graph(parsed_files)
        click.echo(f"   Entity graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    
    # Step 4: Analyze graph
    analyzer = GraphAnalyzer(graph)
    circular_deps = analyzer.find_circular_dependencies()
    stranded = analyzer.find_stranded_nodes(entry_points=cfg.get('entry_points', []))
    
    # Mark cycles in graph
    analyzer.mark_cycles()
    
    if circular_deps:
        click.echo(f"   Found {len(circular_deps)} circular dependencies")
    if stranded:
        click.echo(f"   Found {len(stranded)} stranded nodes")
    
    click.echo("")
    
    # Step 5: Run detectors
    click.echo("🔍 Running slop detectors...")
    all_issues: List[Issue] = []
    
    if cfg.is_detector_enabled('comments'):
        click.echo("   • Comment detector")
        detector = CommentDetector(cfg)
        all_issues.extend(detector.detect(parsed_files))
    
    if cfg.is_detector_enabled('unused_code'):
        click.echo("   • Unused code detector")
        detector = UnusedCodeDetector(cfg)
        file_graph = graph if mode == 'file' else graph_builder.build_file_graph(parsed_files)
        all_issues.extend(detector.detect(parsed_files, file_graph=file_graph))
    
    if cfg.is_detector_enabled('imports'):
        click.echo("   • Import detector")
        detector = ImportDetector(cfg)
        all_issues.extend(detector.detect(parsed_files))
    
    if cfg.is_detector_enabled('complexity'):
        click.echo("   • Complexity detector")
        detector = ComplexityDetector(cfg)
        all_issues.extend(detector.detect(parsed_files))
    
    if cfg.is_detector_enabled('duplicates'):
        click.echo("   • Duplicate code detector")
        detector = DuplicateDetector(cfg)
        all_issues.extend(detector.detect(parsed_files))
    
    click.echo(f"   Found {len(all_issues)} issues\n")
    
    # Step 6: Generate visualization
    viz_path = None
    if not no_viz:
        click.echo("📊 Generating visualization...")
        
        # Group issues by file
        issues_by_file = {}
        for issue in all_issues:
            if issue.file_path not in issues_by_file:
                issues_by_file[issue.file_path] = []
            issues_by_file[issue.file_path].append(issue)
        
        renderer = GraphRenderer()
        viz_file = output_path / 'graph.html'
        viz_path = renderer.render(
            graph,
            str(viz_file),
            title=f"Dependency Graph - {Path(directory).name}",
            issues_by_file=issues_by_file
        )
        click.echo(f"   Saved to: {viz_path}\n")
    
    # Step 7: Generate report
    stats = {
        'files_analyzed': len(parsed_files),
        'entities_found': entity_count,
        'circular_dependencies': circular_deps,
        'stranded_files': stranded,
    }
    
    terminal_reporter = TerminalReporter()
    
    # Determine output format
    if format == 'auto':
        # Count terminal output lines
        line_count = len(all_issues) * 6  # Rough estimate
        threshold = cfg.get_threshold('terminal_output_lines')
        
        if line_count > threshold:
            format = 'markdown'
        else:
            format = 'terminal'
    
    if format == 'markdown':
        click.echo("📝 Generating markdown report...")
        markdown_reporter = MarkdownReporter()
        report_file = output_path / 'report.md'
        report_path = markdown_reporter.report(all_issues, stats, str(report_file), viz_path)
        click.echo(f"   Saved to: {report_path}\n")
        
        # Also print summary to terminal
        click.echo("📊 Summary:")
        terminal_reporter.report(all_issues[:20], stats, viz_path)
        click.echo(f"\n💡 Full report available at: {report_path}")
    else:
        terminal_reporter.report(all_issues, stats, viz_path)
    
    # Exit with error code if critical issues found
    critical_count = sum(1 for i in all_issues if i.severity.value in ('critical', 'error'))
    if critical_count > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()

