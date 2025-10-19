# Changelog

All notable changes to Slop Detector will be documented in this file.

## [0.1.0] - 2025-10-19

### Added

#### Core Features
- **Codebase Visualization**: Interactive HTML graphs showing dependency relationships
  - File-level dependency graphs
  - Entity-level (function/class) dependency graphs
  - Directory-based clustering
  - Multiple layout algorithms (force-directed, breadth-first, circle, grid, concentric)
  
- **Language Support**
  - Python (.py) with AST-based parsing
  - JavaScript (.js, .jsx) with esprima parsing
  - TypeScript (.ts, .tsx) with esprima parsing

#### Slop Detection

- **Comment Detectors**
  - Placeholder comments (TODO, FIXME, HACK, XXX)
  - Obsolete code markers (legacy, deprecated, backwards compatibility)
  - Commented-out code detection
  - Obvious comments that restate code
  - Generic AI-generated docstrings

- **Code Quality Detectors**
  - Unused functions and classes
  - Stranded files (never imported)
  - Unused imports
  - Long functions (configurable threshold, default: 50 lines)
  - Deep nesting (configurable threshold, default: 4 levels)
  - Empty exception handlers
  - Bare except clauses
  - Generic exception catching

- **Architecture Detectors**
  - Circular dependencies between files/modules
  - Duplicate code blocks (configurable threshold, default: 5 lines)

#### Visualization Features
- Interactive Cytoscape.js-based graph
- Color-coded nodes by quality:
  - Green: Clean code
  - Yellow: Info-level issues
  - Orange: Warnings
  - Red: Errors/critical issues
- Circular dependency highlighting (red dashed edges)
- Click nodes for detailed information
- Search functionality
- Zoom, pan, and fit-to-screen controls
- Detailed node information panel

#### Reporting
- **Terminal Reporter**
  - Colorized output
  - Summary statistics
  - Top issues by severity
  - Auto-switches to markdown for large reports
  
- **Markdown Reporter**
  - Executive summary
  - Issue categorization
  - File rankings by issue count
  - Code snippets with context
  - Actionable recommendations
  - Links to interactive visualization

#### Configuration
- JSON-based configuration files (.sloprc.json)
- Customizable thresholds
- Detector enable/disable flags
- Custom ignore patterns
- Entry point definitions
- CLI argument overrides

#### File Scanning
- Respects .gitignore patterns
- Configurable additional ignore patterns
- Automatic exclusion of common directories:
  - node_modules/, venv/, __pycache__/
  - dist/, build/, .git/
  - .next/, .nuxt/, coverage/

#### CLI Interface
- `slop-detector analyze` command
- Multiple output formats (terminal, markdown, auto)
- Configurable output directory
- Mode selection (file vs entity graphs)
- Threshold customization
- Config file support

### Technical Implementation
- Built with NetworkX for graph analysis
- AST-based Python parsing
- Esprima for JavaScript/TypeScript parsing
- Jinja2 for HTML template rendering
- Click for CLI framework
- Colorama for terminal colors
- Pathspec for .gitignore pattern matching

### Testing
- Test fixtures with intentional code issues
- Sample files demonstrating all detector capabilities
- Circular dependency examples
- Stranded file examples

### Documentation
- Comprehensive README
- Detailed USAGE guide
- Example configuration file
- MIT License

