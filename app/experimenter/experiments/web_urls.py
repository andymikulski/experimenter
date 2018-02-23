from django.conf.urls import url

from experimenter.experiments.views import (
    ExperimentCreateView,
    ExperimentDetailView,
)


urlpatterns = [
    url(
        r'^new/$',
        ExperimentCreateView.as_view(),
        name='experiments-create',
    ),
    url(
        r'^(?P<slug>[a-zA-Z0-9-]+)/$',
        ExperimentDetailView.as_view(),
        name='experiments-detail',
    ),
]
