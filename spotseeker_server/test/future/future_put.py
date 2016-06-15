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
@override_settings(SPOTSEEKER_AUTH_ADMINS=('demo_user',))
class FuturePUTTest(TestCase):
    def setUp(self):
        self.spot1 = Spot.objects.create(name="Testing spot with future",
                                         latitude=23,
                                         longitude=45)
        attr = FutureSpotExtendedInfo.objects.create(
            key="has_whiteboards",
            value="true",
            valid_on="2016-10-12T17:19:53.279649+00:00",
            valid_until="2016-04-12T17:19:53.279649+00:00",
            spot=self.spot1
        )
        attr = FutureSpotExtendedInfo.objects.create(
            key="has_dlfgdf",
            value="true",
            valid_on="2016-04-12T17:19:53.279649+00:00",
            valid_until="2016-04-12T17:19:53.279649+00:00",
            spot=self.spot1
        )

        # hours1 = \
        #    FutureSpotAvailableHours.objects.create(spot=self.spot1,
        #                                            day="m",
        #                                            start_time="11:00:00",
        #                                            end_time="23:00:00")
        # hours2 = \
        #    FutureSpotAvailableHours.objects.create(spot=self.spot1,
        #                                            day="t",
        #                                            start_time="9:00:00",
        #                                            end_time="23:59:59")
        self.spot1.save()

        self.client = Client()

    def test_spot_put_new_future_info(self):
        url = "/api/v1/spot/%s" % self.spot1.pk

        response = self.client.get(url)
        etag = response["ETag"]

        response = self.client.put(
            url,
            '{"name":"%s","capacity":"%d", "location": '
            '{"latitude": 55, "longitude": 30}, '
            '"future_extended_info": '
            '[ {"has_a_funky_beat": "true",'
            '"valid_on":"2016-04-12T10:19:53.279649",'
            '"valid_until": ""},'
            '{"has_whiteboards": "true",'
            '"valid_on": "2016-10-12T17:19:53.279649", '
            '"valid_until": "2016-04-12T17:19:53.279649"},'
            '{"has_dlfgdf": "true", '
            '"valid_on": "2016-04-12T17:19:53.279649", '
            '"valid_until": "2016-04-12T17:19:53.279649"}] }'
            % (self.spot1.name, 5),
            content_type="application/json",
            If_Match=etag)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            len(self.spot1.spotextendedinfo_set.filter(
                key="has_a_funky_beat")),
            1)

    def test_spot_put_remove_future_info(self):
        url = "/api/v1/spot/%s" % self.spot1.pk

        response = self.client.get(url)
        etag = response["ETag"]

        response = self.client.put(
            url,
            '{"name":"%s","capacity":"%d", "location": '
            '{"latitude": 55, "longitude": 30}, '
            '"future_extended_info": '
            '[ {"has_whiteboards": "true",'
            '"valid_on": "2016-10-12T17:19:53.279649", '
            '"valid_until": "2016-04-12T17:19:53.279649"} ] }'
            % (self.spot1.name, 5),
            content_type="application/json",
            If_Match=etag)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            len(self.spot1.spotextendedinfo_set.filter(
                key="has_dlfgdf")),
            0)
