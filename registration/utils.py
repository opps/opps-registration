# coding: utf-8

from django.contrib.auth import get_user_model


def generate_username(user):
    """
    generates a new username based in User email and pk
    this is for the cases where username is not required
    """

    User = get_user_model()

    # First possibility, use the email as username
    username = user.email.replace('@', '_').replace('.', '_')
    if not User.objects.filter(username=username).exists():
        return username
    else:
        # should never be returned, but it is here to avoid conflicts
        return "{0}_{1}".format(username, user.pk)
