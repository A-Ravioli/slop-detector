# Slop Detector

A powerful codebase visualizer and code quality analyzer that detects "slop" - low-quality code patterns, unused code, and technical debt.

## Features

### Dependency Visualization
- **Interactive HTML graphs** showing file and entity-level dependencies
- **Two visualization modes**:
  - **File-level**: Shows files as nodes with imports as edges
  - **Entity-level**: Shows functions/classes as nodes with calls/usage as edges
- **Clustered by directory structure** for better organization
- **Color-coded nodes** based on code quality (green = clean, red = issues)
- **Circular dependency highlighting**

### Code Quality Detection

Detects multiple types of "slop":

#### Comment Issues
- Placeholder comments (TODO, FIXME, HACK)
- Obsolete code markers (legacy, deprecated, backwards compatibility)
- Commented-out code
- Obvious comments that just restate code
- Generic AI-generated docstrings with no added value

#### Unused Code
- Stranded files that are never imported
- Unused functions and classes
- Unused imports

#### Complexity Issues
- Functions that are too long (default: >50 lines)
- Deep nesting (default: >4 levels)
- Empty exception handlers
- Bare except clauses
- Generic exception catching

#### Code Duplication
- Duplicate code blocks (default: ≥5 lines)
- Suggests extracting to shared functions

#### Dependency Issues
- Circular dependencies between files/modules
- Files with no incoming edges (except entry points)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/slop-detector.git
cd slop-detector

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

## Usage

### Basic Analysis

```bash
# Analyze current directory
slop-detector analyze

# Analyze specific directory
slop-detector analyze /path/to/codebase

# Analyze with entity-level graph
slop-detector analyze --mode entity

# Skip visualization generation
slop-detector analyze --no-viz
```

### Advanced Options

```bash
slop-detector analyze [DIRECTORY] [OPTIONS]

Options:
  --mode [file|entity]          Graph mode (default: file)
  --output-dir PATH             Output directory (default: ./slop-report)
  --threshold-lines INT         Long function threshold (default: 50)
  --threshold-nesting INT       Deep nesting threshold (default: 4)
  --ignore-patterns TEXT        Additional ignore patterns (can be used multiple times)
  --config FILE                 Path to configuration file
  --no-viz                      Skip visualization generation
  --format [terminal|markdown|auto]  Report format (default: auto)
```

### Configuration File

Create a `.sloprc.json` file in your project root:

```json
{
  "thresholds": {
    "max_function_lines": 50,
    "max_nesting_depth": 4,
    "min_duplicate_lines": 5,
    "terminal_output_lines": 100
  },
  "ignore_patterns": ["*.test.js", "*_pb2.py"],
  "detectors": {
    "comments": true,
    "unused_code": true,
    "duplicates": true,
    "complexity": true,
    "imports": true
  },
  "entry_points": ["main.py", "index.js", "app.py", "__init__.py"]
}
```

## Output

### Terminal Output

For small codebases or when using `--format terminal`:

```
🔍 Slop Detector Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Summary:
  Files analyzed: 45
  Functions/Classes: 234
  Issues found: 18

⚠️  Critical Issues:
  🔴 3 stranded files
  🔴 2 circular dependencies
  ⚠️  5 unused functions
  📝 8 slop comments

📂 Stranded Files:
  - src/old_utils.py (never imported)
  - lib/legacy_helper.js (never imported)

🔄 Circular Dependencies:
  - auth.py → database.py → models.py → auth.py

📊 Visualization: file:///path/to/slop-report/graph.html
```

### Markdown Report

For large codebases, automatically generates a comprehensive markdown report with:
- Executive summary with statistics
- Circular dependency list
- Stranded files
- Issues grouped by category and severity
- Files ranked by issue count
- Actionable recommendations
- Link to interactive visualization

### Interactive Visualization

An HTML file with an interactive graph featuring:
- **Pan and zoom** - Navigate large codebases
- **Multiple layout algorithms** - Choose the best view
- **Node search** - Find specific files/functions
- **Click for details** - See file info and issues
- **Color coding** - Visual quality indicators
- **Legend** - Understand the visualization
- **Circular dependency highlighting** - Red dashed edges

## Supported Languages

- Python (`.py`)
- JavaScript (`.js`, `.jsx`)
- TypeScript (`.ts`, `.tsx`)

## Examples

### Analyze a Python project
```bash
slop-detector analyze ./my-python-project
```

### Analyze with custom thresholds
```bash
slop-detector analyze ./my-app --threshold-lines 100 --threshold-nesting 5
```

### Generate only markdown report (skip terminal output)
```bash
slop-detector analyze ./codebase --format markdown
```

### Entity-level analysis for detailed function call graphs
```bash
slop-detector analyze ./src --mode entity
```

## What Makes Code "Slop"?

Slop Detector looks for patterns commonly found in AI-generated or low-quality code:

1. **Incomplete implementations** - TODOs, FIXMEs, placeholder comments
2. **Dead code** - Unused functions, stranded files, commented code
3. **Poor documentation** - Generic docstrings that add no value
4. **Technical debt markers** - "legacy", "deprecated", "backwards compatibility"
5. **Code smells** - Long functions, deep nesting, duplicate code
6. **Poor error handling** - Empty catch blocks, bare exceptions
7. **Circular dependencies** - Indicates poor architecture
8. **Unused imports** - Clutters code and slows down analysis

## Development

### Running Tests

```bash
pytest tests/
```

### Project Structure

```
slop-detector/
├── slop_detector/
│   ├── cli.py                  # CLI entry point
│   ├── parsers/                # Language parsers
│   │   ├── python_parser.py
│   │   └── javascript_parser.py
│   ├── graph/                  # Graph construction
│   │   ├── builder.py
│   │   └── analyzer.py
│   ├── detectors/              # Slop detectors
│   │   ├── comments.py
│   │   ├── unused_code.py
│   │   ├── complexity.py
│   │   ├── duplicates.py
│   │   └── imports.py
│   ├── visualizer/             # Graph rendering
│   │   └── graph_renderer.py
│   ├── reporters/              # Report generation
│   │   ├── terminal.py
│   │   └── markdown.py
│   └── utils/                  # Utilities
│       ├── file_scanner.py
│       └── config.py
└── tests/
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Built with NetworkX for graph analysis
- Cytoscape.js for interactive visualizations
- esprima for JavaScript/TypeScript parsing
- Python's AST module for Python parsing
