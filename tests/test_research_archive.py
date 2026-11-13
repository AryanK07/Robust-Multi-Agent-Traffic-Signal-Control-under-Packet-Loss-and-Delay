import json
import subprocess
from zipfile import ZipFile

import pytest

from traffic_control.experiments.research_archive import build_archive, verify_archive, RESULT_ROOTS


def test_archive_restores_history_and_preserves_records(tmp_path):
    repo = tmp_path / 'repo'
    repo.mkdir()
    def git(*args):
        return subprocess.run(['git', *args], cwd=repo, check=True, capture_output=True)
    git('init')
    git('config', 'user.name', 'Archive Test')
    git('config', 'user.email', 'archive-test@example.invalid')
    (repo / '.gitignore').write_text('results/\n')
    (repo / 'source.py').write_text('version = 1\n')
    git('add', '.')
    git('commit', '-m', 'test: source fixture')
    original = git('rev-parse', 'HEAD').stdout.strip()
    for name in RESULT_ROOTS:
        folder = repo / name
        folder.mkdir(parents=True)
        (folder / 'record.json').write_text('{"outcome": "unfavorable"}\n')
    archive = tmp_path / 'records.zip'
    result = build_archive(repo, archive)
    assert result['verified_files'] == 4
    assert verify_archive(archive) == result
    with pytest.raises(FileExistsError):
        build_archive(repo, archive)
    with ZipFile(archive) as saved:
        bundle = tmp_path / 'restored.bundle'
        bundle.write_bytes(saved.read('source/repository.bundle'))
        assert json.loads(saved.read(f'{RESULT_ROOTS[0]}/record.json'))['outcome'] == 'unfavorable'
    restored = tmp_path / 'restored'
    subprocess.run(['git', 'clone', str(bundle), str(restored)], check=True, capture_output=True)
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=restored).strip() == original
    assert (restored / 'source.py').read_text() == 'version = 1\n'
    # Repackage a readable ZIP with one changed record, keeping its old manifest.
    damaged = tmp_path / 'changed.zip'
    with ZipFile(archive) as source, ZipFile(damaged, 'x') as target:
        for name in source.namelist():
            target.writestr(name, b'altered' if name.endswith('record.json') else source.read(name))
    with pytest.raises(ValueError, match='content mismatch'):
        verify_archive(damaged)
