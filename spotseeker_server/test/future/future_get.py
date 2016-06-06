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
class FutureGETTest(TestCase):

    def setUp(self):
        spot2 = Spot.objects.create(name="Testing spot with future",
                                    latitude=23,
                                    longitude=45)
        attr = FutureSpotExtendedInfo.objects.create(
            key="has_whiteboards",
            value="true",
            valid_on="2016-04-12T17:19:53.279649+00:00",
            valid_until="2016-04-12T17:19:53.279649+00:00",
            spot=spot2)

        # hours1 = \
        #    FutureSpotAvailableHours.objects.create(spot=spot2,
        #                                            day="m",
        #                                            start_time="11:00:00",
        #                                            end_time="23:00:00")
        # hours2 = \
        #    FutureSpotAvailableHours.objects.create(spot=spot2,
        #                                            day="t",
        #                                            start_time="9:00:00",
        #                                            end_time="23:59:59")
        spot2.save()
        self.spot2 = spot2

    def test_spot_future_extended_info(self):
        url = "/api/v1/spot/%s" % self.spot2.pk
        response = self.client.get(url)
        spot_dict = json.loads(response.content)
        returned_spot = Spot.objects.get(pk=spot_dict['id'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(returned_spot, self.spot2)
        self.assertEqual(
            spot_dict['future_extended_info']['1']['has_whiteboards'],
            'true'
        )
        self.assertEqual(
            spot_dict['future_extended_info']['1']['valid_on'],
            '2016-04-12T17:19:53.279649+00:00'
        )
        self.assertEqual(
            spot_dict['future_extended_info']['1']['valid_until'],
            '2016-04-12T17:19:53.279649+00:00'
        )

    # def test_spot_future_available_hours(self):
    #    url = "/api/v1/spot/%s" % self.spot2.pk
    #    response = self.client.get(url)
    #    returned_spot = Spot.objects.get(pk=spot_dict['id'])
    #    self.assertEqual(response.status_code, 200)
    #    self.assertEqual(returned_spot, self.spot2)


    def tearDown(self):
        self.spot2.delete()
