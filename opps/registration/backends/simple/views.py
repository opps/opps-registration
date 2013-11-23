from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from ...signals import user_registered
from ...views import RegistrationView as BaseRegistrationView

from ...utils import get_or_generate_username

User = get_user_model()

USER_FORM_REQUIRED_FIELDS = getattr(settings, 'USER_FORM_REQUIRED_FIELDS', [])
USER_MODEL_FIELD_NAMES = [field.name for field in User._meta.fields]
USER_REQUIRED_FIELDS = set(
    [User.USERNAME_FIELD] + list(User.REQUIRED_FIELDS) + USER_FORM_REQUIRED_FIELDS
)
USER_FORM_FIELDS = getattr(settings, 'USER_FORM_FIELDS', USER_REQUIRED_FIELDS)


class RegistrationView(BaseRegistrationView):
    """
    A registration backend which implements the simplest possible
    workflow: a user supplies a username, email address and password
    (the bare minimum for a useful account), and is immediately signed
    up and logged in).

    """

    def validate_and_register(self, request, **raw_data):
        """
        Receives a dictionary and validate its data against User model
        and also USER_* settings variables
        if validated creates a new user and authenticate
        else return errors key populated
        """

        cleaned_data = {}
        errors = {}

        for k, v in raw_data.items():
            if v in ['true', 'True', 'on']:
                raw_data[k] = True
            if v in ['false', 'False', 'off']:
                raw_data[k] = False

        for field in USER_REQUIRED_FIELDS:
            if raw_data.get(field) is None:
                errors[field] = [u"required"]

        registration_fields = {
            k: v for k, v in raw_data.items() if k in USER_FORM_FIELDS
        }

        for k, v in registration_fields.items():
            try:
                cleaned_data[k] = User._meta.get_field(k).clean(v, None)
            except ValidationError as e:
                errors[k] = e.messages

        if not errors:
            u_field = User.USERNAME_FIELD
            filters = {u_field: cleaned_data.get(u_field)}
            if User.objects.filter(**filters).exists():
                errors[u_field] = [u'Duplicated %s' % u_field]

        remaining = {
            k: v for k, v in raw_data.items() if k not in USER_FORM_FIELDS
        }

        cleaned_data.update(remaining)

        if not errors:
            user = self.register(request, **cleaned_data)
            if user:
                cleaned_data['id'] = user.pk
            else:
                errors['user'] = [u'Can not authenticate user']

        for k, v in cleaned_data.items():
            if 'password' in k:
                cleaned_data[k] = "*" * len(v)

        response = {
            "errors": errors,
            "cleaned_data": cleaned_data,
            'success': not errors
        }

        redirect_url = getattr(settings, 'OPPS_REGISTRATION_REDIRECT_URL', None)
        if redirect_url:
            response['redirect_url'] = redirect_url

        return response

    def register(self, request, **cleaned_data):
        user_args = {
            'password': cleaned_data.get('password1', cleaned_data.get('password'))
        }
        for field in USER_FORM_FIELDS:
            if field in cleaned_data:
                user_args[field] = cleaned_data[field]

        new_user = User.objects.create_user(**user_args)

        # ensure username for cases where email is the USERNAME_FIELD
        if not new_user.username or new_user.username is None:
            new_user.username = get_or_generate_username(new_user)
            new_user.save()

        # if the default username_field is not 'username'
        username_field = getattr(User, 'USERNAME_FIELD', 'username')
        data = {
            username_field: user_args[username_field],
            'password': user_args['password']
        }

        new_user = authenticate(**data)
        if not new_user:
            return
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
