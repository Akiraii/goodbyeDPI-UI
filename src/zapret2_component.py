"""Windows Zapret2 bundle installer and argument parser.

The upstream Windows distribution is bol-van/zapret-win-bundle, NOT the
zapret2 source release. Keep the two engine directories independent.
"""
from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import tempfile
import zipfile

REQUIRED_FILES = (
    "winws2.exe", "WinDivert.dll", "WinDivert64.sys", "cygwin1.dll",
    "lua/zapret-lib.lua", "lua/zapret-antidpi.lua",
)
ALLOWED_ROOT_FILES = {
    "winws2.exe", "WinDivert.dll", "WinDivert64.sys", "cygwin1.dll",
}
ALLOWED_DIRECTORIES = {"lua", "files", "windivert.filter"}
MAX_FILE_SIZE = 48 * 1024 * 1024
MAX_EXTRACTED_SIZE = 192 * 1024 * 1024


def validate_zapret2_files(destination: str | os.PathLike) -> bool:
    root = Path(destination)
    for name in REQUIRED_FILES:
        file = root.joinpath(*PurePosixPath(name).parts)
        if not file.is_file() or file.stat().st_size == 0:
            return False
    try:
        with (root / "winws2.exe").open("rb") as executable:
            return executable.read(2) == b"MZ"
    except OSError:
        return False


def parse_zapret2_arguments(text: str) -> list[str]:
    """Split argument text, preserving quotes in embedded Lua expressions."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Zapret2 strategy is empty; enter a validated winws2 command.")
    if "\x00" in text or len(text) > 65536:
        raise ValueError("Invalid Zapret2 arguments.")
    # shlex is used for whitespace/quotes only; subprocess starts EXE directly,
    # shell=False. Prefer forward slashes in resource paths on Windows.
    args = shlex.split(text, posix=True)
    if not args:
        raise ValueError("Zapret2 strategy is empty.")
    if any(x.lower().endswith("winws2.exe") for x in args):
        raise ValueError("Enter only arguments, without winws2.exe.")
    if any(x in ("^", "&&", "||", "|") for x in args):
        raise ValueError("Batch syntax is not supported in strategy arguments.")
    return args


def install_zapret2_archive(archive: str, destination: str) -> None:
    """Stage and validate selected Windows bundle files before replacing engine.

    User-modified file lists are preserved when already present. The previous
    complete engine directory is kept in .zapret2-previous for manual rollback.
    """
    dest = Path(destination).resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".zapret2-stage-", dir=dest.parent))
    backup = dest.parent / ".zapret2-previous"
    swapped = False
    try:
        if dest.exists():
            shutil.copytree(dest, staging, dirs_exist_ok=True)

        extracted = set()
        total_size = 0
        with zipfile.ZipFile(archive) as zf:
            for member in zf.infolist():
                if member.is_dir():
                    continue
                # Archive root is name-commit/; locate the nested official
                # zapret-winws/ folder independent of archive SHA.
                bits = PurePosixPath(member.filename.replace("\\", "/")).parts
                if "zapret-winws" not in bits:
                    continue
                pos = bits.index("zapret-winws")
                rel_parts = bits[pos + 1:]
                if not rel_parts or any(p in ("", ".", "..") for p in rel_parts):
                    continue
                root = rel_parts[0]
                if not (
                    (len(rel_parts) == 1 and root in ALLOWED_ROOT_FILES)
                    or (len(rel_parts) > 1 and root in ALLOWED_DIRECTORIES)
                ):
                    continue
                if member.file_size > MAX_FILE_SIZE:
                    raise ValueError("Oversized file in Zapret2 bundle")
                total_size += member.file_size
                if total_size > MAX_EXTRACTED_SIZE:
                    raise ValueError("Zapret2 bundle exceeds size limit")
                # Skip symlinks and any file with OS-specific path ambiguity.
                if member.external_attr >> 16 & 0o170000 == 0o120000:
                    raise ValueError("Symlink in Zapret2 bundle")
                if any(":" in part or "\\" in part for part in rel_parts):
                    raise ValueError("Invalid Zapret2 archive path")
                target = staging.joinpath(*rel_parts)
                if not target.resolve().is_relative_to(staging.resolve()):
                    raise ValueError("Unsafe Zapret2 archive path")
                name = "/".join(rel_parts)
                if name in extracted:
                    raise ValueError("Duplicate file in Zapret2 archive")
                extracted.add(name)
                # Keep custom/local user host lists on update.
                if root == "files" and target.exists():
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member) as source, target.open("wb") as sink:
                    shutil.copyfileobj(source, sink)

        if not validate_zapret2_files(staging):
            raise ValueError("Official Windows bundle is incomplete")
        if backup.exists():
            shutil.rmtree(backup)
        if dest.exists():
            os.replace(dest, backup)
            swapped = True
        try:
            os.replace(staging, dest)
        except Exception:
            if swapped and backup.exists():
                os.replace(backup, dest)
            raise
    finally:
        if staging.exists():
            shutil.rmtree(staging)
