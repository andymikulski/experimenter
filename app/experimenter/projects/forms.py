from django import forms
from django.utils.text import slugify

from experimenter.projects.models import Project


class ProjectForm(forms.ModelForm):
    name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}))
    slug = forms.CharField(required=False)

    class Meta:
        model = Project
        fields = ('name', 'slug', 'image')

    def clean_name(self):
        name = self.cleaned_data['name']
        slug = slugify(name)

        if (
            self.instance.pk is None and
            self.Meta.model.objects.filter(slug=slug).exists()
        ):
            raise forms.ValidationError(
                'A project with this name already exists.')

        return name

    def clean(self):
        cleaned_data = super().clean()

        name = cleaned_data.get('name')
        cleaned_data['slug'] = slugify(name)

        return cleaned_data
