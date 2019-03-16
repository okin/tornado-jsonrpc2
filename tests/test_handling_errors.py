import pytest
import functools
import tornado.web
from tornado.escape import json_encode, json_decode

from tornado_jsonrpc2.handler import JSONRPCHandler


@pytest.fixture
def app(request):
    def noop():
        pass

    return tornado.web.Application([
        (r"/jsonrpc", JSONRPCHandler, {"response_creator": noop}),
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
def test_handling_an_error_without_given_version(app, jsonrpc_fetch):
    # Sending an invalid JSON string
    response = yield jsonrpc_fetch(
        raise_error=False,
        body='{"id": 1, "method": "irrelevant", "params": [}'
    )
    assert 200 == response.code

    json_response = json_decode(response.body)
    assert json_response['jsonrpc'] == '2.0'
    assert json_response['id'] == None
    error = json_response['error']
    assert error['code'] == -32700
    assert error['message'].startswith('Parse error:')
