"""
Forms and validation code for user registration.

Note that all of these forms assume Django's bundle default ``User``
model; since it's not possible for a form to anticipate in advance the
needs of custom user models, you will need to write your own forms if
you're using a custom model.

"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django import forms
from django.utils.translation import ugettext_lazy as _

User = get_user_model()

USER_MODEL_FIELD_NAMES = [field.name for field in User._meta.fields]
USER_REQUIRED_FIELDS = set([User.USERNAME_FIELD] + list(User.REQUIRED_FIELDS))

USER_FORM_FIELDS = getattr(settings, 'USER_FORM_FIELDS', USER_REQUIRED_FIELDS)
USER_FORM_REQUIRED_FIELDS = getattr(settings, 'USER_FORM_REQUIRED_FIELDS', USER_REQUIRED_FIELDS)

required_attrs = {'class': 'required', 'required': 'required'}


class RegistrationFormFromUserModel(object):
    """
    Create form from django user model
    """
    def __init__(self, *args, **kwargs):
        super(RegistrationFormFromUserModel, self).__init__(*args, **kwargs)
        # add new fields befor exsist sields
        insert_index = 0
        for field in USER_FORM_FIELDS:
            formfield = User._meta.get_field(field).formfield()
            if field in USER_FORM_REQUIRED_FIELDS:
                formfield.required = True
                formfield.widget.attrs['required'] = 'required'
                formfield.widget.attrs['class'] = 'required'
            self.fields.insert(insert_index, field, formfield)
            insert_index += 1


class RegistrationForm(RegistrationFormFromUserModel, forms.Form):
    """
    Form for registering a new user account.

    Validates that the requested username is not already in use, and
    requires the password to be entered twice to catch typos.

    Subclasses should feel free to add any additional validation they
    need, but should avoid defining a ``save()`` method -- the actual
    saving of collected user data is delegated to the active
    registration backend.

    """
    required_css_class = 'required'

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs=required_attrs, render_value=True),
        label=_("Password")
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs=required_attrs, render_value=True),
        label=_("Password (again)")
    )

    def clean(self):
        """
        Verifiy that the values entered into the two password fields
        match. Note that an error here will end up in
        ``non_field_errors()`` because it doesn't apply to a single
        field.

        """
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError(_("The two password fields didn't match."))

        # validate if the USERNAME_FIELD does not already exists
        username_field = User.USERNAME_FIELD

        if username_field in self.cleaned_data:
            lookup = {'{0}__iexact'.format(username_field): self.cleaned_data[username_field]}
            if User.objects.filter(**lookup).exists():
                raise forms.ValidationError(
                    _("This %s is already in use.") % username_field
                )

        if username_field != 'username' and 'username' in USER_MODEL_FIELD_NAMES:
            if 'username' in self.cleaned_data:
                # validate the username
                if User.objects.filter(username__iexact=self.cleaned_data['username']).exists():
                    raise forms.ValidationError(_("A user with that username already exists."))

        # validate every required field
        for field in USER_FORM_REQUIRED_FIELDS:
            verbose_name = getattr(User._meta.get_field(field), 'verbose_name', field)
            if not self.cleaned_data.get(field, None):
                raise forms.ValidationError(
                    _(u"You need to fill the %s field.") % verbose_name
                )

        return self.cleaned_data


class RegistrationFormTermsOfService(RegistrationForm):
    """
    Subclass of ``RegistrationForm`` which adds a required checkbox
    for agreeing to a site's Terms of Service.

    """
    tos = forms.BooleanField(widget=forms.CheckboxInput,
                             label=_(u'I have read and agree to the Terms of Service'),
                             error_messages={'required': _("You must agree to the terms to register")})


class RegistrationFormUniqueEmail(RegistrationForm):
    """
    Subclass of ``RegistrationForm`` which enforces uniqueness of
    email addresses.

    """
    def clean_email(self):
        """
        Validate that the supplied email address is unique for the
        site.

        """
        if User.objects.filter(email__iexact=self.cleaned_data['email']):
            raise forms.ValidationError(_("This email address is already in use. Please supply a different email address."))
        return self.cleaned_data['email']


class RegistrationFormNoFreeEmail(RegistrationForm):
    """
    Subclass of ``RegistrationForm`` which disallows registration with
    email addresses from popular free webmail services; moderately
    useful for preventing automated spam registrations.

    To change the list of banned domains, subclass this form and
    override the attribute ``bad_domains``.

    """

    bad_domains = getattr(
        settings,
        'REGISTRATION_BAD_DOMAINS',
        ['aim.com', 'aol.com', 'email.com', 'gmail.com',
         'googlemail.com', 'hotmail.com', 'hushmail.com',
         'msn.com', 'mail.ru', 'mailinator.com', 'live.com',
         'yahoo.com']
    )

    def clean_email(self):
        """
        Check the supplied email address against a list of known free
        webmail domains.

        """
        email_domain = self.cleaned_data['email'].split('@')[1]
        if email_domain in self.bad_domains:
            raise forms.ValidationError(_("Registration using free email addresses is prohibited. Please supply a different email address."))
        return self.cleaned_data['email']
