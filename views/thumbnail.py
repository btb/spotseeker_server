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

    Changes
    =================================================================

    sbutler1@illinois.edu: move some of the URL parameter parsing into
        here to simplify the URL patterns; adapt to the new RESTDispatch
        framework.
"""

from spotseeker_server.views.rest_dispatch import RESTDispatch, RESTException
from spotseeker_server.models import SpotImage, Spot
from django.http import HttpResponse
from django.utils.http import http_date
from spotseeker_server.require_auth import *
from cStringIO import StringIO
from django.core.cache import cache
import simplejson as json
import Image
import time
import re

RE_WIDTH = re.compile(r'width:(\d+)')
RE_HEIGHT = re.compile(r'height:(\d+)')
RE_WIDTHxHEIGHT = re.compile(r'^(\d+)x(\d+)$')

def get_width_height(img, thumb_dimensions, constrain):
    thumb_width = None
    thumb_height = None
    if constrain is True:
        m = RE_WIDTH.search(thumb_dimensions)
        if m:
            thumb_width = m.group(1)
        m = RE_HEIGHT.search(thumb_dimensions)
        if m:
            thumb_height = m.group(1)

        if thumb_width is None and thumb_height is None:
            raise RESTException("Image constraints required", 400)
        elif thumb_width is None:
            thumb_width = img.width * (float(thumb_height) / float(img.height))
        elif thumb_height is None:
            thumb_height = img.height * (float(thumb_width) / float(img.width))
    else:
        m = RE_WIDTHxHEIGHT.match(thumb_dimensions)
        if not m:
            raise RESTException("Image constraints required", 400)
        else:
            thumb_width = m.group(1)
            thumb_height = m.group(2)

    thumb_width = int(thumb_width)
    thumb_height = int(thumb_height)

    return thumb_width, thumb_height

def get_image_thumbnail(spot_image, thumb_width, thumb_height, constrain):
    image = spot_image.image
    im = Image.open(image.path)

    if constrain is True:
        im.thumbnail((thumb_width, thumb_height, Image.ANTIALIAS))
        thumb = im
    else:
        thumb = im.resize((thumb_width, thumb_height), Image.ANTIALIAS)

    return thumb

class ThumbnailView(RESTDispatch):
    """ Returns 200 with a thumbnail of a SpotImage.
    """
    @app_auth_required
    def GET(self, request, spot_id, image_id, thumb_dimensions=None, constrain=False):
        img = SpotImage.objects.get(pk=image_id)
        spot = img.spot

        if int(spot.pk) != int(spot_id):
            raise RESTException("Image Spot ID doesn't match spot id in url", 404)

        if thumb_dimensions is None:
            raise RESTException("Image constraints required", 400)

        thumb_width, thumb_height = get_width_height(img, thumb_dimensions, constrain)

        if thumb_height <= 0 or thumb_width <= 0:
            raise RESTException("Bad image constraints", 400)

        thumb = get_image_thumbnail(img, thumb_width, thumb_height, constrain)
        tmp = StringIO()
        thumb.save(tmp, thumb.format, quality=95)
        tmp.seek(0)

        response = HttpResponse(tmp.getvalue(), content_type=img.content_type)
        # 7 day timeout?
        response['Expires'] = http_date(time.time() + 60 * 60 * 24 * 7)
        return response

class MultiThumbnailView(RESTDispatch):

    def build_response(self, image_data, offsets):
        response = HttpResponse(image_data, content_type='image/jpeg')
        # 7 day timeout?
        response['Expires'] = http_date(time.time() + 60 * 60 * 24 * 7)
        response['Sprite-Offsets'] = offsets
        return response

    """ Returns 200 with a thumbnail of a SpotImage.
    """
    @app_auth_required
    def GET(self, request, image_ids, thumb_dimensions=None, constrain=False):

        cached_image = cache.get('multi_image_%s' % image_ids)
        cached_offsets = cache.get('multi_image_offsets_%s' % image_ids)

        if cached_image and cached_offsets:
            return self.build_response(cached_image, cached_offsets)

        thumbnails = {}
        width = 0
        height = 0

        offset_data = []

        for image_id in image_ids.split(","):
            img = SpotImage.objects.get(pk=image_id)
            spot = img.spot

            thumb_width, thumb_height = get_width_height(img, thumb_dimensions, constrain)

            if thumb_width > width:
                width = thumb_width

            offset_data.append([0, thumb_width, height, height + thumb_height])
            height = height + thumb_height

            if thumb_dimensions is None:
                raise RESTException("Image constraints required", 400)

            if thumb_height <= 0 or thumb_width <= 0:
                raise RESTException("Bad image constraints", 400)

            thumb = get_image_thumbnail(img, thumb_width, thumb_height, constrain)

            thumbnails[image_id] = thumb

        total_image = Image.new("RGB", (width, height))

        running_height = 0
        for image_id in thumbnails:
            total_image.paste(thumbnails[image_id], (0, running_height))
            running_height += thumbnails[image_id].size[1]

        tmp = StringIO()
        total_image.save(tmp, 'jpeg', quality=95)
        tmp.seek(0)

        cache.set('multi_image_%s' % image_ids, tmp.getvalue())
        cache.set('multi_image_offsets_%s' % image_ids, json.dumps(offset_data, separators=(',',':')))

        return self.build_response(tmp.getvalue(), json.dumps(offset_data, separators=(',',':')))

