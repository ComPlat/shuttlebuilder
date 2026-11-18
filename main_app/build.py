"""Build helpers for ShuttleInstance.build() (M1).

The orchestrator owns the public interface below (`BuildError`); the build
pipeline worker fills in the rest of this module.
"""


class BuildError(Exception):
    """A Shuttle build failed.

    - `public_message`: neutral, translated text that may be shown to any user.
    - `detail`: short, **redacted** technical detail (e.g. the first compiler
      lines, or the name of the file that failed). May be shown to staff only.
      Never contains passwords, tokens or rendered sources.
    - `reference`: short id that is also written to the server log, so a user
      can quote it to an administrator.
    """

    def __init__(self, public_message, detail="", reference=""):
        super().__init__(public_message)
        self.public_message = str(public_message)
        self.detail = detail
        self.reference = reference


# ---------------------------------------------------------------------------
# Helpers (WP 1.1 - 1.5)
# ---------------------------------------------------------------------------
import fcntl
import logging
import os
import shutil
import subprocess
import tempfile
import uuid
from contextlib import contextmanager

from django.conf import settings
from django.template import Context, Engine
from django.utils.translation import gettext as _

logger = logging.getLogger("main_app.build")

_GO_ESCAPES = {"\\": "\\\\", '"': '\\"', "\n": "\\n", "\r": "\\r", "\t": "\\t"}
_MAX_LOG_CHARS = 8000
_DETAIL_LINES = 20


def go_str(value):
    """Return `value` escaped for the inside of a double-quoted Go string literal.

    The result is also valid inside a JSON string, so
    `json.loads('"' + go_str(v) + '"') == str(v)`.
    """
    if value is None:
        return ""
    out = []
    for ch in str(value):
        if ch in _GO_ESCAPES:
            out.append(_GO_ESCAPES[ch])
        elif ord(ch) < 0x20 or ord(ch) == 0x7F:
            out.append("\\u%04x" % ord(ch))
        else:
            out.append(ch)
    return "".join(out)


def redact(text, secrets):
    """Replace every non-empty secret (raw and Go-escaped form) in `text` with `***`."""
    text = "" if text is None else str(text)
    variants = set()
    for secret in secrets:
        if secret:
            variants.add(str(secret))
            variants.add(go_str(secret))
    # longest first, so that a secret containing a shorter one is replaced as a whole
    for variant in sorted((v for v in variants if v), key=len, reverse=True):
        text = text.replace(variant, "***")
    return text


@contextmanager
def file_lock(path, shared=False):
    """Hold an `fcntl.flock` on `path` (created if missing) for the duration of the block."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_SH if shared else fcntl.LOCK_EX)
        yield
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def new_reference():
    return uuid.uuid4().hex[:8]


def build_timeout():
    return getattr(settings, "SHUTTLE_BUILD_TIMEOUT", 600)


def get_secrets(instance):
    return [instance.password, instance.passwort_bagit, instance.user, instance.user_bagit]


def render_go_tree(src_dir, context, secrets=()):
    """Render all `*.go` files (not `*_test.go`) below `src_dir` in place; leave everything else untouched."""
    engine = Engine(autoescape=False)
    for root, dirs, files in os.walk(src_dir):
        for name in files:
            if not name.endswith(".go") or name.endswith("_test.go"):
                continue
            path = os.path.join(root, name)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
                rendered = engine.from_string(text).render(context)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(rendered)
            except Exception as e:
                rel = os.path.relpath(path, src_dir)
                raise BuildError(_("Building the Shuttle failed."),
                                 detail="Template rendering failed in %s: %s" % (rel, type(e).__name__),
                                 reference=new_reference())


def make_context(values):
    return Context(values, autoescape=False)


def run_step(cmd, step, instance, env, cwd):
    """Run one build command; on failure log (redacted) and raise `BuildError`."""
    secrets = get_secrets(instance)
    rc = None
    output = ""
    failed = False
    try:
        p = subprocess.run(cmd, env=env, cwd=cwd, capture_output=True, text=True, timeout=build_timeout())
        rc = p.returncode
        output = (p.stdout or "") + (p.stderr or "")
        failed = rc != 0
    except subprocess.TimeoutExpired as e:
        failed = True
        rc = "timeout"
        for part in (e.stdout, e.stderr):
            if isinstance(part, bytes):
                part = part.decode("utf-8", "replace")
            output += part or ""
    except OSError as e:
        failed = True
        rc = "oserror"
        output = "%s: %s" % (type(e).__name__, cmd[0])  # tool path is not secret
    if not failed:
        return
    reference = new_reference()
    output = redact(output, secrets)
    logger.error("Shuttle build failed: instance=%s arch=%s step=%s rc=%s ref=%s output:\n%s",
                 redact(instance.name, secrets), instance.architecture, step, rc, reference,
                 output[:_MAX_LOG_CHARS])
    detail = "\n".join(output.splitlines()[:_DETAIL_LINES])
    raise BuildError(_("Building the Shuttle failed."), detail=detail, reference=reference)


def xp_goroot():
    return getattr(settings, "XP_GOROOT", None) or "/usr/local/go1.10.8"


def go_env(architecture):
    env = os.environ.copy()
    env["GOPATH"] = settings.GOPATH
    env["GOOS"] = "windows" if architecture.startswith("win") else "linux"
    if architecture == "win_i386":
        # Go 1.10.8 in GOPATH mode: no modules, no toolchain switching.
        env["GOROOT"] = xp_goroot()
        env.pop("GO111MODULE", None)
        env.pop("GOTOOLCHAIN", None)
    else:
        env["GOROOT"] = settings.GOROOT
        env["GOTOOLCHAIN"] = "local"
    if architecture == "raspberry_pi_6":
        env["GOARCH"] = "arm"
        env["GOARM"] = "6"
    elif architecture == "raspberry_pi_7":
        env["GOARCH"] = "arm"
        env["GOARM"] = "7"
    elif architecture == "raspberry_pi_64":
        env["GOARCH"] = "arm64"
    elif architecture == "win_i386":
        env["GOARCH"] = "386"
    return env


def compile_into_temp(instance, repo_path, builds_dir, filename, config):
    """Copy, render and compile the Shuttle in a temporary folder; return the path of the binary.

    The caller must remove the returned folder's parent (`tmp_root`); it is returned as second value.
    """
    tmp_root = tempfile.mkdtemp(prefix=".%s.tmp-" % instance.name, dir=builds_dir)
    try:
        tmp_src = os.path.join(tmp_root, "src")
        tmp_bin = os.path.join(tmp_root, "bin")
        shutil.copytree(repo_path, tmp_src)
        os.makedirs(tmp_bin, exist_ok=True)
        render_go_tree(tmp_src, config, get_secrets(instance))
        env = go_env(instance.architecture)
        if instance.architecture == "win_i386":
            go_tool = os.path.join(xp_goroot(), "bin", "go")
            build_cmd = [go_tool, "build", "-o", None]
        else:
            go_tool = os.path.join(settings.GOROOT, "bin/go")
            run_step([go_tool, "mod", "download"], "go mod download", instance, env, tmp_src)
            build_cmd = [go_tool, "build", "-buildvcs=false", "-o", None]
        out = os.path.join(tmp_bin, filename)
        build_cmd[-1] = out
        run_step(build_cmd, "go build", instance, env, tmp_src)
        return out, tmp_root
    except BaseException:
        shutil.rmtree(tmp_root, ignore_errors=True)
        raise
