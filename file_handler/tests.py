from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from main_app.models import ShuttleInstance


class StartFilesTest(TestCase):
    def test_vbs(self):
        r = self.client.get(reverse('shuttle_task.vbs'))
        self.assertEqual(r.status_code, 200)
        body = r.content.decode()
        self.assertIn('C:\\Program Files\\Shuttle\\shuttle.exe', body)
        self.assertIn('WinScriptHost.CurrentDirectory = "C:\\Program Files\\Shuttle"', body)
        self.assertLess(body.index('CurrentDirectory'), body.index('.Run'))

    def test_generic_unit(self):
        r = self.client.get(reverse('file_shuttle.service'))
        body = r.content.decode()
        self.assertEqual(r.status_code, 200)
        self.assertIn('Description=Shuttle\n', body)
        self.assertIn('User=CHANGE_ME', body)
        self.assertIn('RestartSec=10', body)
        self.assertIn('network-online.target', body)
        self.assertIn('ExecStart=/opt/Shuttle/shuttle', body)


class InstanceUnitTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        U = get_user_model()
        cls.owner = U.objects.create_user(username='own', password='x-dummy')
        cls.other = U.objects.create_user(username='oth', password='x-dummy')
        cls.staff = U.objects.create_user(username='stf', password='x-dummy', is_staff=True)

    def make(self, name='lab1', **kw):
        kw.setdefault('architecture', 'ubuntu_64')
        return ShuttleInstance.objects.create(name=name, owner=self.owner, **kw)

    def get(self, inst, user=None):
        if user:
            self.client.force_login(user)
        return self.client.get(reverse('file_shuttle_instance.service', kwargs={'pk': inst.pk}))

    def test_with_user(self):
        r = self.get(self.make(linux_user='labuser'), self.owner)
        body = r.content.decode()
        self.assertEqual(r.status_code, 200)
        self.assertIn('Description=Shuttle (lab1)\n', body)
        self.assertIn('User=labuser\n', body)
        self.assertNotIn('CHANGE_ME', body)
        self.assertIn('shuttle.service', r['Content-Disposition'])
        self.assertIn('network-online.target', body)
        self.assertIn('RestartSec=10', body)

    def test_empty_user(self):
        body = self.get(self.make(), self.owner).content.decode()
        self.assertIn('User=CHANGE_ME\n', body)
        self.assertIn('Replace CHANGE_ME with the Linux user', body)

    def test_unvalidated_user_not_written(self):
        body = self.get(self.make(linux_user='x\nExecStart=/bin/evil'), self.owner).content.decode()
        self.assertNotIn('evil', body)
        self.assertIn('User=CHANGE_ME', body)

    def test_name_control_chars_stripped(self):
        body = self.get(self.make(name='a\nExecStart=/bin/x\r\x00b'), self.owner).content.decode()
        self.assertEqual([l for l in body.splitlines() if l.startswith('ExecStart=')], ['ExecStart=/opt/Shuttle/shuttle'])
        self.assertIn('Description=Shuttle (aExecStart=/bin/xb)\n', body)

    def test_access(self):
        inst = self.make()
        self.assertEqual(self.get(inst, self.other).status_code, 404)
        self.assertEqual(self.get(inst, self.staff).status_code, 200)

    def test_anonymous(self):
        r = self.get(self.make())
        self.assertIn(r.status_code, (302, 403, 404))
        self.assertNotIn(b'ExecStart', r.content)

    def test_windows_is_404(self):
        for arch in ('win_64', 'win_i386'):
            self.assertEqual(self.get(self.make(name='w' + arch, architecture=arch), self.owner).status_code, 404)

    def test_arm(self):
        self.assertEqual(self.get(self.make(name='pi', architecture='raspberry_pi_64'), self.owner).status_code, 200)
