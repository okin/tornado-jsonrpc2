import tornado.web
from tornado.escape import json_encode, json_decode

import pytest

from tornado_jsonrpc2.handler import BasicJSONRPCHandler


@pytest.fixture
def app():
    class DummyHandler(BasicJSONRPCHandler):
        async def post(self):
            await self.handle_jsonrpc(self.request)

    return tornado.web.Application([
        (r"/dummy", DummyHandler),
    ])


@pytest.mark.gen_test
def test_compute_function_has_to_be_implemented_by_subclass(http_client, base_url):
    request = {"method": "foo",
               "params": [],
               "id": 1}

    response = yield http_client.fetch(base_url + '/dummy',
                                       method="POST",
                                       headers={'Content-Type': 'application/json'},
                                       body=json_encode(request))

    assert 200 == response.code
    jresponse = json_decode(response.body)

    assert 1 == jresponse['id']
    assert not jresponse['result']
    expected_error = {'code': -32603,
                      'message': 'Internal error: Handler does not create an result.'}
    assert jresponse['error'] == expected_error
