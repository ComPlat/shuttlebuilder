from django.test import TestCase

from main_app.forms import ShuttleInstanceForm

SHA = 'SHA256:' + 'A' * 43


class LinuxUserFormTest(TestCase):
    def form(self, **kw):
        d = dict(name='n1', transfer='sftp', user='u', password='pw', src='/s', dst='host/path',
                 shuttle_type='file', common_name_parts='^a', duration=300, architecture='ubuntu_64',
                 host_key=SHA)
        d.update(kw)
        return ShuttleInstanceForm(d, {})

    def test_valid(self):
        for v in ['', 'lab', '_svc', 'a-b_c1', 'a' * 32, ' lab ']:
            f = self.form(linux_user=v)
            self.assertTrue(f.is_valid(), (v, f.errors))
            self.assertEqual(f.cleaned_data['linux_user'], v.strip())

    def test_invalid(self):
        for v in ['Lab', '1lab', 'a b', 'a' * 33, 'a\nUser=root', 'a;b', '-x', 'ä']:
            self.assertIn('linux_user', self.form(linux_user=v).errors, v)

    def test_cleared_for_windows(self):
        for arch in ('win_64', 'win_i386'):
            f = self.form(linux_user='lab', architecture=arch, transfer='webdav', dst='https://x.example/a')
            self.assertTrue(f.is_valid(), f.errors)
            self.assertEqual(f.cleaned_data['linux_user'], '')

    def test_windows_invalid_value_is_cleared_not_an_error(self):
        # design §1.4: linux_user doesn't apply to Windows, so it is cleared, never an error
        f = self.form(linux_user='Bad Name', architecture='win_64', transfer='webdav', dst='https://x.example/a')
        self.assertTrue(f.is_valid(), f.errors)
        self.assertEqual(f.cleaned_data['linux_user'], '')
