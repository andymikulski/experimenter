from django import forms
from django.utils.text import slugify

from experimenter.projects.models import Project
from experimenter.experiments.models import Experiment, ExperimentChangeLog


class ExperimentForm(forms.ModelForm):
    project = forms.ModelChoiceField(help_text=Experiment.PROJECT_HELP_TEXT, queryset=Project.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}))
    name = forms.CharField(help_text=Experiment.NAME_HELP_TEXT, widget=forms.TextInput(attrs={'class': 'form-control'}))
    slug = forms.CharField(required=False)
    short_description = forms.CharField(help_text=Experiment.SHORT_DESCRIPTION_HELP_TEXT, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    population_percent = forms.DecimalField(help_text=Experiment.POPULATION_PERCENT_HELP_TEXT, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    firefox_version = forms.ChoiceField(choices=Experiment.VERSION_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    firefox_channel = forms.ChoiceField(choices=Experiment.CHANNEL_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    client_matching = forms.CharField(help_text=Experiment.CLIENT_MATCHING_HELP_TEXT, initial=Experiment.CLIENT_MATCHING_DEFAULT, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}))
    proposed_start_date = forms.DateField(help_text=Experiment.PROPOSED_START_DATE_HELP_TEXT, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    proposed_end_date = forms.DateField(help_text=Experiment.PROPOSED_END_DATE_HELP_TEXT, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))

    class Meta:
        model = Experiment
        exclude = ['status', 'total_users']

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data['name']
        slug = slugify(name)

        if (
            self.instance.pk is None and
            self.Meta.model.objects.filter(slug=slug).exists()
        ):
            raise forms.ValidationError(
                'An experiment with this name already exists.')

        return name

    def clean_population_percent(self):
        population_percent = self.cleaned_data['population_percent']

        if population_percent > 100 or population_percent < 0:
            raise forms.ValidationError('The population size must be between 0 and 100 percent.')

        return population_percent

    def clean(self):
        cleaned_data = super().clean()

        name = cleaned_data.get('name')
        cleaned_data['slug'] = slugify(name)

        return cleaned_data

    def save(self, *args, **kwargs):
        instance = super().save(*args, **kwargs)

        ExperimentChangeLog.objects.create(
            experiment=instance,
            changed_by=self.request.user,
            new_status=Experiment.STATUS_CREATED,
        )

        return instance
