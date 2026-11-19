from django.template.loader import render_to_string
from django.test import SimpleTestCase


class DocsPagesTest(SimpleTestCase):
    def test_basic_info_renders_troubleshooting(self):
        html = render_to_string('main_app/sdc/basic_info.html')
        self.assertIn('Troubleshooting', html)
        for message in [
            'Error connecting to destination (will retry)',
            'SSH host key for ',
            'CHANGED (presented SHA256:',
            'SSH host key mismatch for ',
            'TLS certificate verification is DISABLED (-insecure)',
            'WinSCP.com not found, expected at ',
            'cannot read -crt file ',
            'startup check failed: converter executable does not exist',
            'Sent register: 0 entries loaded, empty register: all stable files will be sent once',
        ]:
            self.assertIn(message, html)
        self.assertIn('/opt/Shuttle', html)
        self.assertIn('Program Files', html)

    def test_shuttle_scripts_renders_rules(self):
        html = render_to_string('main_app/sdc/shuttle_scripts.html')
        for text in ['.exe', 'execute bit', 'alphabetical order', 'hidden files', 'conversion skipped',
                     'converter executable does not exist']:
            self.assertIn(text, html)
