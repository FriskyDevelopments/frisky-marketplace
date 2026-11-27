import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
renderer = load('renderer', 'render-vibe-config.py')
validator = load('validator', 'validate-marketplace.py')
submissions = load('submissions', 'build-grok-submissions.py')

class MarketplaceTests(unittest.TestCase):
    def setUp(self):
        self.template = (ROOT / 'mistral/vibe-config.toml').read_text()
        self.env = {'MAKE_MCP_URL':'https://us2.make.com/mcp/test-toolbox', 'MAKE_MCP_TOKEN':'test-secret-never-written','N8N_MCP_TOKEN':'another-test-secret'}
    def test_all_structural_checks(self):
        self.assertTrue(validator.validate())
    def test_renderer_preserves_secret_variable_names(self):
        text = renderer.render(self.template, self.env)
        self.assertNotIn(self.env['MAKE_MCP_TOKEN'], text)
        self.assertNotIn(self.env['N8N_MCP_TOKEN'], text)
        config = tomllib.loads(text)
        self.assertEqual(config['mcp_servers'][0]['auth']['api_key_env'], 'MAKE_MCP_TOKEN')
        self.assertEqual(config['mcp_servers'][0]['url'], self.env['MAKE_MCP_URL'])
    def test_reject_missing_url(self):
        with self.assertRaises(ValueError): renderer.render(self.template, {})
    def test_reject_http_url(self):
        with self.assertRaises(ValueError): renderer.render(self.template, {'MAKE_MCP_URL':'http://us2.make.com/mcp'})
    def test_reject_unapproved_host(self):
        with self.assertRaises(ValueError): renderer.render(self.template, {'MAKE_MCP_URL':'https://example.com/mcp'})
    def test_reject_credential_url(self):
        with self.assertRaises(ValueError): renderer.render(self.template, {'MAKE_MCP_URL':'https://user:pass@us2.make.com/mcp'})
    def test_reject_unresolved_variables(self):
        with self.assertRaises(ValueError): renderer.render(self.template+'\n# ${UNKNOWN}\n', self.env)
    def test_renderer_private_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)/'config.toml'
            cmd=[sys.executable,str(ROOT/'scripts/render-vibe-config.py'),'--output',str(output)]
            env={**os.environ,**self.env}
            self.assertEqual(subprocess.run(cmd,env=env,capture_output=True).returncode,0)
            self.assertEqual(output.stat().st_mode & 0o777,0o600)
            before=output.read_bytes()
            self.assertNotEqual(subprocess.run(cmd,env=env,capture_output=True).returncode,0)
            self.assertEqual(output.read_bytes(),before)
    def test_missing_manifest_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy=Path(tmp)/'repo';shutil.copytree(ROOT,copy,ignore=shutil.ignore_patterns('__pycache__'))
            (copy/'plugins/frisky-dev-mcp/.grok-plugin/plugin.json').unlink()
            with self.assertRaises(FileNotFoundError):validator.validate(copy)
    def test_submission_pins_real_revision_and_subdir(self):
        entries=submissions.build_entries('544ddafaac130e36582389580c734514f083fc9c')
        self.assertEqual(len(entries),3)
        for e in entries:
            self.assertEqual(e['source']['sha'],'544ddafaac130e36582389580c734514f083fc9c')
            self.assertEqual(e['source']['path'],'plugins/'+e['name'])
            self.assertTrue(e['domains'])
    def test_submission_rejects_branch_and_placeholder(self):
        for bad in ('main','HEAD','abc','0'*40):
            with self.assertRaises(ValueError):submissions.build_entries(bad)

if __name__ == '__main__': unittest.main()
