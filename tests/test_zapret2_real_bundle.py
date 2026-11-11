"""Live integration smoke on Windows using the official, current Windows bundle.

This test DOES NOT start packet interception or modify the Windows networking
configuration. It checks the real downloaded archive and --help output.
"""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from zapret2_component import (
    convert_zapret2_batch,
    install_zapret2_archive,
    parse_zapret2_arguments,
    validate_blockcheck2_files,
    validate_zapret2_files,
)

BASE = "https://api.github.com/repos/bol-van/zapret-win-bundle"


def fetch(url, destination=None):
    req = urllib.request.Request(url, headers={"User-Agent": "goodbyeDPI-UI-zapret2-ci"})
    with urllib.request.urlopen(req, timeout=60) as response:
        if destination is None:
            return response.read()
        with open(destination, "wb") as f:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)


def main():
    if os.name != "nt":
        raise RuntimeError("This integration test must run on Windows")
    commit = json.loads(fetch(BASE + "/commits/master"))["sha"]
    if len(commit) != 40:
        raise RuntimeError("Invalid official bundle SHA")
    print("Official bundle commit:", commit, flush=True)
    with tempfile.TemporaryDirectory() as root:
        path = Path(root)
        bundle = path / "bundle.zip"
        fetch(f"https://github.com/bol-van/zapret-win-bundle/archive/{commit}.zip", bundle)
        print("Downloaded archive:", bundle.stat().st_size, "bytes", flush=True)
        with zipfile.ZipFile(bundle) as archive:
            scripts = [
                member for member in archive.namelist()
                if member.endswith("/zapret-winws/preset2_example.cmd")
            ]
            if len(scripts) != 1:
                raise AssertionError("Missing upstream Zapret2 CMD sample")
            raw = archive.read(scripts[0]).decode("utf-8-sig")
            args = parse_zapret2_arguments(convert_zapret2_batch(raw))
            assert "--wf-tcp-out=80,443" in args, args[:3]
            assert any(x.startswith("--lua-init=") for x in args), args[:3]
            print("Official strategy imported:", len(args), "arguments")
        dest = path / "installed"
        install_zapret2_archive(str(bundle), str(dest))
        if not validate_zapret2_files(dest):
            raise AssertionError("Windows binary installation was incomplete")
        if not validate_blockcheck2_files(dest):
            raise AssertionError("Official Blockcheck2 dependencies are incomplete")
        print("Real Windows bundle installation: PASS", flush=True)
        exe = dest / "winws2.exe"
        proc = subprocess.run(
            [str(exe), "--help"],
            cwd=str(dest),
            capture_output=True,
            text=True,
            errors="replace",
            timeout=25,
        )
        output = proc.stdout + proc.stderr
        print("winws2.exe --help exit:", proc.returncode, flush=True)
        print("Output preview:", output[:750], flush=True)
        if not output.strip() or proc.returncode not in (0, 1):
            raise AssertionError("winws2 --help did not start correctly")
        print("Real Windows binary smoke: PASS", flush=True)


if __name__ == "__main__":
    main()
