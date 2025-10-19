# Slop Detector Usage Guide

## Quick Start

```bash
# Install the tool
pip install -e .

# Analyze current directory
slop-detector analyze

# Analyze specific directory
slop-detector analyze /path/to/project
```

## Basic Analysis

### File-Level Dependency Graph (Default)

Shows files as nodes and imports as edges:

```bash
slop-detector analyze ./my-project
```

This will:
- Scan all Python, JavaScript, and TypeScript files
- Create a file dependency graph
- Detect code quality issues
- Generate an interactive HTML visualization
- Output results to terminal (or markdown for large reports)

### Entity-Level Dependency Graph

Shows functions/classes as nodes and calls as edges:

```bash
slop-detector analyze ./my-project --mode entity
```

This gives you a more granular view of your codebase, showing which functions call which other functions.

## Customization

### Setting Thresholds

```bash
# Allow longer functions (default is 50 lines)
slop-detector analyze . --threshold-lines 100

# Allow deeper nesting (default is 4 levels)
slop-detector analyze . --threshold-nesting 6
```

### Ignoring Files

```bash
# Ignore specific patterns
slop-detector analyze . --ignore-patterns "*.test.js" --ignore-patterns "*_pb2.py"
```

### Using a Configuration File

Create `.sloprc.json` in your project root:

```json
{
  "thresholds": {
    "max_function_lines": 75,
    "max_nesting_depth": 5,
    "min_duplicate_lines": 8,
    "terminal_output_lines": 150
  },
  "ignore_patterns": [
    "*.test.js",
    "*_test.py",
    "test_*.py",
    "*_pb2.py"
  ],
  "detectors": {
    "comments": true,
    "unused_code": true,
    "duplicates": true,
    "complexity": true,
    "imports": true
  },
  "entry_points": [
    "main.py",
    "index.js",
    "app.py",
    "server.js",
    "cli.py"
  ]
}
```

Then run:

```bash
slop-detector analyze . --config .sloprc.json
```

### Output Options

```bash
# Skip visualization generation (faster)
slop-detector analyze . --no-viz

# Force markdown report
slop-detector analyze . --format markdown

# Force terminal output
slop-detector analyze . --format terminal

# Custom output directory
slop-detector analyze . --output-dir ./analysis-results
```

## Understanding the Output

### Terminal Output

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
```

### Issue Severities

- **🔴 ERROR/CRITICAL**: Serious issues that likely indicate dead code or architectural problems
  - Stranded files
  - Circular dependencies
  - Obsolete code markers
  - Empty exception handlers

- **⚠️  WARNING**: Issues that should be addressed but aren't critical
  - Placeholder comments (TODO, FIXME)
  - Deep nesting
  - Long functions
  - Commented-out code

- **📝 INFO**: Minor issues or style improvements
  - Generic docstrings
  - Obvious comments
  - Unused imports

### Issue Categories

1. **Placeholder Comment**: TODOs, FIXMEs, incomplete code markers
2. **Obsolete Code**: Legacy code, deprecated functions, backwards compatibility notes
3. **Commented Code**: Commented-out code blocks
4. **Obvious Comment**: Comments that just repeat what the code does
5. **Generic Docstring**: Documentation that adds no value beyond the function name
6. **Unused Code**: Functions/classes that are never called
7. **Stranded File**: Files that are never imported
8. **Unused Import**: Imported modules that aren't used
9. **Long Function**: Functions exceeding the line threshold
10. **Deep Nesting**: Functions with too many indentation levels
11. **Empty Exception Handler**: Catch blocks with no error handling
12. **Duplicate Code**: Code blocks that appear multiple times

## Interactive Visualization

The HTML visualization includes:

- **Pan and Zoom**: Navigate large codebases
- **Search**: Find specific files or functions
- **Node Details**: Click nodes to see file info and issues
- **Layout Options**: Choose different graph layouts
- **Color Coding**:
  - 🟢 Green: Clean code, no issues
  - 🟡 Yellow: Has info-level issues
  - 🟠 Orange: Has warnings
  - 🔴 Red: Has errors or critical issues
- **Edge Colors**:
  - Blue: Normal dependencies
  - Red dashed: Circular dependencies

## CI/CD Integration

Exit codes:
- `0`: Success, no critical issues
- `1`: Critical or error-level issues found

Example GitHub Actions:

```yaml
name: Code Quality Check

on: [push, pull_request]

jobs:
  slop-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install slop-detector
        run: pip install slop-detector
      - name: Run analysis
        run: slop-detector analyze . --format markdown
      - name: Upload report
        uses: actions/upload-artifact@v2
        if: always()
        with:
          name: slop-report
          path: slop-report/
```

## Example Workflows

### Cleaning Up a Legacy Codebase

1. Run initial analysis:
   ```bash
   slop-detector analyze . --output-dir initial-analysis
   ```

2. Review stranded files and remove dead code

3. Fix circular dependencies

4. Address placeholder comments (TODOs, FIXMEs)

5. Remove commented-out code

6. Refactor long functions and deep nesting

7. Run again to verify improvements:
   ```bash
   slop-detector analyze . --output-dir final-analysis
   ```

### Pre-Release Code Review

```bash
# Strict analysis for production code
slop-detector analyze src/ \
  --threshold-lines 40 \
  --threshold-nesting 3 \
  --format markdown \
  --output-dir pre-release-check
```

Review the markdown report for any issues before releasing.

### Monitoring Code Quality Over Time

Run periodically and compare reports:

```bash
# Weekly analysis
slop-detector analyze . --output-dir reports/$(date +%Y-%m-%d)
```

Track metrics:
- Total issues
- Stranded files count
- Circular dependencies
- Average function length
- Code duplication instances

## Tips

1. **Start with file-level analysis** to understand the overall architecture
2. **Use entity-level analysis** to understand function call patterns
3. **Fix stranded files first** - they're often completely dead code
4. **Break circular dependencies** - they indicate design issues
5. **Address placeholder comments** - complete the work or remove them
6. **Be cautious with unused code detection** - some code may be used via reflection or external tools
7. **Use configuration files** for consistent team-wide standards
8. **Review visualizations** - they often reveal architectural insights

## Troubleshooting

### Too Many False Positives

Adjust thresholds in configuration:
```json
{
  "thresholds": {
    "max_function_lines": 100,
    "max_nesting_depth": 6
  }
}
```

### Files Incorrectly Marked as Stranded

Add entry points to configuration:
```json
{
  "entry_points": ["main.py", "wsgi.py", "manage.py"]
}
```

### Parsing Errors

Some TypeScript features may not parse correctly. The tool will skip problematic files and continue analyzing the rest.

## Advanced Usage

### Analyzing Specific Directories

```bash
# Analyze only source code
slop-detector analyze src/

# Analyze multiple directories
slop-detector analyze src/ lib/ --output-dir combined-analysis
```

### Comparing Before/After

```bash
# Before refactoring
slop-detector analyze . --output-dir before/

# After refactoring  
slop-detector analyze . --output-dir after/

# Compare issue counts
```

### Custom Entry Points

For projects with non-standard entry points:

```bash
slop-detector analyze . \
  --config custom-config.json \
  --output-dir analysis
```

Where `custom-config.json` specifies your entry points.

