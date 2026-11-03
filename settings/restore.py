#!/usr/bin/env python3
"""Restore reviewed preferences; back up every overwritten file/domain first."""
import argparse
import datetime
import json
import os
from pathlib import Path
import plistlib
import shutil
import sqlite3
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
HOME = Path.home()


def export_domain(domain):
    result = subprocess.run(['/usr/bin/defaults', 'export', domain, '-'], capture_output=True)
    return plistlib.loads(result.stdout) if result.returncode == 0 else {}


def restore(dry_run=False):
    manifest = json.loads((ROOT / 'settings/manifest.json').read_text())
    alfred_root = HOME / 'Library/Application Support/Alfred'
    metadata = alfred_root / 'prefs.json'
    local_hash = None
    current = alfred_root / 'Alfred.alfredpreferences'
    if metadata.exists():
        info = json.loads(metadata.read_text())
        current = Path(info.get('current', str(current))).expanduser()
        local_hash = info.get('localhash')
    if not local_hash:
        raise SystemExit('Start Alfred once, quit it, then run restore again (missing Alfred localhash).')
    for entry in manifest['preferences']:
        plistlib.loads((ROOT / entry['source']).read_bytes())
    for entry in manifest['files']:
        if not (ROOT / entry['source']).is_file():
            raise FileNotFoundError(entry['source'])
        if entry.get('merge_json'):
            json.loads((ROOT / entry['source']).read_text())
            target = HOME / entry['target']
            if target.exists():
                json.loads(target.read_text())
    with sqlite3.connect(':memory:') as db:
        db.executescript((ROOT / 'settings/input-source-pro/Main.sql').read_text())
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise RuntimeError('Invalid Input Source Pro snapshot')
    backup = HOME / 'Library/Application Support/mac-transfer/backups' / datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    if not dry_run:
        os.umask(0o077)
        backup.mkdir(parents=True)

    def save_existing(target):
        if target.exists() or target.is_symlink():
            dest = backup / 'files' / target.relative_to(HOME)
            dest.parent.mkdir(parents=True, exist_ok=True)
            if target.is_dir():
                shutil.copytree(target, dest, symlinks=True)
            else:
                shutil.copy2(target, dest, follow_symlinks=True)

    for entry in manifest['preferences']:
        domain = entry['domain']
        source = ROOT / entry['source']
        values = plistlib.loads(source.read_bytes())
        print(f'Preferences: {domain} ({len(values)} keys)')
        if dry_run:
            continue
        existing = export_domain(domain)
        dest = backup / 'preferences' / (domain + '.plist')
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(plistlib.dumps(existing))
        existing.update(values)
        with tempfile.NamedTemporaryFile(suffix='.plist') as temp:
            temp.write(plistlib.dumps(existing))
            temp.flush()
            subprocess.run(['/usr/bin/defaults', 'import', domain, temp.name], check=True)

    # Existing Alfred installation has its own machine-local preference directory.
    for entry in manifest['files']:
        source = ROOT / entry['source']
        if entry.get('alfred'):
            relative = entry['target']
            if '{localhash}' in relative and not local_hash:
                raise SystemExit('Start Alfred once, quit it, then run restore again (missing Alfred localhash).')
            target = current / relative.replace('{localhash}', local_hash or '')
        else:
            target = HOME / entry['target']
        print(f'File: {target}')
        if dry_run:
            continue
        merged = None
        if entry.get('merge_json'):
            merged = json.loads(target.read_text()) if target.exists() else {}
            merged.update(json.loads(source.read_text()))
        # Alfred may sync outside HOME: preserve it separately in that case.
        if not target.is_relative_to(HOME):
            if target.exists():
                dest = backup / 'external-alfred' / target.relative_to(current)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, dest)
        else:
            save_existing(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink():
            target.unlink()
        if merged is not None:
            target.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + '\n')
        else:
            shutil.copy2(source, target)

    source = ROOT / 'settings/input-source-pro/Main.sql'
    target = HOME / 'Library/Application Support/Input Source Pro/Main.sqlite'
    print(f'Database: {target}')
    # Validate the SQL snapshot even in dry-run mode.
    with sqlite3.connect(':memory:') as db:
        db.executescript(source.read_text())
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise RuntimeError('Invalid Input Source Pro snapshot')
        if not dry_run:
            for suffix in ['', '-wal', '-shm']:
                item = Path(str(target) + suffix)
                save_existing(item)
                if item.exists() or item.is_symlink():
                    item.unlink()
            target.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(target) as output:
                db.backup(output)
    if not dry_run:
        print(f'Original settings saved to: {backup}')
    print('Log out and back in after restoration. Grant accessibility/input-monitoring permissions manually.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if not args.dry_run:
        running = []
        for name in ['Alfred', 'Alfred Preferences', 'Rectangle', 'Input Source Pro', 'Scroll Reverser', 'Snipaste', 'Cursor', 'Karabiner-Elements', 'Flux', 'IINA', 'Typeless']:
            if subprocess.run(['/usr/bin/pgrep', '-x', name], stdout=subprocess.DEVNULL).returncode == 0:
                running.append(name)
        if running:
            parser.error('Quit these apps before restoring: ' + ', '.join(running))
    restore(args.dry_run)
