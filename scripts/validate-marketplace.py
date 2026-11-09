"""Structural validation for the three Frisky cross-client plugins; no network calls."""
import json
from pathlib import Path
import re
import tomllib

ROOT = Path(__file__).resolve().parents[1]
NAMES = {'frisky-dev-make', 'frisky-dev-mcp', 'frisky-dev-n8n'}

def read(root, path):
    return json.loads((root / path).read_text())

def validate(root=ROOT):
    for flavor in ('claude', 'grok'):
        catalog = read(root, f'.{flavor}-plugin/marketplace.json')
        assert catalog['name'] == 'frisky-dev'
        entries = catalog['plugins']
        assert len(entries) == len(NAMES)
        assert {e['name'] for e in entries} == NAMES
        for entry in entries:
            name = entry['name']
            source = entry['source']
            relative = source if isinstance(source, str) else source['path']
            assert relative == f'./plugins/{name}', f'{name}: wrong source path'
            plugin = (root / relative).resolve()
            assert plugin.is_relative_to(root.resolve()), 'Source escapes repository'
            manifest = read(plugin, f'.{flavor}-plugin/plugin.json')
            assert manifest['name'] == name and manifest['version']
            servers = read(plugin, '.mcp.json')['mcpServers']
            assert len(servers) == 1
            for server in servers.values():
                assert server['type'] == 'http'
                url = server['url']
                assert url.startswith('https://') or url == '${MAKE_MCP_URL}'
                for header in server.get('headers', {}).values():
                    assert re.fullmatch(r'Bearer \$\{[A-Z0-9_]+\}', header), 'Literal credential/header forbidden'
    assert read(root, '.agents/plugins/marketplace.json') == read(root, '.claude-plugin/marketplace.json')
    frisky = read(root, 'plugins/frisky-dev-mcp/.mcp.json')['mcpServers']['frisky']
    assert frisky['url'] == 'https://mcp.friskydev.com/mcp' and 'headers' not in frisky
    cloud = read(root, 'plugins/frisky-dev-n8n/.mcp.json')['mcpServers']['n8n']
    assert cloud['url'] == 'https://frisky.app.n8n.cloud/mcp-server/http'
    legacy = read(root, 'n8n-connector/kimi.plugin.json')['mcpServers']['n8n-connector']
    assert legacy['url'] == 'https://n8n.friskydev.com/mcp-server/http'
    config = tomllib.loads((root / 'mistral/vibe-config.toml').read_text())
    entries = {e['name']: e for e in config['mcp_servers']}
    assert set(entries) == NAMES
    for e in entries.values():
        assert e['transport'] == 'streamable-http' and 'headers' not in e
    assert entries['frisky-dev-mcp']['auth'] == {'type':'oauth', 'scopes':['frisky.mcp']}
    for name, var in [('frisky-dev-make','MAKE_MCP_TOKEN'), ('frisky-dev-n8n','N8N_MCP_TOKEN')]:
        auth = entries[name]['auth']
        assert auth == {'type':'static', 'api_key_env':var,'api_key_header':'Authorization','api_key_format':'Bearer {token}'}
    worksheet = read(root, 'mistral/connectors.json')
    assert {e['name'] for e in worksheet['connectors']} == NAMES
    return True

if __name__ == '__main__':
    validate()
    print('Three plugins validated across Claude/Grok; Vibe authentication and distinct n8n targets checked.')
