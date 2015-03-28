from django import forms
from django.core.files import File
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div

from models import JobTemplate
from project.utils import StringIO


class JobTemplateForm(forms.ModelForm):
    name = forms.CharField(max_length=400)
    template = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'cols': 50,
                'rows': 26,
            }),
        required=False,
    )

    helper = FormHelper()
    helper.form_tag = False
    helper.layout = Layout(
        Div(
            Div('name', css_class='col-xs-12'),
        css_class='row'),
        'template',
    )
    def __init__(self, user, *args, **kwargs):
        super(JobTemplateForm, self).__init__(*args, **kwargs)
        self.user = user

    class Meta:
        model = JobTemplate
        fields = ("name", "template")

    def clean_template(self):
        template = self.cleaned_data.get("template")
        name = self.cleaned_data.get("name")
        return File(StringIO(template, name=name))