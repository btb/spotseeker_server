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

from django.core.files import File
from django.test import TestCase
from os.path import abspath, dirname
from spotseeker_server.models import *

TEST_ROOT = abspath(dirname(__file__))


class SpotModelToStringTests(TestCase):

    def test_spot(self):
        """ Tests that a Spot can be successfully created.
        """
        spot = Spot.objects.create(name="This is the test name")

        test_str = "{0}".format(spot)
        self.assertEqual(test_str, "This is the test name")

    def test_available_hours(self):
        """ Tests that SpotAvailableHours can be successfully created.
        """
        spot = Spot.objects.create(name="This is the test name")
        hours = SpotAvailableHours.objects.create(
            spot=spot,
            day="m",
            start_time="11:00",
            end_time="14:00")

        test_str = "{0}".format(hours)
        self.assertEqual(test_str,
                         "This is the test name: m, 11:00:00-14:00:00")

#    def test_future_available_hours(self):
#        """ Tests that FutureSpotAvailableHours can be sucessfully created.
#        """
#        spot = Spot.objects.create(name="This is the test name")
#        hours = FutureSpotAvailableHours.objects.create(
#            spot=spot,
#            day="m",
#            start_time="11:00",
#            end_time="14:00",
#            valid_on="2016-04-12T10:19:53.279649",
#            valid_until="2016-05-12T10:19:53.279649")
#
#        test_str = "{0}".format(hours)
#        self.assertEqual(test_str,
#                         "This is the test name: m, 11:00:00-14:00:00")
#        # assert that spot has future hours

    # test_future_available_hours_no_valid_until

    def test_extended_info(self):
        """ Tests creation of an ExtendedInfo object.
        """
        spot = Spot.objects.create(name="This is the test name")
        attr = SpotExtendedInfo(key="has_whiteboards", value="1", spot=spot)

        test_str = "{0}".format(attr)
        self.assertEqual(test_str, "This is the test name[has_whiteboards: 1]")

    def test_future_extended_info(self):
        """ Tests creation of a FutureExtendedInfo object.
        """
        spot = Spot.objects.create(name="This is the test name")
        key = "has_whiteboards"
        value = "1"
        valid_on = "2016-04-12T17:19:53.279649+00:00"
        valid_until = "2016-05-12T17:19:53.279649+00:00"
        attr = FutureSpotExtendedInfo(key=key,
                                      value=value,
                                      valid_on=valid_on,
                                      valid_until=valid_until,
                                      spot=spot)
        attr.save()

        test_str = "{0}".format(attr)
        self.assertEqual(test_str, "This is the test name[has_whiteboards: 1]")

        # assert the object has the right attributes
        self.assertTrue(hasattr(attr, 'key'))
        self.assertTrue(hasattr(attr, 'value'))
        self.assertTrue(hasattr(attr, 'valid_on'))
        self.assertTrue(hasattr(attr, 'valid_until'))

        # assert that the json contains future_extended_info
        jds = spot.json_data_structure()
        self.assertTrue('future_extended_info' in jds.keys())

        # assert that the value for future ei looks right
        compare = {}
        compare[key] = value
        compare['valid_on'] = valid_on
        compare['valid_until'] = valid_until
        self.assertTrue(compare in jds['future_extended_info'].values())

    def test_future_extended_info_no_valid_until(self):
        """ Tests creation of a FutureExtendedInfo object.
        """
        spot = Spot.objects.create(name="This is the test name")
        key = "has_whiteboards"
        value = "1"
        valid_on = "2016-04-12T17:19:53.279649+00:00"
        valid_until = None
        attr = FutureSpotExtendedInfo(key=key,
                                      value=value,
                                      valid_on=valid_on,
                                      valid_until=valid_until,
                                      spot=spot)
        attr.save()

        test_str = "{0}".format(attr)
        self.assertEqual(test_str, "This is the test name[has_whiteboards: 1]")

        # assert the object has the right attributes
        self.assertTrue(hasattr(attr, 'key'))
        self.assertTrue(hasattr(attr, 'value'))
        self.assertTrue(hasattr(attr, 'valid_on'))
        self.assertTrue(hasattr(attr, 'valid_until'))

        # assert that the json contains future_extended_info
        jds = spot.json_data_structure()
        self.assertTrue('future_extended_info' in jds.keys())

        # assert that the value for future ei looks right
        compare = {}
        compare[key] = value
        compare['valid_on'] = valid_on
        self.assertTrue(compare in jds['future_extended_info'].values())


    def test_image(self):
        spot = Spot.objects.create(name="This is the test name")
        f = open("%s/resources/test_gif.gif" % TEST_ROOT)
        gif = SpotImage.objects.create(
            description="This is the GIF test",
            spot=spot,
            image=File(f))

        test_str = "{0}".format(gif)
        self.assertEqual(test_str, "This is the GIF test")
