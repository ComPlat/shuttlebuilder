from django.utils import timezone

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

    class Meta:
        model = ShuttleInstance
        fields = ['name', 'transfer', 'user', 'password', 'src', 'dst', 'shuttle_type', 'duration', 'architecture']
