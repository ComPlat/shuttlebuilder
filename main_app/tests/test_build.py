import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
from datetime import timedelta
from types import SimpleNamespace
from unittest import mock

from django.utils import timezone
from django.test import SimpleTestCase, override_settings

from main_app.build import BuildError, go_env, go_str, redact, render_go_tree
from main_app.models import ShuttleInstance

NASTY_PW = 'p&a<s>s\'"\\'
KEYS = ["src", "name", "dst", "user", "password", "duration", "crt", "type", "common_regex", "tType",
        "dst_converter", "user_converter", "password_converter", "preconvert", "public", "hostkey", "insecure"]

GO_FIXTURE = 'package main\n\nimport "os"\n\nfunc main() {\n\tvals := []string{\n' + "".join(
    '\t\t"{{ %s }}",\n' % k for k in KEYS) + '\t}\n\tfor _, v := range vals {\n\t\tos.Stdout.WriteString(v + "\\x00")\n\t}\n}\n'


def make_instance(**kw):
    values = dict(name="inst1", user="us&er", password=NASTY_PW, transfer="webdav", src="C:\\Data & Results",
                  dst="https://x.example/a?b=1&c=<2>", shuttle_type="flat_tar", common_name_parts="^<a>\\d+",
                  duration=300, architecture="ubuntu_64", with_converter=True, user_bagit="u\tb", dst_bagit="d\\\\e",
                  passwort_bagit="pb\"\n", public_link="https://p.example/", last_update=timezone.now() - timedelta(hours=1))
    values.update(kw)
    return ShuttleInstance(**values)


def expected(inst):
    return {"src": inst.src, "name": inst.name, "dst": inst.dst, "user": inst.user, "password": inst.password,
            "duration": str(inst.duration), "crt": "", "type": inst.shuttle_type,
            "common_regex": inst.common_name_parts, "tType": inst.transfer, "dst_converter": inst.dst_bagit,
            "user_converter": inst.user_bagit, "password_converter": inst.passwort_bagit, "preconvert": "T",
            "public": inst.public_link, "hostkey": "", "insecure": ""}


class GoStrTest(SimpleTestCase):
    def test_round_trip(self):
        for v in ['&<>\'"\\', "a\nb\rc\td", "\x00\x01\x1f\x7f", "äöü€😀", "", "C:\\Data\\\\x", 42]:
            self.assertEqual(json.loads('"' + go_str(v) + '"'), str(v))

    def test_none(self):
        self.assertEqual(go_str(None), "")

    def test_redact(self):
        text = "pw=%s esc=%s other" % (NASTY_PW, go_str(NASTY_PW))
        out = redact(text, [NASTY_PW, "", None])
        self.assertNotIn("p&a", out)
        self.assertEqual(out.count("***"), 2)


class RenderTest(SimpleTestCase):
    def test_render_values_round_trip(self):
        inst = make_instance()
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "main.go"), "w", encoding="utf-8") as f:
                f.write(GO_FIXTURE)
            render_go_tree(d, inst._get_build_config())
            with open(os.path.join(d, "main.go"), encoding="utf-8") as f:
                lines = [l.strip() for l in f.read().splitlines() if l.strip().startswith('"')]
        exp = expected(inst)
        self.assertEqual(len(lines), 17)
        for key, line in zip(KEYS, lines):
            self.assertEqual(json.loads(line.rstrip(",")), exp[key], key)

    def test_go_run(self):
        if not shutil.which("go"):
            self.skipTest("go not on PATH")
        inst = make_instance()
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "main.go"), "w", encoding="utf-8") as f:
                f.write(GO_FIXTURE)
            with open(os.path.join(d, "go.mod"), "w") as f:
                f.write("module x\n\ngo 1.20\n")
            render_go_tree(d, inst._get_build_config())
            env = dict(os.environ, GOFLAGS="-mod=mod", GOCACHE=os.path.join(d, ".cache"),
                       GOPATH=os.path.join(d, ".gopath"))
            p = subprocess.run(["go", "run", "."], cwd=d, env=env, capture_output=True, text=True, timeout=300)
            self.assertEqual(p.returncode, 0, p.stderr[:500])
        exp = expected(inst)
        self.assertEqual(p.stdout.split("\x00")[:-1], [exp[k] for k in KEYS])

    def test_only_go_files_rendered(self):
        inst = make_instance()
        binary = bytes(range(256)) + b"{{ x }}"
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "sub"))
            files = {"README.md": b"{% broken {{ ", "sub/data.bin": binary, "a_test.go": b"x := \"{{ x }}\" {% if %}",
                     "sub/b.go": b'v := "{{ password }}"'}
            for name, content in files.items():
                with open(os.path.join(d, name), "wb") as f:
                    f.write(content)
            render_go_tree(d, inst._get_build_config())
            for name in ("README.md", "sub/data.bin", "a_test.go"):
                with open(os.path.join(d, name), "rb") as f:
                    self.assertEqual(f.read(), files[name], name)
            with open(os.path.join(d, "sub/b.go"), encoding="utf-8") as f:
                self.assertEqual(f.read(), 'v := "%s"' % go_str(NASTY_PW))

    def test_render_failure_has_no_contents(self):
        inst = make_instance()
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "bad.go"), "w") as f:
                f.write("SECRETCONTENT {% if %}")
            with self.assertRaises(BuildError) as cm:
                render_go_tree(d, inst._get_build_config())
        self.assertIn("bad.go", cm.exception.detail)
        self.assertNotIn("SECRETCONTENT", cm.exception.detail)
        self.assertTrue(cm.exception.reference)


@override_settings(GOROOT="/opt/go-new", XP_GOROOT="/opt/go-xp", GOPATH="/opt/gopath")
class GoEnvTest(SimpleTestCase):
    CASES = {
        "ubuntu_64": ("linux", None, None),
        "raspberry_pi_6": ("linux", "arm", "6"),
        "raspberry_pi_7": ("linux", "arm", "7"),
        "raspberry_pi_64": ("linux", "arm64", None),
        "win_i386": ("windows", "386", None),
        "win_64": ("windows", None, None),
    }

    def test_all_architectures(self):
        from main_app.models import ShuttleInstance
        known = {c[0] for c in ShuttleInstance._meta.get_field("architecture").choices}
        self.assertEqual(known, set(self.CASES))
        with mock.patch.dict(os.environ, {"GO111MODULE": "on", "GOARCH": "", "GOARM": ""}):
            for arch, (goos, goarch, goarm) in self.CASES.items():
                env = go_env(arch)
                self.assertEqual(env["GOOS"], goos, arch)
                if goarch:
                    self.assertEqual(env["GOARCH"], goarch, arch)
                if goarm:
                    self.assertEqual(env["GOARM"], goarm, arch)
                self.assertEqual(env["GOPATH"], "/opt/gopath")
                if arch == "win_i386":
                    self.assertEqual(env["GOROOT"], "/opt/go-xp")
                    self.assertNotIn("GO111MODULE", env)
                else:
                    self.assertEqual(env["GOROOT"], "/opt/go-new", arch)
                    self.assertEqual(env["GOTOOLCHAIN"], "local", arch)


@override_settings(GOROOT="/nonexistent-goroot", GOPATH="/nonexistent-gopath")
class BuildTest(SimpleTestCase):
    def setUp(self):
        self.old_cwd = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(os.chdir, self.old_cwd)
        os.chdir(self.tmp.name)
        self.repo = os.path.join(self.tmp.name, "repo")
        os.makedirs(self.repo)
        with open(os.path.join(self.repo, "main.go"), "w") as f:
            f.write('package main\nvar p = "{{ password }}"\n')
        self.git = SimpleNamespace(last_reload=None, get_path=lambda: ("x", self.repo),
                                   git_reload=mock.Mock())
        self.git.last_reload = timezone.now() - timedelta(minutes=5)
        patcher = mock.patch("main_app.models.GitInstance.objects.get", return_value=self.git)
        patcher.start()
        self.addCleanup(patcher.stop)

    def builds(self):
        return os.path.join(self.tmp.name, "projects", "builds")

    def test_failure_redacted_and_cleaned(self):
        inst = make_instance(with_converter=False)
        target = os.path.join(inst.get_path(), "bin", "shuttle")
        os.makedirs(os.path.dirname(target))
        with open(target, "w") as f:
            f.write("old")
        fail = subprocess.CompletedProcess([], 1, stdout="oops %s" % NASTY_PW, stderr="bad %s" % go_str(NASTY_PW))
        with mock.patch("main_app.build.subprocess.run", return_value=fail):
            with self.assertLogs("main_app.build", "ERROR") as logs:
                with self.assertRaises(BuildError) as cm:
                    inst.build()
        err = cm.exception
        self.assertIn("***", err.detail)
        self.assertNotIn("p&a", err.detail)
        self.assertNotIn("p&a", "\n".join(logs.output))
        self.assertIn(err.reference, "\n".join(logs.output))
        self.assertEqual([n for n in os.listdir(self.builds()) if n.startswith(".") and ".tmp-" in n], [])
        with open(target) as f:
            self.assertEqual(f.read(), "old")

    def _run_commands(self, arch):
        inst = make_instance(architecture=arch)
        calls = []

        def fake(cmd, **kw):
            calls.append((list(cmd), kw["env"]))
            if cmd[1] == "build":
                with open(cmd[-1], "w") as f:
                    f.write("bin")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        with mock.patch("main_app.build.subprocess.run", side_effect=fake):
            inst.build()
        return calls

    @override_settings(GOROOT="/opt/go-new", XP_GOROOT="/opt/go-xp")
    def test_commands_modern(self):
        calls = self._run_commands("ubuntu_64")
        self.assertEqual([c[0][:3] for c in calls], [["/opt/go-new/bin/go", "mod", "download"],
                                                      ["/opt/go-new/bin/go", "build", "-buildvcs=false"]])
        self.assertEqual(calls[1][0][3], "-o")

    @override_settings(GOROOT="/opt/go-new", XP_GOROOT="/opt/go-xp")
    def test_commands_xp(self):
        calls = self._run_commands("win_i386")
        self.assertEqual(len(calls), 1)
        cmd, env = calls[0]
        self.assertEqual(cmd[:3], ["/opt/go-xp/bin/go", "build", "-o"])
        self.assertNotIn("-buildvcs=false", cmd)
        self.assertEqual(env["GOROOT"], "/opt/go-xp")

    @override_settings(GOROOT="/opt/go-new", XP_GOROOT="/nonexistent/go-xp")
    def test_missing_xp_tool_names_path(self):
        inst = make_instance(architecture="win_i386")
        with mock.patch("main_app.build.subprocess.run", side_effect=FileNotFoundError(2, "No such file")):
            with self.assertLogs("main_app.build", "ERROR"):
                with self.assertRaises(BuildError) as cm:
                    inst.build()
        self.assertIn("/nonexistent/go-xp/bin/go", cm.exception.detail)
        self.assertNotIn("p&a", cm.exception.detail)

    def test_timeout_is_build_error(self):
        inst = make_instance()
        with mock.patch("main_app.build.subprocess.run", side_effect=subprocess.TimeoutExpired("go", 1)):
            with self.assertLogs("main_app.build", "ERROR"):
                with self.assertRaises(BuildError):
                    inst.build()

    def test_success_replaces_binary(self):
        inst = make_instance()

        def fake(cmd, **kw):
            if cmd[1] == "build":
                with open(kw["cwd"] and os.path.join(kw["cwd"], "main.go"), encoding="utf-8") as f:
                    rendered = f.read()
                with open(cmd[-1], "w") as f:
                    f.write(rendered)
            return subprocess.CompletedProcess(cmd, 0, "", "")

        with mock.patch("main_app.build.subprocess.run", side_effect=fake):
            path = inst.build()
        with open(path) as f:
            self.assertIn(go_str(NASTY_PW), f.read())
        self.assertEqual(sorted(os.listdir(os.path.join(self.builds(), "inst1"))), ["bin"])

    def test_concurrent_builds_run_go_once(self):
        inst = make_instance()
        calls = []

        def fake(cmd, **kw):
            if cmd[1] == "build":
                calls.append(cmd)
                time.sleep(0.5)
                with open(cmd[-1], "w") as f:
                    f.write("bin")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        errors = []

        def run():
            try:
                inst.build()
            except Exception as e:  # pragma: no cover
                errors.append(e)

        with mock.patch("main_app.build.subprocess.run", side_effect=fake):
            threads = [threading.Thread(target=run) for _ in range(2)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        self.assertEqual(errors, [])
        self.assertEqual(len(calls), 1)
