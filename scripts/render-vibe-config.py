"""Render the Vibe template without writing token values or overwriting user config."""
import argparse
import json
import os
from pathlib import Path
import re
import tomllib
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]

def render(template, env):
    url = env.get("MAKE_MCP_URL", "")
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != "us2.make.com" or parsed.username or parsed.password or any(c.isspace() for c in url):
        raise ValueError("MAKE_MCP_URL must be the approved HTTPS us2.make.com toolbox URL")
    # JSON string escaping is also valid for a TOML basic string.
    text = template.replace('"${MAKE_MCP_URL}"', json.dumps(url))
    if re.search(r"\$\{[^}]+\}", text):
        raise ValueError("Unresolved configuration variable")
    tomllib.loads(text)
    return text

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="New file, never an existing Vibe config")
    args = parser.parse_args()
    try:
        text = render((ROOT / "mistral/vibe-config.toml").read_text(), os.environ)
        fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as out:
            out.write(text)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print("Created configuration; review locally and append only missing server entries.")

if __name__ == "__main__":
    main()
