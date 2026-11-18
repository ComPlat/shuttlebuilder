"""Form rules of ShuttleInstanceForm that test_options.py does not cover (converter, duration, flat_tar, name)."""
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from main_app.forms import GitInstanceForm, ShuttleInstanceForm
from main_app.models import ShuttleInstance

ARCHITECTURES = ('win_i386', 'win_64', 'ubuntu_64', 'raspberry_pi_6', 'raspberry_pi_7', 'raspberry_pi_64')
CONVERTER_FIELDS = ('dst_bagit', 'user_bagit', 'passwort_bagit', 'public_link', 'profile')


def data(**kw):
    d = dict(name='n1', transfer='webdav', user='u', password='pw', src='/s', dst='https://x.example/a',
             shuttle_type='file', common_name_parts='^a', duration=300, architecture='ubuntu_64')
    d.update(kw)
    return d


def converter_data(**kw):
    d = data(with_converter='on', dst_bagit='https://y.example/b', user_bagit='u', passwort_bagit='p',
             public_link='https://p.example/')
    d.update(kw)
    return d


def profile_files():
    return {'profile': SimpleUploadedFile('p.json', b'{}')}


class ConverterFormTest(TestCase):
    def test_converter_only_on_win64_and_ubuntu64(self):
        for arch in ARCHITECTURES:
            with self.subTest(arch=arch):
                f = ShuttleInstanceForm(converter_data(architecture=arch), profile_files())
                if arch in ('win_64', 'ubuntu_64'):
                    self.assertTrue(f.is_valid(), f.errors)
                else:
                    self.assertIn('with_converter', f.errors)

    def test_converter_fields_are_required(self):
        for field in CONVERTER_FIELDS:
            with self.subTest(missing=field):
                d = converter_data()
                files = profile_files()
                if field == 'profile':
                    files = {}
                else:
                    d[field] = ''
                f = ShuttleInstanceForm(d, files)
                self.assertIn(field, f.errors)
                self.assertEqual(set(f.errors) & set(CONVERTER_FIELDS), {field})

    def test_converter_fields_not_required_without_converter(self):
        f = ShuttleInstanceForm(data(), {})
        self.assertTrue(f.is_valid(), f.errors)

    def test_public_link_gets_trailing_slash(self):
        f = ShuttleInstanceForm(converter_data(public_link='https://p.example'), profile_files())
        self.assertTrue(f.is_valid(), f.errors)
        self.assertEqual(f.cleaned_data['public_link'], 'https://p.example/')


class DurationFormTest(TestCase):
    def test_zero_is_an_error_and_one_is_ok(self):
        self.assertIn('duration', ShuttleInstanceForm(data(duration=0), {}).errors)
        self.assertNotIn('duration', ShuttleInstanceForm(data(duration=1), {}).errors)
        f = ShuttleInstanceForm(data(duration=1), {})
        self.assertTrue(f.is_valid(), f.errors)

    def test_negative_is_an_error(self):
        self.assertIn('duration', ShuttleInstanceForm(data(duration=-5), {}).errors)


class FlatTarFormTest(TestCase):
    def test_flat_tar_needs_common_name_parts(self):
        for value in ('', None):
            with self.subTest(value=value):
                f = ShuttleInstanceForm(data(shuttle_type='flat_tar', common_name_parts=value or ''), {})
                self.assertIn('common_name_parts', f.errors)

    def test_flat_tar_needs_compilable_regex(self):
        f = ShuttleInstanceForm(data(shuttle_type='flat_tar', common_name_parts='(unclosed'), {})
        self.assertIn('common_name_parts', f.errors)

    def test_flat_tar_with_valid_regex_is_ok(self):
        f = ShuttleInstanceForm(data(shuttle_type='flat_tar', common_name_parts=r'^<a>\d+'), {})
        self.assertTrue(f.is_valid(), f.errors)

    def test_other_types_ignore_the_regex(self):
        f = ShuttleInstanceForm(data(shuttle_type='file', common_name_parts='(unclosed'), {})
        self.assertNotIn('common_name_parts', f.errors)


class NameReadOnlyTest(TestCase):
    def test_existing_instance_keeps_its_name(self):
        inst = ShuttleInstance(pk=7, name='original', user='u', password='pw', transfer='webdav', src='/s',
                               dst='https://x.example/a', shuttle_type='file', architecture='ubuntu_64')
        f = ShuttleInstanceForm(data(name='renamed'), {}, instance=inst)
        self.assertTrue(f.fields['name'].widget.attrs.get('readonly'))
        self.assertTrue(f.is_valid(), f.errors)
        self.assertEqual(f.cleaned_data['name'], 'original')

    def test_new_instance_takes_the_given_name(self):
        f = ShuttleInstanceForm(data(name='fresh'), {})
        self.assertNotIn('readonly', f.fields['name'].widget.attrs)
        self.assertTrue(f.is_valid(), f.errors)
        self.assertEqual(f.cleaned_data['name'], 'fresh')

    def test_git_instance_keeps_its_name(self):
        from main_app.models import GitInstance
        git = GitInstance(pk=3, name='g', url='https://example.invalid/x.git', branch='main')
        f = GitInstanceForm({'name': 'other', 'url': git.url, 'branch': 'main'}, instance=git)
        self.assertTrue(f.is_valid(), f.errors)
        self.assertEqual(f.cleaned_data['name'], 'g')
