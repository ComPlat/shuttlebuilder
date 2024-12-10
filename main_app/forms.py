import re

from jsonschema.exceptions import ValidationError

from main_app.models import ShuttleInstance
from main_app.models import GitInstance
from main_app.models import ElnConnection
from django.forms.models import ModelForm


# Form Model ElnConnection

class ElnConnectionForm(ModelForm):
    class Meta:
        model = ElnConnection
        fields = "__all__"



# Form Model GitInstance

class GitInstanceForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = self.instance
        if instance and instance.pk:
            self.fields['name'].widget.attrs['readonly'] = True


    def clean_name(self):
        instance = self.instance
        if instance and instance.pk:
            return instance.name
        else:
            return self.cleaned_data['name']


    class Meta:
        model = GitInstance
        fields = ['name', 'url', 'branch']

    def generate_filte(self):
        pass



# Form Model ShuttleInstance

class ShuttleInstanceForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = self.instance
        if instance and instance.pk:
            self.fields['name'].widget.attrs['readonly'] = True

    def clean_name(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.name
        else:
            return self.cleaned_data['name']

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data['shuttle_type'] == 'flat_tar':
            common_name_parts = cleaned_data.get('common_name_parts', '')
            if len(common_name_parts) == 0:
                self.add_error('common_name_parts', ValidationError('Common name regex must not be empty if the send type is set to flat_tar'))

            try:
                re.compile(fr"{common_name_parts}")
            except:
                self.add_error('common_name_parts', ValidationError('Common name regex must be a compilable regular expression send type is set to flat_tar'))
        return cleaned_data

    class Meta:
        model = ShuttleInstance
        fields = ['name', 'transfer', 'user', 'password', 'src', 'dst', 'shuttle_type', 'common_name_parts', 'duration', 'architecture']
