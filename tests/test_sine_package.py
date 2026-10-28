import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("build_sine", ROOT / "scripts" / "build-sine.py")
packager = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packager)


class SinePackageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for name in (*packager.ENTRYPOINTS, *packager.LICENSES):
            self.write(name, b"/* fixture */\n")

    def write(self, name, data):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def test_only_active_local_references_are_collected(self):
        css = '''
            /* @import url(missing.css); */
            @import url("nested/first.css");
            @import 'nested/second.css';
            @import url(nested/third.css) screen;
            a {
                content: "url(not-a-file.svg)";
                background: URL('../icons/an%20icon.svg#part');
                mask: url(data:image/svg+xml;base64,AAAA);
                list-style: url(chrome://browser/skin/tab.svg);
                cursor: url(resource://gre/image.svg);
                filter: url(#filter);
            }
            @namespace url("http://www.w3.org/1999/xhtml");
            @-moz-document url("about:config") {}
        '''
        self.assertEqual(list(packager.local_references(css)), [
            "nested/first.css", "nested/second.css", "nested/third.css",
            "../icons/an icon.svg",
        ])

    def test_dependency_graph_preserves_namespaces_and_binary_assets(self):
        self.write("userChrome.css", b'@import url(custom/theme.css);\r\n')
        nested = b'@namespace url("http://www.w3.org/1999/xhtml");\n'
        nested += b'a { background: url(../icons/test.png); }\n'
        self.write("custom/theme.css", nested)
        self.write("icons/test.png", b"\x00\x01\xff")
        files = packager.package_files(self.root)
        self.assertEqual(files["custom/theme.css"], nested)
        self.assertEqual(files["icons/test.png"], b"\x00\x01\xff")
        self.assertEqual(files["userChrome.css"], b'@import url(custom/theme.css);\n')
        self.assertTrue(set(packager.LICENSES).issubset(files))

    def test_text_output_is_independent_of_checkout_line_endings(self):
        self.write("userChrome.css", b'a { background: url(icons/test.svg); }\r\n')
        self.write("icons/test.svg", b"<svg>\r\n</svg>\r\n")
        self.write(packager.LICENSES[0], b"license\r\n")
        files = packager.package_files(self.root)
        self.assertEqual(files["icons/test.svg"], b"<svg>\n</svg>\n")
        self.assertEqual(files[packager.LICENSES[0]], b"license\n")

    def test_import_cycles_terminate(self):
        self.write("userChrome.css", b'@import "custom/cycle.css";')
        self.write("custom/cycle.css", b'@import "../userChrome.css";')
        self.assertIn("custom/cycle.css", packager.package_files(self.root))

    def test_missing_dependency_fails_explicitly(self):
        self.write("userChrome.css", b'@import url(missing.css);')
        with self.assertRaisesRegex(ValueError, "Missing dependency: missing.css"):
            packager.package_files(self.root)

    def test_path_escape_is_rejected(self):
        self.write("userChrome.css", b'@import "../outside.css";')
        with self.assertRaisesRegex(ValueError, "outside the source tree"):
            packager.package_files(self.root)

    def test_generated_sources_cannot_be_imported(self):
        self.write("userChrome.css", b'@import "sine/userChrome.css";')
        with self.assertRaisesRegex(ValueError, "outside the source tree"):
            packager.package_files(self.root)

    def test_check_detects_stale_missing_and_obsolete_files(self):
        packager.build(self.root)
        packager.build(self.root, check=True)
        for name, action in (
            ("userChrome.css", "change"),
            ("userContent.css", "remove"),
            ("unused.css", "add"),
        ):
            with self.subTest(action=action):
                path = self.root / "sine" / name
                if action == "remove":
                    path.unlink()
                else:
                    path.write_bytes(b"/* stale */")
                with self.assertRaisesRegex(ValueError, "out of date"):
                    packager.build(self.root, check=True)
                packager.build(self.root)
                packager.build(self.root, check=True)

    def test_github_zip_install_has_every_dependency_without_submodules(self):
        # GitHub archives contain gitlinks, not the contents of submodules.
        names = subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=ROOT,
        ).decode().split("\0")
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w") as bundle:
            for name in sorted(set(filter(None, names))):
                source = ROOT / name
                if source.is_file():
                    bundle.writestr(name, source.read_bytes())
        archive.seek(0)
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(self.root / "installed")
            names = set(bundle.namelist())
        manifest = json.loads((ROOT / "theme.json").read_text(encoding="utf-8"))
        self.assertEqual(set(manifest["style"]), {"chrome", "content"})
        self.assertTrue(manifest["id"])
        self.assertNotIn("homepage", manifest)
        self.assertNotIn("updatedAt", manifest)
        self.assertNotIn("firefox-csshacks/chrome/dark_checkboxes_and_radios.css", names)
        pending = []
        installed = (self.root / "installed").resolve()
        for name in manifest["style"].values():
            self.assertTrue(name.startswith("sine/"))
            self.assertIn(name, names)
            pending.append(installed / name)
        visited = set()
        while pending:
            path = pending.pop().resolve()
            if path in visited:
                continue
            visited.add(path)
            self.assertTrue(path.is_relative_to(installed / "sine"), str(path))
            self.assertTrue(path.is_file(), str(path))
            if path.suffix == ".css":
                pending.extend(
                    path.parent / ref
                    for ref in packager.local_references(path.read_text(encoding="utf-8"))
                )
        self.assertGreater(len(visited), 30)
        self.assertTrue(any(path.suffix == ".svg" for path in visited))


if __name__ == "__main__":
    unittest.main()
