#!/usr/bin/env python3
"""Package the active CSS dependency graph for Sine's submodule-free GitHub ZIPs."""

import argparse
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parent.parent
ENTRYPOINTS = ("userChrome.css", "userContent.css")
LICENSES = (
    "firefox-csshacks/LICENSE",
    "CustomCSSforFx/LICENSE-MPL-v2",
    "CustomCSSforFx/LICENSE-GPL-v3",
)
STRING = r""" "(?:\\.|[^"\\])*" | '(?:\\.|[^'\\])*' """
TOKENS = re.compile(
    rf"""
    (?P<comment>/\*.*?\*/)
    | @import\s+(?P<import_string>{STRING})
    | (?P<url>\burl\(\s*(?:{STRING}|[^)'"\s]*)\s*\))
    | (?P<string>{STRING})
    """,
    re.DOTALL | re.IGNORECASE | re.VERBOSE,
)


def local_references(css):
    """Yield active relative URLs, leaving comments, strings and browser URIs alone."""
    for token in TOKENS.finditer(css):
        if token.lastgroup == "url":
            value = token.group()[4:-1].strip()
        elif token.lastgroup == "import_string":
            value = token.group("import_string")
        else:
            continue
        if value.startswith(("'", '"')):
            value = value[1:-1]
        if "\\" in value:
            raise ValueError(f"CSS escapes in URLs are not supported: {value}")
        parsed = urlsplit(value)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        if parsed.path.startswith("/"):
            raise ValueError(f"Absolute file URL cannot be packaged: {value}")
        yield unquote(parsed.path)


def package_files(root):
    """Keep each stylesheet separate to preserve @namespace scope and import order."""
    root = root.resolve()
    files = {}
    pending = [root / name for name in (*ENTRYPOINTS, *LICENSES)]
    while pending:
        source = pending.pop().resolve()
        if not source.is_relative_to(root) or source.is_relative_to(root / "sine"):
            raise ValueError(f"Dependency is outside the source tree: {source}")
        relative = source.relative_to(root).as_posix()
        if relative in files:
            continue
        if not source.is_file():
            raise ValueError(
                f"Missing dependency: {relative}. "
                "Run git submodule update --init --recursive before building."
            )
        data = source.read_bytes()
        if source.suffix in (".css", ".svg") or relative in LICENSES:
            # Git checkouts may use CRLF; keep generated output identical on every OS.
            text = data.decode("utf-8-sig").replace("\r\n", "\n")
            data = text.encode("utf-8")
        if source.suffix == ".css":
            css = data.decode("utf-8")
            pending.extend(source.parent / ref for ref in local_references(css))
        files[relative] = data
    return files


def build(root, check=False):
    files = package_files(root)
    output = root / "sine"
    existing = {
        path.relative_to(output).as_posix(): path
        for path in output.rglob("*")
        if path.is_file()
    }
    changed = [
        name for name, data in files.items()
        if name not in existing or existing[name].read_bytes() != data
    ]
    obsolete = sorted(existing.keys() - files.keys())
    if check:
        if changed or obsolete:
            raise ValueError(
                "Sine package is out of date: "
                + ", ".join(sorted(changed) + obsolete)
                + ". Run python scripts/build-sine.py and commit the sine directory."
            )
    else:
        for name, data in files.items():
            target = output / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        for name in obsolete:
            existing[name].unlink()
    return len(files)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if generated files are stale")
    args = parser.parse_args()
    try:
        count = build(ROOT, args.check)
    except (ValueError, OSError) as error:
        print(f"Sine packaging failed: {error}", file=sys.stderr)
        return 1
    print(f"Sine package {'verified' if args.check else 'built'}: {count} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
