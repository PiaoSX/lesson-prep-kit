"""Black-box installer checks; never writes to a real agent's skill directory."""

from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


PROJECT = Path(__file__).resolve().parents[1]
SKILLS = ('high-school-lesson-prep', 'chinese-material-search')


def files_under(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


class InstallerContract(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='lesson-install-test-')
        self.base = Path(self.temporary.name).resolve()
        self.target = self.base / '课程 skills'
        self.environment = dict(os.environ, CODEX_HOME=str(self.base / 'codex-home'),
                                PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')

    def tearDown(self):
        self.temporary.cleanup()

    def command(self, route, project=PROJECT):
        return [sys.executable, str(project / 'install.py')]

    def run_installer(self, route, *arguments, project=PROJECT, success=True):
        result = subprocess.run(self.command(route, project) + list(map(str, arguments)),
                                cwd=self.base, env=self.environment, capture_output=True,
                                text=True, encoding='utf-8')
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def fixture(self):
        project = self.base / 'fixture'
        shutil.copytree(PROJECT / 'skills', project / 'skills')
        shutil.copyfile(PROJECT / 'install.py', project / 'install.py')
        return project

    def each_route(self):
        return ('python',)

    def test_dry_run_has_no_filesystem_side_effects(self):
        for route in self.each_route():
            with self.subTest(route=route):
                before = files_under(self.base)
                result = self.run_installer(route, '--target', self.target, '--dry-run')
                self.assertFalse(self.target.exists())
                self.assertEqual(files_under(self.base), before)
                self.assertEqual({x['status'] for x in result['skills']}, {'would-install'})

    def test_installs_complete_bundle_and_preserves_existing_edits(self):
        for route in self.each_route():
            with self.subTest(route=route):
                target = self.target / route
                result = self.run_installer(route, '--target', target)
                self.assertEqual({x['status'] for x in result['skills']}, {'installed'})
                for name in SKILLS:
                    destination = target / name
                    self.assertFalse(destination.is_symlink())
                    self.assertEqual(files_under(destination), files_under(PROJECT / 'skills' / name))
                edited = target / SKILLS[0] / 'SKILL.md'
                edited.write_text('User changes must survive.', encoding='utf-8')
                before = files_under(target)
                again = self.run_installer(route, '--target', target)
                self.assertEqual({x['status'] for x in again['skills']}, {'skipped-existing'})
                self.assertEqual(before, files_under(target))
                self.assertFalse((target / '.lesson-prep-install.lock').exists())

    def test_respects_codex_home_without_explicit_target(self):
        for route in self.each_route():
            with self.subTest(route=route):
                result = self.run_installer(route, '--dry-run')
                expected = Path(self.environment['CODEX_HOME']) / 'skills'
                self.assertEqual(Path(result['target']), expected)
                self.assertFalse(expected.exists())

    def test_refuses_to_install_over_its_own_source(self):
        for route in self.each_route():
            with self.subTest(route=route):
                before = files_under(PROJECT / 'skills')
                self.run_installer(route, '--target', PROJECT / 'skills', success=False)
                self.assertEqual(before, files_under(PROJECT / 'skills'))

    def test_existing_file_is_not_overwritten_or_partially_installed(self):
        for route in self.each_route():
            with self.subTest(route=route):
                target = self.target / route
                target.mkdir(parents=True)
                collision = target / SKILLS[1]
                collision.write_text('User file.', encoding='utf-8')
                before = files_under(target)
                self.run_installer(route, '--target', target, success=False)
                self.assertEqual(before, files_under(target))
                self.assertFalse((target / SKILLS[0]).exists())

    def test_incomplete_bundle_fails_before_creating_target(self):
        for route in self.each_route():
            with self.subTest(route=route):
                project = self.fixture()
                resource = project / 'skills/high-school-lesson-prep/references/method-library/methods.json'
                resource.unlink()
                self.run_installer(route, '--target', self.target, project=project, success=False)
                self.assertFalse(self.target.exists())
                shutil.rmtree(project)

    def test_existing_lock_is_preserved(self):
        for route in self.each_route():
            with self.subTest(route=route):
                target = self.target / route
                lock = target / '.lesson-prep-install.lock'
                lock.mkdir(parents=True)
                self.run_installer(route, '--target', target, success=False)
                self.assertTrue(lock.is_dir())
                self.assertFalse((target / SKILLS[0]).exists())

    def test_source_links_are_rejected(self):
        for route in self.each_route():
            with self.subTest(route=route):
                project = self.fixture()
                outside = self.base / 'private.txt'
                outside.write_text('Not a skill resource.', encoding='utf-8')
                link = project / 'skills' / SKILLS[0] / 'outside.txt'
                try:
                    link.symlink_to(outside)
                except OSError:
                    shutil.rmtree(project)
                    self.skipTest('This Windows account cannot create symbolic links')
                self.run_installer(route, '--target', self.target, project=project, success=False)
                self.assertFalse(self.target.exists())
                shutil.rmtree(project)


if __name__ == '__main__':
    unittest.main()
