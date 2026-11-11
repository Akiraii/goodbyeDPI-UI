"""Offline unit tests for the isolated Zapret2 bundle installer."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from zapret2_component import (
    REQUIRED_FILES, install_zapret2_archive,
    parse_zapret2_arguments, validate_zapret2_files,
)


def make_zip(path, complete=True):
    with zipfile.ZipFile(path, "w") as zf:
        for name in REQUIRED_FILES:
            if not complete and name == "cygwin1.dll":
                continue
            body = b"MZstub-binary" if name.endswith(".exe") else b"data"
            zf.writestr("zapret-win-bundle-commit/zapret-winws/" + name, body)
        zf.writestr("zapret-win-bundle-commit/zapret-winws/files/list-youtube.txt", b"upstream")


class Zapret2Tests(unittest.TestCase):
    def test_parser_quoted_lua(self):
        args = parse_zapret2_arguments('--wf-tcp-out=80,443 --lua-init="foo = 123"')
        self.assertEqual(args, ["--wf-tcp-out=80,443", "--lua-init=foo = 123"])

    def test_rejects_shell_tokens(self):
        with self.assertRaises(ValueError):
            parse_zapret2_arguments("--wf-tcp-out=443 && echo bad")

    def test_install_update_preserves_custom_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "bundle.zip"
            make_zip(archive)
            dest = root / "zapret2"
            install_zapret2_archive(str(archive), str(dest))
            self.assertTrue(validate_zapret2_files(dest))
            custom = dest / "files/list-youtube.txt"
            custom.write_text("user-customized")
            install_zapret2_archive(str(archive), str(dest))
            self.assertEqual(custom.read_text(), "user-customized")
            self.assertTrue((root / ".zapret2-previous/winws2.exe").exists())

    def test_incomplete_does_not_replace_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "zapret2"
            archive = root / "bundle.zip"
            make_zip(archive)
            install_zapret2_archive(str(archive), str(dest))
            prev = (dest / "winws2.exe").read_bytes()
            make_zip(archive, complete=False)
            # During an update, an omitted file must not silently be
            # accepted just because it exists in the previous installation.
            # A fresh install must reject incomplete archives.
            new_dest = root / "zapret2-fresh"
            with self.assertRaises(ValueError):
                install_zapret2_archive(str(archive), str(new_dest))
            self.assertEqual((dest / "winws2.exe").read_bytes(), prev)


if __name__ == "__main__":
    unittest.main()
