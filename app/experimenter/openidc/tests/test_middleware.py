from django.conf import settings
from django.contrib.auth.models import User, Group
from django.urls import Resolver404
from django.test import TestCase

import mock

from experimenter.openidc.middleware import OpenIDCAuthMiddleware


class OpenIDCAuthMiddlewareTests(TestCase):

    def setUp(self):
        self.middleware = OpenIDCAuthMiddleware()

        mock_resolve_patcher = mock.patch(
            'experimenter.openidc.middleware.resolve')
        self.mock_resolve = mock_resolve_patcher.start()
        self.addCleanup(mock_resolve_patcher.stop)

    def test_get_group_creates_group_with_project_experiment_permissions(self):
        self.assertFalse(Group.objects.all().exists())
        group = self.middleware.get_experimenter_group()
        self.assertTrue(Group.objects.all().exists())
        self.assertEqual(group.permissions.all().count(), 12)
        self.assertEqual(
            set([
                permission.content_type.app_label for
                permission in group.permissions.all()
            ]),
            set(['projects', 'experiments']),
        )

    def test_get_group_only_creates_one_group(self):
        self.assertEqual(Group.objects.all().count(), 0)
        self.middleware.get_experimenter_group()
        self.assertEqual(Group.objects.all().count(), 1)
        self.middleware.get_experimenter_group()
        self.assertEqual(Group.objects.all().count(), 1)

    def test_whitelisted_url_is_not_authed(self):
        request = mock.Mock()
        request.path = '/whitelisted-view/'
        whitelisted_view_name = 'whitelisted-view'

        with self.settings(OPENIDC_AUTH_WHITELIST=[whitelisted_view_name]):
            mock_view = mock.Mock()
            mock_view.url_name = whitelisted_view_name
            self.mock_resolve.return_value = mock_view

            response = self.middleware.process_request(request)
            self.assertEqual(response, None)

    def test_404_path_forces_authentication(self):
        request = mock.Mock()
        request.META = {
        }

        self.mock_resolve.side_effect = Resolver404

        response = self.middleware.process_request(request)
        self.assertEqual(response.status_code, 401)

    def test_request_missing_headers_raises_401(self):
        request = mock.Mock()
        request.META = {
        }

        with self.settings(OPENIDC_AUTH_WHITELIST=[]):
            response = self.middleware.process_request(request)

        self.assertEqual(response.status_code, 401)

    def test_user_created_with_correct_email_from_header(self):
        user_email = 'user@example.com'

        request = mock.MagicMock()
        request.META = {
            settings.OPENIDC_EMAIL_HEADER: user_email,
        }

        self.assertEqual(User.objects.all().count(), 0)

        with self.settings(OPENIDC_AUTH_WHITELIST=[]):
            response = self.middleware.process_request(request)

        self.assertEqual(response, None)
        self.assertEqual(User.objects.all().count(), 1)

        self.assertEqual(request.user.email, user_email)
        self.assertTrue(request.user.is_staff)
        self.assertTrue(
            self.middleware.get_experimenter_group()
            in request.user.groups.all()
        )
