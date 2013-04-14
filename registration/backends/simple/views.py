from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth import get_user_model

from ...signals import user_registered
from ...views import RegistrationView as BaseRegistrationView

from ...utils import get_or_generate_username

User = get_user_model()


class RegistrationView(BaseRegistrationView):
    """
    A registration backend which implements the simplest possible
    workflow: a user supplies a username, email address and password
    (the bare minimum for a useful account), and is immediately signed
    up and logged in).

    """
    def register(self, request, **cleaned_data):
        username, email, password = cleaned_data['username'], cleaned_data['email'], cleaned_data['password1']
        new_user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # ensure username for cases qhere email is the USERNAME_FIELD
        if not new_user.username or new_user.username is None:
            new_user.username = get_or_generate_username(new_user)
            new_user.save()

        # if the default username_field is not 'username'
        username_field = getattr(User, 'USERNAME_FIELD', 'username')
        data = {
            username_field: cleaned_data[username_field],
            'password': password
        }
        new_user = authenticate(**data)
        login(request, new_user)
        user_registered.send(sender=self.__class__,
                             user=new_user,
                             request=request)
        return new_user

    def registration_allowed(self, request):
        """
        Indicate whether account registration is currently permitted,
        based on the value of the setting ``REGISTRATION_OPEN``. This
        is determined as follows:

        * If ``REGISTRATION_OPEN`` is not specified in settings, or is
          set to ``True``, registration is permitted.

        * If ``REGISTRATION_OPEN`` is both specified and set to
          ``False``, registration is not permitted.

        """
        return getattr(settings, 'REGISTRATION_OPEN', True)

    def get_success_url(self, request, user):
        return (user.get_absolute_url(), (), {})
