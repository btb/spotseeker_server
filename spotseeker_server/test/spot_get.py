""" Copyright 2012, 2013 UW Information Technology, University of Washington

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

from django.test import TestCase
from django.conf import settings
from django.test.client import Client
from spotseeker_server.models import Spot, SpotExtendedInfo, \
    FutureSpotExtendedInfo
import simplejson as json
from django.test.utils import override_settings
from mock import patch
from django.core import cache
from spotseeker_server import models


@override_settings(
    SPOTSEEKER_AUTH_MODULE='spotseeker_server.auth.all_ok',
    SPOTSEEKER_SPOT_FORM='spotseeker_server.default_forms.spot.'
                         'DefaultSpotForm')
class SpotGETTest(TestCase):

    def setUp(self):
        dummy_cache = \
            cache.get_cache('django.core.cache.backends.dummy.DummyCache')
        with patch.object(models, 'cache', dummy_cache):
            self.client = Client()
            spot1 = Spot.objects.create(name="This is for testing GET",
                                        latitude=55,
                                        longitude=30)
            spot1.save()
            self.spot1 = spot1

    def test_invalid_id(self):
        dummy_cache = \
            cache.get_cache('django.core.cache.backends.dummy.DummyCache')
        with patch.object(models, 'cache', dummy_cache):
            response = self.client.get("/api/v1/spot/bad_id")
            self.assertEqual(response.status_code,
                             404,
                             "Rejects a non-numeric id")

    def test_invalid_id_too_high(self):
        dummy_cache = \
            cache.get_cache('django.core.cache.backends.dummy.DummyCache')
        with patch.object(models, 'cache', dummy_cache):
            url = "/api/v1/spot/%s" % (self.spot1.pk + 10000)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404, "Spot ID too high")

    def test_content_type(self):
        dummy_cache = \
            cache.get_cache('django.core.cache.backends.dummy.DummyCache')
        with patch.object(models, 'cache', dummy_cache):
            url = "/api/v1/spot/%s" % self.spot1.pk
            response = self.client.get(url)
            self.assertEqual(response["Content-Type"], "application/json")

            url = "/api/v1/spot/all"
            response = self.client.get(url)
            self.assertEqual(response["Content-Type"], "application/json")

    def test_etag(self):
        dummy_cache = \
            cache.get_cache('django.core.cache.backends.dummy.DummyCache')
        with patch.object(models, 'cache', dummy_cache):
            url = "/api/v1/spot/%s" % self.spot1.pk
            response = self.client.get(url)
            self.assertEqual(response["ETag"], self.spot1.etag)

    def test_invalid_params(self):
        dummy_cache = \
            cache.get_cache('django.core.cache.backends.dummy.DummyCache')
        with patch.object(models, 'cache', dummy_cache):
            url = "/api/v1/spot/%s" % self.spot1.pk
            response = self.client.get(url, {'bad_param': 'does not exist'},)
            self.assertEqual(response.status_code, 200)
            spot_dict = json.loads(response.content)
            returned_spot = Spot.objects.get(pk=spot_dict['id'])
            self.assertEqual(returned_spot, self.spot1)

    def test_valid_id(self):
        dummy_cache = \
            cache.get_cache('django.core.cache.backends.dummy.DummyCache')
        with patch.object(models, 'cache', dummy_cache):
            url = "/api/v1/spot/%s" % self.spot1.pk
            response = self.client.get(url)
            spot_dict = json.loads(response.content)
            returned_spot = Spot.objects.get(pk=spot_dict['id'])
            self.assertEqual(response.status_code, 200)
            self.assertEqual(returned_spot, self.spot1)
