# Zapret2 (feature/zapret2)

This branch adds an **independent Windows Zapret2** engine to GoodbyeDPI-UI,
without replacing classic Zapret.

## Source and installation

- The binary comes from `bol-van/zapret-win-bundle` (the `zapret-winws/` directory).
- Updates use the full 40-character git commit SHA from the official bundle master.
- Required files: winws2.exe, cygwin1.dll, WinDivert.dll, WinDivert64.sys,
  lua/zapret-lib.lua, lua/zapret-antidpi.lua.
- The installer extracts only a safe allowlist of files and directories, stages
  updates and retains the previous files at `data/.zapret2-previous/`.
- The user's default strategy is `data/settings/presets/zapret2/user.json`.
  Use forward slashes in resource paths within custom arguments.
- JSON import/export and the standard single-command, caret-continued
  CMD/BAT examples are supported. Imported scripts are **never executed**.
  Arbitrary batch commands/variables are rejected. Complex custom CMD/BAT
  scripts may require manual conversion.
- Blockcheck2 integration is a separate future step.
- This is a DEVELOPMENT branch. No verified Windows GUI build or live DPI tests yet.

## Testing

Run `python -m unittest discover -s tests -p 'test_zapret2_component.py' -v`.
The same checks are configured as a GitHub Actions workflow on this branch.

## Windows test checklist

1. Launch GoodbyeDPI-UI as administrator on a clean Windows 10/11 x64 VM.
2. Install Zapret2 and run diagnostics. Verify binary and DLL presence.
3. Validate/save a strategy, select Zapret2 and start it.
4. Check logs, network access, and correct stop of the engine process.
5. Verify switching back to classic Zapret; update and roll back Zapret2.
6. Ensure user-modified host lists and other engines' configs are preserved.

Official upstream: https://github.com/bol-van/zapret-win-bundle
