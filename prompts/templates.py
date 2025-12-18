import os
import yaml
from pathlib import Path
from typing import Dict, Any, Tuple

# Base directory for prompts
PROMPT_DIR = Path(__file__).parent

class PromptLoader:
    def __init__(self):
        self._prompts = {}
        self._configs = {}
        self._load_all()

    def _load_all(self):
        """Load all markdown prompt files in the directory."""
        for md_file in PROMPT_DIR.glob("*.md"):
            name = md_file.stem
            content, config = self._parse_file(md_file)
            self._prompts[name] = content
            self._configs[name] = config

    def _parse_file(self, filepath: Path) -> Tuple[str, Dict[str, Any]]:
        """Parse a markdown file with YAML front matter."""
        text = filepath.read_text(encoding="utf-8")
        
        if text.startswith("---\n"):
            parts = text.split("---\n", 2)
            if len(parts) >= 3:
                # Part 0 is empty, Part 1 is YAML, Part 2 is content
                try:
                    front_matter = yaml.safe_load(parts[1])
                    content = parts[2].strip()
                    # Extract 'model_config' if present, otherwise use entire front matter
                    config = front_matter.get("model_config", {})
                    return content, config
                except yaml.YAMLError as e:
                    print(f"Warning: Failed to parse YAML in {filepath}: {e}")
                    return text, {}
        
        # Fallback for files without front matter
        return text, {}

    def get_prompt(self, role: str) -> str:
        """Get the raw prompt text for a role."""
        return self._prompts.get(role, "")

    def get_config(self, role: str) -> Dict[str, Any]:
        """Get the model configuration for a role."""
        return self._configs.get(role, {})

# Singleton instance for easy import
loader = PromptLoader()

# Exposed variables for direct access
# Example usage: from prompts.templates import AffirmativePrompt, AffirmativeConfig
AffirmativePrompt = loader.get_prompt("affirmative")
AffirmativeConfig = loader.get_config("affirmative")

NegativePrompt = loader.get_prompt("negative")
NegativeConfig = loader.get_config("negative")

AdjudicatorPrompt = loader.get_prompt("adjudicator")
AdjudicatorConfig = loader.get_config("adjudicator")
