import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
START = "<!-- app-compatibility:start -->"
END = "<!-- app-compatibility:end -->"


def render_table(index, compatibility):
    names = [plugin["name"] for plugin in index["plugins"]]
    if set(compatibility) != set(names):
        raise ValueError("Compatibility entries must match the marketplace plugin names")
    rows = ["| Plugin | Supported Kimi app versions |", "|--------|-----------------------------|"]
    for name in sorted(names):
        versions = compatibility[name]
        if versions is not None:
            if (not isinstance(versions, list) or not versions
                    or any(not isinstance(v, str) or not re.fullmatch(r"[0-9A-Za-z.+-]+", v)
                           for v in versions)
                    or len(set(versions)) != len(versions)):
                raise ValueError(f"{name}: use null or a nonempty list of unique version labels")
        label = ", ".join(f"`{v}`" for v in versions) if versions else "Not yet verified"
        rows.append(f"| `{name}` | {label} |")
    return "\n".join([START, *rows, END])


def main():
    parser = argparse.ArgumentParser(description="Show or check the README app compatibility table")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    table = render_table(json.loads((ROOT / "plugins.json").read_text()),
                         json.loads((ROOT / "app-compatibility.json").read_text()))
    if args.check:
        readme = (ROOT / "README.md").read_text()
        if readme.count(START) != 1 or readme.count(END) != 1 or table not in readme:
            parser.exit(1, "README app compatibility table is stale; regenerate with this script.\n")
        print("App compatibility table is up to date.")
    else:
        print(table)


if __name__ == "__main__":
    main()
