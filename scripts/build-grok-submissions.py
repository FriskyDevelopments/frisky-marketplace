"""Generate pinned Grok submission entries without publishing or altering the catalog."""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

def build_entries(sha):
    if not re.fullmatch('[0-9a-f]{40}', sha) or sha == '0' * 40:
        raise ValueError('A real, full 40-character pushed commit SHA is required')
    catalog = json.loads((ROOT / '.grok-plugin/marketplace.json').read_text())
    domains = {'frisky-dev-make':['us2.make.com'], 'frisky-dev-mcp':['mcp.friskydev.com'], 'frisky-dev-n8n':['frisky.app.n8n.cloud']}
    entries = []
    for plugin in catalog['plugins']:
        entry = dict(plugin)
        entry['source'] = {'source':'url','url':'https://github.com/FriskyDevelopments/frisky-marketplace.git','sha':sha,'path':plugin['source']['path'].removeprefix('./')}
        entry['keywords'] = ['frisky', 'mcp', plugin['name']]
        entry['domains'] = domains[plugin['name']]
        entry['homepage'] = 'https://github.com/FriskyDevelopments/frisky-marketplace'
        entries.append(entry)
    return entries

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sha', required=True)
    p.add_argument('--output-dir', type=Path, default=Path('grok-submissions'))
    args = p.parse_args()
    try:
        entries = build_entries(args.sha)
    except ValueError as exc:
        p.error(str(exc))
    # New output directory only: never overwrite a reviewed submission.
    args.output_dir.mkdir(parents=True, exist_ok=False)
    for entry in entries:
        (args.output_dir / (entry['name'] + '.json')).write_text(json.dumps(entry, indent=2) + '\n')
    print('Generated three pinned entries; no publication performed.')

if __name__ == '__main__':
    main()
