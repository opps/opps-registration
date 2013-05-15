# coding: utf-8

from django.forms.widgets import Widget
from django.utils.html import format_html
from django.utils.encoding import force_text


class HTMLWidget(Widget):
    def __init__(self, attrs=None, html=''):
        super(HTMLWidget, self).__init__(attrs=attrs)
        self.html = html

    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        return format_html(force_text(self.html))
