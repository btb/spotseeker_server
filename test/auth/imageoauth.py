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
from spotseeker_server.models import Spot, TrustedOAuthClient
import random
from os.path import abspath, dirname
import tempfile
import shutil
from django.test.utils import override_settings
from mock import patch
from django.core import cache
from spotseeker_server import models
import hashlib
import time
import oauth2 as oauth
from oauth_provider.models import Consumer

TEST_ROOT = abspath(dirname(__file__))


@override_settings(SPOTSEEKER_AUTH_MODULE='spotseeker_server.auth.oauth')
class SpotImagePOSTAuthOAuth(TestCase):
    """ Tests POSTing to /api/v1/spot/<spot id>/image.
    """

    def setUp(self):
        self.TEMP_DIR = tempfile.mkdtemp()
        spot = Spot.objects.create(name="This is to test adding images")
        spot.save()
        self.spot = spot

        self.url = '/api/v1/spot/{0}/image'.format(self.spot.pk)
        self.url = self.url

    def test_jpeg(self):
        dummy_cache = cache.get_cache('django.core.cache.backends.dummy.DummyCache')
        with patch.object(models, 'cache', dummy_cache):
            with self.settings(MEDIA_ROOT=self.TEMP_DIR):
                c = Client()
                f = open("%s/../resources/test_jpeg.jpg" % TEST_ROOT)
                response = c.post(self.url, {"description": "This is a jpeg", "image": f})
                f.close()

                self.assertEqual(response.content, "Error authorizing application")

    def test_valid_gif(self):
        dummy_cache = cache.get_cache('django.core.cache.backends.dummy.DummyCache')
        with patch.object(models, 'cache', dummy_cache):
            with self.settings(MEDIA_ROOT=self.TEMP_DIR):
                consumer_name = "Test consumer"
                key = hashlib.sha1("{0} - {1}".format(random.random(), time.time())).hexdigest()
                secret = hashlib.sha1("{0} - {1}".format(random.random(), time.time())).hexdigest()

                create_consumer = Consumer.objects.create(name=consumer_name, key=key, secret=secret)
                trusted_consumer = TrustedOAuthClient.objects.create(consumer=create_consumer, is_trusted=True)

                consumer = oauth.Consumer(key=key, secret=secret)

                req = oauth.Request.from_consumer_and_token(consumer, None, http_method='GET', http_url="http://testserver/api/v1/spot/%s" % self.spot.pk)
                oauth_header = req.to_header()

                client = Client()
                f = open("%s/../resources/test_gif.gif" % TEST_ROOT)
                body = {"description": "This is a gif", "image": f}
                response = client.post(self.url, {"description": "This is a png", "image": f}, HTTP_AUTHORIZATION=oauth_header['Authorization'], HTTP_XOAUTH_USER="pmichaud")
                f.close()

                self.assertEquals(response.status_code, 201, "Gives a Created response to posting a gif")


    def test_invalid_image_type(self):
        dummy_cache = cache.get_cache('django.core.cache.backends.dummy.DummyCache')
        with patch.object(models, 'cache', dummy_cache):
            with self.settings(MEDIA_ROOT=self.TEMP_DIR):
                c = Client()
                f = open("%s/../resources/test_bmp.bmp" % TEST_ROOT)
                response = c.post(self.url, {"description": "This is a bmp file - invalid format", "image": f})
                f.close()

                self.assertEqual(response.content, "Error authorizing application")

    def test_invalid_file(self):
        dummy_cache = cache.get_cache('django.core.cache.backends.dummy.DummyCache')
        with patch.object(models, 'cache', dummy_cache):
            with self.settings(MEDIA_ROOT=self.TEMP_DIR):
                c = Client()
                f = open("%s/../resources/fake_jpeg.jpg" % TEST_ROOT)
                response = c.post(self.url, {"description": "This is really a text file", "image": f})
                f.close()

                self.assertEqual(response.content, "Error authorizing application")

    def test_no_file(self):
        dummy_cache = cache.get_cache('django.core.cache.backends.dummy.DummyCache')
        with patch.object(models, 'cache', dummy_cache):
            with self.settings(MEDIA_ROOT=self.TEMP_DIR):
                c = Client()
                response = c.post(self.url, {"description": "This is really a text file"})

                self.assertEqual(response.content, "Error authorizing application")

    def tearDown(self):
        shutil.rmtree(self.TEMP_DIR)
