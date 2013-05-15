#coding: utf-8

from django.forms.fields import Field
from .widgets import HTMLWidget


class HTMLField(Field):

    def __init__(self, html=None, *args, **kwargs):
        super(HTMLField, self).__init__(
            widget=HTMLWidget(html=html),
            required=False,
            **kwargs
        )

    def to_python(self, value):
        "Returns a Unicode object."
        return u""

    def widget_attrs(self, widget):
        attrs = super(HTMLField, self).widget_attrs(widget)
        return attrs
