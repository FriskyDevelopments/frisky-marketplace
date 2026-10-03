import argparse
import html
import re

from scripts.marketplace import ROOT, local_path, read_json, validate_index_paths


def cell(value):
    return html.escape(value).replace("|", "&#124;").replace("\n", " ")


def replace_region(text, name, content):
    start = f"<!-- BEGIN GENERATED {name} -->"
    end = f"<!-- END GENERATED {name} -->"
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError(f"Expected one generated {name} region")
    pattern = re.escape(start) + r".*?" + re.escape(end)
    result, count = re.subn(pattern, lambda _: f"{start}\n{content}\n{end}", text, flags=re.DOTALL)
    if count != 1:
        raise ValueError(f"Invalid generated {name} region")
    return result


def generate_readme(text, index, root=ROOT):
    validate_index_paths(index, root)
    rows = [
        "| # | | Plugin | What it wires into your chats | Category |",
        "|---|-|--------|-------------------------------|----------|",
    ]
    for number, entry in enumerate(index["plugins"], 1):
        icon = ""
        description = entry.get("description", "")
        if "path" in entry:
            directory = local_path(root, entry["path"])
            manifest = read_json(directory / "kimi.plugin.json")
            description = manifest["interface"].get("shortDescription", description)
            icons = sorted(p for p in directory.glob("icon.*") if p.suffix in {".svg", ".png", ".jpg", ".jpeg"})
            if icons:
                source = "./" + icons[0].relative_to(root).as_posix()
                icon = f'<img src="{html.escape(source, quote=True)}" width="24" alt="{cell(entry["name"])}">'
        target = entry.get("path", entry.get("url", ""))
        rows.append(
            f'| {number:02d} | {icon} | [**{cell(entry["name"])}**]({target}) | '
            f'{cell(description)} | `{cell(entry.get("category", ""))}` |'
        )
    count = len(index["plugins"])
    text = replace_region(text, "COUNT", f"![plugins](https://img.shields.io/badge/plugins-{count}-00e5ff?style=flat-square)")
    text = replace_region(text, "TAGLINE", f"**{count} connectors · one org tab · zero ceremony**")
    return replace_region(text, "ROSTER", "\n".join(rows))


def main():
    parser = argparse.ArgumentParser(description="Generate the README roster and plugin count")
    parser.add_argument("--check", action="store_true", help="Fail if generated README content is stale")
    args = parser.parse_args()
    path = ROOT / "README.md"
    current = path.read_text(encoding="utf-8")
    generated = generate_readme(current, read_json(ROOT / "plugins.json"))
    if args.check:
        if current != generated:
            parser.exit(1, "README is stale; run python -m scripts.generate_roster\n")
    elif current != generated:
        path.write_text(generated, encoding="utf-8")


if __name__ == "__main__":
    main()
