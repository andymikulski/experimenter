from django.core.urlresolvers import reverse
from django.views.generic import CreateView, DetailView
from rest_framework.generics import ListAPIView, UpdateAPIView
from rest_framework.response import Response

from experimenter.experiments.forms import ExperimentForm
from experimenter.experiments.models import Experiment, ExperimentChangeLog
from experimenter.experiments.serializers import (
    ExperimentSerializer,
)


class ExperimentCreateView(CreateView):
    model = Experiment
    form_class = ExperimentForm
    template_name = 'experiments/edit.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_initial(self):
        initial = super().get_initial()

        if 'project' in self.request.GET:
            initial['project'] = self.request.GET['project']

        return initial

    def get_success_url(self):
        return reverse('experiments-detail', kwargs={'slug': self.object.slug})

class ExperimentDetailView(DetailView):
    model = Experiment
    template_name = 'experiments/detail.html'


class ExperimentListView(ListAPIView):
    filter_fields = ('project__slug', 'status')
    queryset = Experiment.objects.all()
    serializer_class = ExperimentSerializer


class ExperimentAcceptView(UpdateAPIView):
    queryset = Experiment.objects.filter(status=Experiment.STATUS_PENDING)
    lookup_field = 'slug'

    def update(self, request, *args, **kwargs):
        experiment = self.get_object()

        old_status = experiment.status

        experiment.status = experiment.STATUS_ACCEPTED
        experiment.save()

        ExperimentChangeLog.objects.create(
            experiment=experiment,
            old_status=old_status,
            new_status=experiment.status,
            changed_by=self.request.user,
        )

        return Response()


class ExperimentRejectView(UpdateAPIView):
    queryset = Experiment.objects.filter(status=Experiment.STATUS_PENDING)
    lookup_field = 'slug'

    def update(self, request, *args, **kwargs):
        experiment = self.get_object()

        old_status = experiment.status

        experiment.status = experiment.STATUS_REJECTED
        experiment.save()

        ExperimentChangeLog.objects.create(
            experiment=experiment,
            old_status=old_status,
            new_status=experiment.status,
            changed_by=self.request.user,
            message=self.request.data.get('message', ''),
        )

        return Response()
