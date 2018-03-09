import json

from django import forms
from django.utils.text import slugify

from experimenter.projects.forms import AutoNameSlugFormMixin
from experimenter.projects.models import Project
from experimenter.experiments.models import Experiment, ExperimentVariant, ExperimentChangeLog


class JSONField(forms.CharField):

    def clean(self, value):
        cleaned_value = super().clean(value)

        if cleaned_value:
            try:
                json.loads(cleaned_value)
            except json.JSONDecodeError:
                raise forms.ValidationError('This is not valid JSON.')

        return cleaned_value


class VariantAutoNameSlugFormMixin(object):

    def clean(self):
        cleaned_data = super().clean()

        name = cleaned_data.get('name')
        cleaned_data['slug'] = slugify(name)

        return cleaned_data


class ControlVariantForm(VariantAutoNameSlugFormMixin, forms.ModelForm):
    slug = forms.CharField(required=False)
    experiment = forms.ModelChoiceField(queryset=Experiment.objects.all(), required=False)
    ratio = forms.IntegerField(required=False, label='Variant Split', initial='50', help_text=Experiment.CONTROL_RATIO_HELP_TEXT, widget=forms.NumberInput(attrs={'type':'range', 'min': '1', 'max': '99', 'step': '1'}))
    name = forms.CharField(label='Name', help_text=Experiment.CONTROL_NAME_HELP_TEXT, widget=forms.TextInput(attrs={'class': 'form-control'}))
    description = forms.CharField(label='Description', help_text=Experiment.CONTROL_DESCRIPTION_HELP_TEXT, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    value = JSONField(label='Pref Value', help_text=Experiment.CONTROL_VALUE_HELP_TEXT, widget=forms.TextInput(attrs={'class': 'form-control'}))

    prefix = 'control_'

    class Meta:
        model = ExperimentVariant
        fields = [
            'slug',
            'experiment',
            'ratio',
            'name',
            'description',
            'value',
            'is_control',
        ]


    def clean_is_control(self):
        return True


class ExperimentalVariantForm(VariantAutoNameSlugFormMixin, forms.ModelForm):
    slug = forms.CharField(required=False)
    experiment = forms.ModelChoiceField(required=False, queryset=Experiment.objects.all())
    ratio = forms.IntegerField(required=False, initial='50')
    name = forms.CharField(label='Name', help_text=Experiment.VARIANT_NAME_HELP_TEXT, widget=forms.TextInput(attrs={'class': 'form-control'}))
    description = forms.CharField(label='Description', help_text=Experiment.VARIANT_DESCRIPTION_HELP_TEXT, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    value = JSONField(label='Pref Value', help_text=Experiment.VARIANT_VALUE_HELP_TEXT, widget=forms.TextInput(attrs={'class': 'form-control'}))

    prefix = 'experimental_'

    class Meta:
        model = ExperimentVariant
        fields = [
            'slug',
            'experiment',
            'ratio',
            'name',
            'description',
            'value',
            'is_control',
        ]

    def clean_is_control(self):
        return False


class ExperimentChangelogFormMixin(object):

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        experiment = super().save(*args, **kwargs)

        latest_change = experiment.changes.latest()

        if latest_change:
            ExperimentChangeLog.objects.create(
                experiment=experiment,
                changed_by=self.request.user,
                old_status=latest_change.new_status,
                new_status=experiment.status,
            )
        else:
            ExperimentChangeLog.objects.create(
                experiment=experiment,
                changed_by=self.request.user,
                new_status=Experiment.STATUS_CREATED,
            )

        return experiment


class ExperimentOverviewForm(AutoNameSlugFormMixin, ExperimentChangelogFormMixin, forms.ModelForm):
    project = forms.ModelChoiceField(label='Project', help_text=Experiment.PROJECT_HELP_TEXT, queryset=Project.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}))
    name = forms.CharField(label='Name', help_text=Experiment.NAME_HELP_TEXT, widget=forms.TextInput(attrs={'class': 'form-control'}))
    slug = forms.CharField(required=False)
    short_description = forms.CharField(label='Short Description', help_text=Experiment.SHORT_DESCRIPTION_HELP_TEXT, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    population_percent = forms.DecimalField(label='Population Size', help_text=Experiment.POPULATION_PERCENT_HELP_TEXT, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    firefox_version = forms.ChoiceField(choices=Experiment.VERSION_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    firefox_channel = forms.ChoiceField(choices=Experiment.CHANNEL_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    client_matching = forms.CharField(label='Population Filtering', help_text=Experiment.CLIENT_MATCHING_HELP_TEXT, initial=Experiment.CLIENT_MATCHING_DEFAULT, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 10}))
    proposed_start_date = forms.DateField(label='Proposed Start Date', help_text=Experiment.PROPOSED_START_DATE_HELP_TEXT, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    proposed_end_date = forms.DateField(label='Proposed End Date', help_text=Experiment.PROPOSED_END_DATE_HELP_TEXT, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))

    class Meta:
        model = Experiment
        fields = [
            'project',
            'name',
            'slug',
            'short_description',
            'population_percent',
            'firefox_version',
            'firefox_channel',
            'client_matching',
            'proposed_start_date',
            'proposed_end_date',
        ]

    def clean_population_percent(self):
        population_percent = self.cleaned_data['population_percent']

        if population_percent > 100 or population_percent < 0:
            raise forms.ValidationError('The population size must be between 0 and 100 percent.')

        return population_percent


class ExperimentVariantsForm(ExperimentChangelogFormMixin, forms.ModelForm):
    pref_key = forms.CharField(label='Pref Name', help_text=Experiment.PREF_KEY_HELP_TEXT, widget=forms.TextInput(attrs={'class': 'form-control'}))
    pref_type = forms.ChoiceField(label='Pref Type', help_text=Experiment.PREF_TYPE_HELP_TEXT, choices=Experiment.PREF_TYPE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    pref_branch = forms.ChoiceField(label='Pref Branch', help_text=Experiment.PREF_BRANCH_HELP_TEXT, choices=Experiment.PREF_BRANCH_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = Experiment
        fields = [
            'pref_key',
            'pref_type',
            'pref_branch',
        ]

    def __init__(self, data=None, instance=None, *args, **kwargs):
        super().__init__(data=data, instance=instance, *args, **kwargs)

        self.control_form = ControlVariantForm(
            data=data,
            instance=instance.control if instance else None,
        )
        self.experimental_form = ExperimentalVariantForm(
            data=data,
            instance=instance.variant if instance else None,
        )

    def is_valid(self, *args, **kwargs):
        return super().is_valid(*args, **kwargs) and self.control_form.is_valid(*args, **kwargs) and self.experimental_form.is_valid(*args, **kwargs)

    def save(self, *args, **kwargs):
        experiment = super().save(*args, **kwargs)

        if self.control_form.instance.slug:
            self.control_form.instance.experiment = experiment
            self.control_form.save(*args, **kwargs)

        if self.experimental_form.instance.slug:
            self.experimental_form.instance.experiment = experiment
            self.experimental_form.instance.ratio = 100 - self.control_form.instance.ratio
            self.experimental_form.save(*args, **kwargs)

        return experiment


class ExperimentObjectivesForm(ExperimentChangelogFormMixin, forms.ModelForm):
    objectives = forms.CharField(label='Objectives', help_text=Experiment.OBJECTIVES_HELP_TEXT, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 20}))
    analysis = forms.CharField(label='Analysis Plan', help_text=Experiment.ANALYSIS_HELP_TEXT, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 20}))

    class Meta:
        model = Experiment
        fields = ('objectives', 'analysis')


class ExperimentRisksForm(ExperimentChangelogFormMixin, forms.ModelForm):
    risks = forms.CharField(label='Risks', help_text=Experiment.RISKS_HELP_TEXT, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 20}))
    testing = forms.CharField(label='Test Plan', help_text=Experiment.TESTING_HELP_TEXT, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 20}))

    class Meta:
        model = Experiment
        fields = ('risks', 'testing')
