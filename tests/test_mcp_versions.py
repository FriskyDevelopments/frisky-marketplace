import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
EXACT_PACKAGE = re.compile(
    r"(?:@[a-z0-9._-]+/)?[a-z0-9._-]+@"
    r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?"
)
# Public npm returned 404 on 2026-10-03; remove once a release is verified.
UNAVAILABLE_PACKAGES = {
    ("framer/kimi.plugin.json", "framer", "framer-mcp-server"),
}


class McpVersionTests(unittest.TestCase):
    def test_local_launch_packages_are_pinned(self):
        paths = sorted(ROOT.glob("*/kimi.plugin.json"))
        paths += sorted(ROOT.glob("*/.mcp.json"))
        self.assertTrue(paths)
        for path in paths:
            servers = json.loads(path.read_text()).get("mcpServers", {})
            for name, server in servers.items():
                if "command" not in server:
                    continue
                with self.subTest(path=str(path.relative_to(ROOT)), server=name):
                    self.assertEqual(server["command"], "npx")
                    args = server["args"]
                    self.assertGreaterEqual(len(args), 2)
                    self.assertEqual(args[0], "-y")
                    package = args[1]
                    exception = (path.relative_to(ROOT).as_posix(), name, package)
                    if exception not in UNAVAILABLE_PACKAGES:
                        self.assertIsNotNone(EXACT_PACKAGE.fullmatch(package))

    def test_convex_mirror_matches_manifest(self):
        folder = ROOT / "convex-connector"
        manifest = json.loads((folder / "kimi.plugin.json").read_text())
        mirror = json.loads((folder / ".mcp.json").read_text())
        self.assertEqual(manifest["mcpServers"], mirror["mcpServers"])

    def test_exact_version_format_rejects_floating_references(self):
        for package in ("convex", "convex@latest", "convex@^1.45.0",
                        "convex@~1.45.0", "convex@1.45", "convex@*"):
            with self.subTest(package=package):
                self.assertIsNone(EXACT_PACKAGE.fullmatch(package))
        for package in ("convex@1.45.0", "@example/mcp@1.2.3-beta.1"):
            with self.subTest(package=package):
                self.assertIsNotNone(EXACT_PACKAGE.fullmatch(package))
