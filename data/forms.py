from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div


class JobTemplateForm(forms.Form):
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