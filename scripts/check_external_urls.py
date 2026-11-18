"""Check indexed plugin URLs without credentials or MCP tool calls."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
MCP_REACHABLE_STATUSES = {401, 403, 405, 406, 415}


def collect_urls(root):
    targets = []
    index = json.loads((root / "plugins.json").read_text())
    for plugin in index["plugins"]:
        name = plugin["name"]
        if "url" in plugin:
            targets.append((f"{name}:index", plugin["url"], False))
        if "path" not in plugin:
            continue
        manifest = json.loads(
            (root / plugin["path"] / "kimi.plugin.json").read_text()
        )
        interface = manifest.get("interface", {})
        for field in ("websiteURL", "iconUrl"):
            url = interface.get(field, "")
            if url and (field == "websiteURL" or ":" in url or url.startswith("//")):
                targets.append((f"{name}:{field}", url, False))
        for server, config in manifest.get("mcpServers", {}).items():
            if "url" in config:
                targets.append((f"{name}:mcp:{server}", config["url"], True))
    return targets


def request_status(url, method, timeout):
    request = urllib.request.Request(
        url, method=method,
        headers={"User-Agent": "frisky-marketplace-url-check/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status
    except urllib.error.HTTPError as error:
        status = error.code
        error.close()
        return status


def check_url(target, timeout=15):
    label, url, is_mcp = target
    try:
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            return False, f"FAIL {label}: expected an HTTPS URL without credentials"
        status = request_status(url, "HEAD", timeout)
        if status == 405:
            status = request_status(url, "GET", timeout)
        if 200 <= status < 300:
            return True, f"PASS {label}: HTTP {status}"
        if is_mcp and status in MCP_REACHABLE_STATUSES:
            return True, f"PASS {label}: HTTP {status} (auth/protocol gate; reachability only)"
        return False, f"FAIL {label}: HTTP {status}"
    except (urllib.error.URLError, OSError, ValueError) as error:
        # Exception messages and URLs can contain credentials; log neither.
        return False, f"FAIL {label}: {type(error).__name__} (network/TLS/URL error)"


def positive_timeout(value):
    timeout = float(value)
    if not 0 < timeout < float("inf"):
        raise argparse.ArgumentTypeError("timeout must be finite and positive")
    return timeout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=positive_timeout, default=15)
    args = parser.parse_args()
    targets = collect_urls(ROOT)
    with ThreadPoolExecutor(max_workers=6) as executor:
        results = list(executor.map(lambda target: check_url(target, args.timeout), targets))
    for _, message in results:
        print(message)
    failed = sum(not passed for passed, _ in results)
    print(f"Checked {len(results)} external URLs; {failed} failed.")
    return int(failed > 0)


if __name__ == "__main__":
    raise SystemExit(main())
