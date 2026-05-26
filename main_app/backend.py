from django.contrib.auth.backends import ModelBackend

from chemotion_api import Instance

from django.contrib.auth import get_user_model

User = get_user_model()

from sdc_user.models import SdcUser

from main_app.models import ElnConnection, ElnUser


class ELNBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):


        try:
            instance = ElnConnection.get_active()
            if not instance:
                raise ValueError('No ELN connected')
            instance = Instance(instance.url).test_connection().login(username, password)
            user, c = User.objects.get_or_create(username=username)
            if c:
                user.is_staff = instance.get_user().is_admin()

            user.set_password(password)
            elnuser, _ = ElnUser.objects.get_or_create(user=user)
            elnuser.token = instance.token
            elnuser.is_eln_user = True
            elnuser.save()
        except:
            try:
                user = User.objects.get(username__iexact=username)
            except User.MultipleObjectsReturned:
                user = User.objects.filter(username__iexact=username).order_by('id').first()
            except:
                return None
            if not user.check_password(password):
                return None
            elnuser, _ = ElnUser.objects.get_or_create(user=user)
            elnuser.token = ""
            elnuser.is_eln_user =  False
            elnuser.save()

        user.save()
        return user

