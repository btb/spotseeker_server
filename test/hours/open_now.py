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
from django.utils.unittest import skipIf
from django.conf import settings
from django.test.client import Client
from spotseeker_server.models import Spot, SpotAvailableHours, SpotMetaType
import simplejson as json
from datetime import datetime
import datetime as alternate_date

from time import *
from django.test.utils import override_settings
from mock import patch
from django.core import cache
from spotseeker_server import models


@override_settings(SPOTSEEKER_AUTH_MODULE='spotseeker_server.auth.all_ok')
class SpotHoursOpenNowTest(TestCase):
    """ Tests that we can tell if a Spot is available now, based on it's Available Hours.
    """

    @skipIf(datetime.now().hour + 2 > 23 or datetime.now().hour < 2, "Skip open_now tests due to the time of day")
    def test_open_now(self):
        dummy_cache = cache.get_cache('django.core.cache.backends.dummy.DummyCache')
        with patch.object(models, 'cache', dummy_cache):
            default_meta_name = getattr(settings, 'SS_DEFAULT_META_TYPE', 'default')
            default_meta_type = SpotMetaType.objects.get_or_create(name=default_meta_name)[0]
            open_spot = Spot.objects.create(name="This spot is open now")
            open_spot.spotmetatypes.add(default_meta_type)
            no_hours_spot = Spot.objects.create(name="This spot has no hours")
            no_hours_spot.spotmetatypes.add(default_meta_type)
            closed_spot = Spot.objects.create(name="This spot has hours, but is closed")
            closed_spot.spotmetatypes.add(default_meta_type)

            now = datetime.time(datetime.now())

            open_start = alternate_date.time(now.hour - 1, now.minute)
            open_end = alternate_date.time(now.hour + 1, now.minute)

            closed_start = alternate_date.time(now.hour + 1, now.minute)
            closed_end = alternate_date.time(now.hour + 2, now.minute)

            day_lookup = ["su", "m", "t", "w", "th", "f", "sa"]
            day_num = int(strftime("%w", localtime()))
            today = day_lookup[day_num]

            open_hours = SpotAvailableHours.objects.create(spot=open_spot, day=today, start_time=open_start, end_time=open_end)
            closed_hours = SpotAvailableHours.objects.create(spot=closed_spot, day=today, start_time=closed_start, end_time=closed_end)

            # Testing to make sure too small of a radius returns nothing
            c = Client()
            response = c.get("/api/v1/spot", {'open_now': True})
            self.assertEquals(response.status_code, 200, "Accepts a query for open now")
            spots = json.loads(response.content)

            has_open_spot = False
            has_closed_spot = False
            has_no_hours_spot = False

            for spot in spots:
                if spot['id'] == open_spot.pk:
                    has_open_spot = True

                if spot['id'] == closed_spot.pk:
                    has_closed_spot = True

                if spot['id'] == no_hours_spot.pk:
                    has_no_hours_spot = True

            self.assertEquals(has_closed_spot, False, "Doesn't find the closed spot")
            self.assertEquals(has_no_hours_spot, False, "Doesn't find the spot with no hours")
            self.assertEquals(has_open_spot, True, "Finds the open spot")
