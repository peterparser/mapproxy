# This file is part of the MapProxy project.
# Copyright (C) 2013 Omniscale <http://omniscale.de>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import random

import pytest

from mapproxy.cache.riak import RiakCache
from mapproxy.compat.modules import urlparse
from mapproxy.grid import tile_grid
from mapproxy.test.image import create_tmp_image_buf
from mapproxy.test.unit.test_cache_tile import TileCacheTestBase


tile_image = create_tmp_image_buf((256, 256), color='blue')
tile_image2 = create_tmp_image_buf((256, 256), color='red')


@pytest.mark.skipif(sys.version_info > (3, 7), reason="riak is not compatible with this Python version")
class RiakCacheTestBase(TileCacheTestBase):
    always_loads_metadata = True
    def setup(self):
        url = os.environ[self.riak_url_env]
        urlparts = urlparse.urlparse(url)
        protocol = urlparts.scheme.lower()
        node = {'host': urlparts.hostname}
        if ':' in urlparts.hostname:
            if protocol == 'pbc':
                node['pb_port'] = urlparts.port
            if protocol in ('http', 'https'):
                node['http_port'] = urlparts.port

        db_name = 'mapproxy_test_%d' % random.randint(0, 100000)

        TileCacheTestBase.setup(self)

        self.cache = RiakCache([node], protocol, db_name, tile_grid=tile_grid(3857, name='global-webmarcator'))

    def teardown(self):
        import riak
        bucket = self.cache.bucket
        for k in bucket.get_keys():
            riak.RiakObject(self.cache.connection, bucket, k).delete()
        TileCacheTestBase.teardown(self)
    
    def test_default_coverage(self):
        assert self.cache.coverage is None

    def test_double_remove(self):
        tile = self.create_tile()
        self.create_cached_tile(tile)
        assert self.cache.remove_tile(tile)
        assert self.cache.remove_tile(tile)


@pytest.mark.skipif(not os.environ.get('MAPPROXY_TEST_RIAK_HTTP'),
                    reason="MAPPROXY_TEST_RIAK_HTTP not set")
class TestRiakCacheHTTP(RiakCacheTestBase):
    riak_url_env = 'MAPPROXY_TEST_RIAK_HTTP'


@pytest.mark.skipif(not os.environ.get('MAPPROXY_TEST_RIAK_PBC'),
                    reason="MAPPROXY_TEST_RIAK_PBC not set")
class TestRiakCachePBC(RiakCacheTestBase):
    riak_url_env = 'MAPPROXY_TEST_RIAK_PBC'
