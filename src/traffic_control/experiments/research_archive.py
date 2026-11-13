"""Exclusive research archives with a portable, independently checked inventory."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile


RESULT_ROOTS = ('results/phase11', 'results/phase11_audit_v1', 'results/followup_v2')


def file_digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify_archive(path: Path) -> dict:
    """Check every member without extraction; reject missing/extra/unsafe entries."""
    with ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('duplicate archive members')
        for name in names:
            parts = PurePosixPath(name)
            if parts.is_absolute() or '..' in parts.parts or '\\' in name or ':' in name:
                raise ValueError('unsafe archive member')
        manifest = json.loads(archive.read('archive_manifest.json'))
        if set(names) != set(manifest['files']) | {'archive_manifest.json'}:
            raise ValueError('archive inventory mismatch')
        for name, expected in manifest['files'].items():
            with archive.open(name) as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            if digest != expected['sha256'] or archive.getinfo(name).file_size != expected['bytes']:
                raise ValueError(f'archive content mismatch: {name}')
    return dict(archive=path.name, bytes=path.stat().st_size, sha256=file_digest(path),
                verified_files=len(manifest['files']), source_commit=manifest['source_commit'])


def build_archive(repository: Path, output: Path) -> dict:
    """Include the named research roots and all history reachable from HEAD.

    Existing outputs are never replaced. Run only after campaigns/analysis stop
    writing. An unsuccessful creation leaves its partial archive for diagnosis.
    """
    repository, output = repository.resolve(), output.resolve()
    if output.exists() or output.with_suffix('.sha256.json').exists():
        raise FileExistsError(output)
    status = subprocess.check_output(['git', 'status', '--porcelain'], cwd=repository, text=True)
    if status.strip():
        raise ValueError('archive requires a clean committed source tree')
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repository, text=True).strip()
    roots = [repository / name for name in RESULT_ROOTS]
    if any(not root.is_dir() for root in roots):
        raise FileNotFoundError('all declared research result roots must be present')
    if any(output.is_relative_to(root) for root in roots):
        raise ValueError('archive output must be outside its input roots')
    paths = sorted(path for root in roots for path in root.rglob('*') if path.is_file())
    if any(path.is_symlink() or not path.resolve().is_relative_to(repository) for path in paths):
        raise ValueError('research input must be an ordinary in-repository file')
    output.parent.mkdir(parents=True, exist_ok=True)
    inventory = {}
    with TemporaryDirectory(prefix='traffic-research-bundle-') as temporary:
        bundle = Path(temporary) / 'repository.bundle'
        subprocess.run(['git', 'bundle', 'create', str(bundle), 'HEAD'], cwd=repository,
                       check=True, capture_output=True)
        subprocess.run(['git', 'bundle', 'verify', str(bundle)], cwd=repository,
                       check=True, capture_output=True)
        with ZipFile(output, 'x', compression=ZIP_DEFLATED, compresslevel=6) as archive:
            entries = [(p.relative_to(repository).as_posix(), p) for p in paths]
            entries.append(('source/repository.bundle', bundle))
            for name, path in entries:
                expected = dict(bytes=path.stat().st_size, sha256=file_digest(path))
                archive.write(path, name)
                inventory[name] = expected
            manifest = dict(schema='traffic-research-archive-v1', source_commit=commit,
                            created_utc=datetime.now(timezone.utc).isoformat(),
                            result_roots=RESULT_ROOTS, files=inventory)
            archive.writestr('archive_manifest.json', json.dumps(manifest, indent=2)+'\n')
        # Verify the ZIP bytes and that the inputs did not change during creation.
        result = verify_archive(output)
        current_paths = sorted(p for root in roots for p in root.rglob('*') if p.is_file())
        if current_paths != paths or any(file_digest(p) != inventory[p.relative_to(repository).as_posix()]['sha256'] for p in paths):
            raise ValueError('research files changed while the archive was created')
    with output.with_suffix('.sha256.json').open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    return result
