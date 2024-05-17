from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q
from chemotion_api import Instance

from main_app.models import ElnConnection


class ELNBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):


        try:
            instance = ElnConnection.get_active()
            instance = Instance(instance.url).test_connection().login(username, password)
            user, c = User.objects.get_or_create(username=username)
            if c:
                user.is_staff = instance.get_user().is_admin()

            user.set_password(password)
            user.elnuser.token = instance.token
            user.elnuser.is_eln_user = True
        except:
            try:
                user = User.objects.get(username__iexact=username)
            except User.MultipleObjectsReturned:
                user = User.objects.filter(username__iexact=username).order_by('id').first()
            except:
                return None
            if not user.check_password(password):
                return None
            user.elnuser.is_eln_user = False

        user.elnuser.save()
        user.save()
        return user

