"""Configuration management for slop detector."""

import json
from pathlib import Path
from typing import Dict, Any, Optional


DEFAULT_CONFIG = {
    "thresholds": {
        "max_function_lines": 50,
        "max_nesting_depth": 4,
        "min_duplicate_lines": 5,
        "terminal_output_lines": 100,
    },
    "ignore_patterns": [],
    "detectors": {
        "comments": True,
        "unused_code": True,
        "duplicates": True,
        "complexity": True,
        "imports": True,
    },
    "entry_points": ["main.py", "index.js", "app.py", "server.js", "__init__.py"],
}


class Config:
    """Configuration manager."""
    
    def __init__(self, config_path: Optional[str] = None, overrides: Optional[Dict[str, Any]] = None):
        self.config = DEFAULT_CONFIG.copy()
        
        # Load from file if provided
        if config_path:
            self.load_from_file(config_path)
        
        # Apply overrides
        if overrides:
            self._deep_update(self.config, overrides)
    
    def load_from_file(self, config_path: str):
        """Load configuration from JSON file."""
        path = Path(config_path)
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                self._deep_update(self.config, user_config)
    
    def _deep_update(self, base: Dict, update: Dict):
        """Deep update dictionary."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_threshold(self, name: str) -> int:
        """Get threshold value."""
        return self.config["thresholds"].get(name, 0)
    
    def is_detector_enabled(self, name: str) -> bool:
        """Check if detector is enabled."""
        return self.config["detectors"].get(name, True)

