import importlib

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import SimpleTestCase, TransactionTestCase
from django.utils import timezone

mig = importlib.import_module("main_app.migrations.0018_go_literal_values")


class ConvertValueTest(SimpleTestCase):
    def test_design_examples(self):
        cases = [
            (r"C:\\Data", r"C:\Data"),
            (r"C:\Data", r"C:\Data"),
            (r"\\\\server\\share", r"\\server\share"),
            ('a"b', 'a"b'),
            ("p&a<s>", "p&a<s>"),
            ("", ""),
        ]
        for old, new in cases:
            with self.subTest(old=old):
                self.assertEqual(mig.convert_value(old), new)

    def test_none(self):
        self.assertIsNone(mig.convert_value(None))

    def test_single_backslash_before_letter_is_literal_backslash(self):
        # old build doubled the lone backslash, so \n was a backslash + n
        self.assertEqual(mig.convert_value(r"C:\new\table"), r"C:\new\table")

    def test_escaped_double_stays_single(self):
        self.assertEqual(mig.convert_value(r"D:\\new"), r"D:\new")

    def test_go_decode_escapes(self):
        d = mig.go_decode
        self.assertEqual(d(r"a\tb\nc"), "a\tb\nc")
        self.assertEqual(d(r"\x41\101\u00e4\U0001F600"), "AA\u00e4\U0001F600")
        self.assertEqual(d(r"\a\b\f\r\v\\\""), "\a\b\f\r\v\\\"")
        self.assertEqual(d("\u00e4"), "\u00e4")
        self.assertEqual(d(r"\xc3\xa4"), "\u00e4")  # bytes form valid UTF-8

    def test_go_decode_invalid(self):
        d = mig.go_decode
        for bad in ['a"b', "a\nb", "abc\\", r"\q", r"\x4", r"\xZZ", r"\12", r"\400",
                    r"\u12", r"\uD800", r"\U00110000", r"\xff"]:
            with self.subTest(bad=bad):
                self.assertIsNone(d(bad))

    def test_invalid_kept_unchanged(self):
        # contains an unescaped quote after old_render -> never compiled
        self.assertEqual(mig.convert_value(r'C:\x"y'), r'C:\x"y')


class MigrationTest(TransactionTestCase):
    migrate_from = [("main_app", "0017_shuttleinstance_public_link")]
    migrate_to = [("main_app", "0018_go_literal_values")]

    def _migrate(self, target):
        executor = MigrationExecutor(connection)
        executor.migrate(target)
        return executor.loader.project_state(target).apps

    def tearDown(self):
        MigrationExecutor(connection).migrate(MigrationExecutor(connection).loader.graph.leaf_nodes())

    def _make(self, apps, owner, **kw):
        Instance = apps.get_model("main_app", "ShuttleInstance")
        base = dict(user="u", password="pw", transfer="webdav", src="s", dst="d", shuttle_type="file",
                    owner_id=owner, last_build=timezone.now(), duration=300, architecture="ubuntu_64")
        base.update(kw)
        return Instance.objects.create(**base)

    def test_forward_and_reverse(self):
        old_apps = self._migrate(self.migrate_from)
        owner = None  # owner is nullable; avoids the swapped user model
        a = self._make(old_apps, owner, name="a", src=r"C:\\Data", dst=r"\\\\server\\share",
                       password="p&a<s>", user_bagit=None, common_name_parts=r"^\\d+")
        b = self._make(old_apps, owner, name="b", src=r"C:\Data")
        bad = self._make(old_apps, owner, name="bad", password='a"b')
        keep = self._make(old_apps, owner, name="keep", src="/plain")
        # name collision: decoded "x\y" already exists
        c1 = self._make(old_apps, owner, name=r"x\y")
        c2 = self._make(old_apps, owner, name=r"x\\y")

        new_apps = self._migrate(self.migrate_to)
        I = new_apps.get_model("main_app", "ShuttleInstance")
        a, b, bad, keep, c1, c2 = (I.objects.get(pk=o.pk) for o in (a, b, bad, keep, c1, c2))
        self.assertEqual(a.src, r"C:\Data")
        self.assertEqual(a.dst, r"\\server\share")
        self.assertEqual(a.password, "p&a<s>")
        self.assertIsNone(a.user_bagit)
        self.assertEqual(a.common_name_parts, r"^\\d+")  # untouched
        self.assertIsNone(a.last_build)
        self.assertEqual(b.src, r"C:\Data")
        self.assertIsNotNone(b.last_build)  # value unchanged -> no rebuild forced
        self.assertEqual(bad.password, 'a"b')
        self.assertIsNotNone(bad.last_build)
        self.assertEqual(keep.src, "/plain")
        self.assertIsNotNone(keep.last_build)
        self.assertEqual(c1.name, r"x\y")
        self.assertEqual(c2.name, r"x\\y")  # collision: old name kept

        old_apps = self._migrate(self.migrate_from)
        I = old_apps.get_model("main_app", "ShuttleInstance")
        a = I.objects.get(pk=a.pk)
        self.assertEqual(a.src, r"C:\\Data")
        self.assertEqual(a.dst, r"\\\\server\\share")
        self.assertIsNone(a.last_build)
