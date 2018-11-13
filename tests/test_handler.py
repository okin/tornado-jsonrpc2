import pytest
import functools
import tornado.web
from tornado.escape import json_encode, json_decode

from tornado_jsonrpc2.handler import JSONRPCHandler


@pytest.fixture(params=["1.0", "2.0"])
def app(request):
    async def noop():
        pass

    return tornado.web.Application([
        (r"/jsonrpc", JSONRPCHandler, {"response_creator": noop,
                                       "version": request.param}),
    ])


@pytest.fixture
def test_url(base_url):
    return base_url + '/jsonrpc'


@pytest.fixture
def jsonrpc_fetch(http_client, test_url):
    return functools.partial(
        http_client.fetch,
        test_url,
        method="POST",
        headers={'Content-Type': 'application/json'},
    )


@pytest.mark.gen_test
def test_calling_with_unsupported_version(app, jsonrpc_fetch):
    response = yield jsonrpc_fetch(
        raise_error=False,
        body=json_encode({"jsonrpc": "3000", "method": "foobar", "id": "1"})
    )
    assert 200 == response.code

    json_response = json_decode(response.body)
    expected_error = {'code': -32600,
                      'message': 'Invalid Request: Refusing to handle version 3000'}
    assert json_response['error'] == expected_error
