"""Convert stored values from the old "pre-escaped for Go" form to raw values.

Until now the model stored text such as ``C:\\Data`` (two backslashes) because
the build placed it unescaped into a Go string literal. From now on the build
escapes values itself (``go_str``), so the database must hold the raw value.

The conversion is ``go_decode(old_render(value))``: render the value the way the
old build did, then read the result as the body of a Go interpreted string
literal. Values that were never a valid literal (they never compiled) stay as
they are. Only counts are logged, never values.
"""
import logging
import re

from django.db import migrations, transaction

logger = logging.getLogger("main_app.build")

FIELDS = ("src", "dst", "user", "password", "name", "dst_bagit", "user_bagit", "passwort_bagit")

_SIMPLE = {"a": 0x07, "b": 0x08, "f": 0x0C, "n": 0x0A, "r": 0x0D, "t": 0x09, "v": 0x0B,
           "\\": 0x5C, '"': 0x22}
_HEX = "0123456789abcdefABCDEF"


def old_render(s):
    """Copy of the former ``ShuttleInstance.replace_single_backslashes``."""
    return re.sub(r'(?<!\\)\\(?!\\)', r'\\\\', s or "")


def go_decode(s):
    """Interpret ``s`` as the body of a Go interpreted string literal.

    Returns the decoded string, or ``None`` if ``s`` is not a valid literal body.
    """
    out = bytearray()
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c == '"' or c == "\n":
            return None
        if c != "\\":
            out += c.encode("utf-8", "surrogatepass")
            i += 1
            continue
        i += 1
        if i >= n:
            return None
        e = s[i]
        if e in _SIMPLE:
            out.append(_SIMPLE[e])
            i += 1
        elif e == "x":
            h = s[i + 1:i + 3]
            if len(h) != 2 or any(ch not in _HEX for ch in h):
                return None
            out.append(int(h, 16))
            i += 3
        elif e in "01234567":
            o = s[i:i + 3]
            if len(o) != 3 or any(ch not in "01234567" for ch in o) or int(o, 8) > 255:
                return None
            out.append(int(o, 8))
            i += 3
        elif e in "uU":
            width = 4 if e == "u" else 8
            h = s[i + 1:i + 1 + width]
            if len(h) != width or any(ch not in _HEX for ch in h):
                return None
            cp = int(h, 16)
            if cp > 0x10FFFF or 0xD800 <= cp <= 0xDFFF:
                return None
            out += chr(cp).encode("utf-8")
            i += 1 + width
        else:
            return None
    try:
        return out.decode("utf-8")
    except UnicodeDecodeError:
        return None


def convert_value(value):
    """New stored value for an old one (unchanged if it was never a valid literal)."""
    if value is None:
        return None
    decoded = go_decode(old_render(value))
    return value if decoded is None else decoded


def forward(apps, schema_editor):
    Instance = apps.get_model("main_app", "ShuttleInstance")
    db = schema_editor.connection.alias
    rows = list(Instance.objects.using(db).order_by("pk"))
    names = {r.name for r in rows}
    checked = changed = invalid = 0
    with transaction.atomic(using=db):
        for row in rows:
            checked += 1
            updates = {}
            for field in FIELDS:
                old = getattr(row, field)
                if old is None:
                    continue
                new = convert_value(old)
                if new == old:
                    if go_decode(old_render(old)) is None:
                        invalid += 1
                    continue
                if field == "name":
                    if new in names:
                        continue  # unique: keep the old name
                    names.discard(old)
                    names.add(new)
                updates[field] = new
            if updates:
                updates["last_build"] = None
                Instance.objects.using(db).filter(pk=row.pk).update(**updates)
                changed += 1
    logger.info("Migration 0018: %d instances checked, %d changed, %d field values kept (not a valid Go literal)",
                checked, changed, invalid)


def reverse(apps, schema_editor):
    Instance = apps.get_model("main_app", "ShuttleInstance")
    db = schema_editor.connection.alias
    changed = 0
    with transaction.atomic(using=db):
        rows = list(Instance.objects.using(db).order_by("pk"))
        names = {r.name for r in rows}
        for row in rows:
            updates = {}
            for field in FIELDS:
                old = getattr(row, field)
                if old and "\\" in old:
                    new = old.replace("\\", "\\\\")
                    if field == "name":
                        # unique and max_length 50: keep the old name if it would collide or not fit
                        if new in names or len(new) > 50:
                            continue
                        names.discard(old)
                        names.add(new)
                    updates[field] = new
            if updates:
                updates["last_build"] = None
                Instance.objects.using(db).filter(pk=row.pk).update(**updates)
                changed += 1
    logger.info("Migration 0018 (reverse): %d instances changed", changed)


class Migration(migrations.Migration):

    dependencies = [
        ("main_app", "0017_shuttleinstance_public_link"),
    ]

    operations = [
        migrations.RunPython(forward, reverse),
    ]
