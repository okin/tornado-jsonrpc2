import pytest
import functools
import tornado.web
from tornado.escape import json_encode, json_decode

from tornado_jsonrpc2.handler import JSONRPCHandler


@pytest.fixture
def app(request):
    async def version(request):
        print("Handling {!r}".format(request))
        return request.version

    return tornado.web.Application([
        (r"/jsonrpc", JSONRPCHandler, {"response_creator": version}),
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
async def test_mixing_handled_versions(jsonrpc_fetch):
    v1Request = {
        "method": "foo",
        "params": [],
        "id": 1
    }

    response = await jsonrpc_fetch(body=json_encode(v1Request))
    assert 200 == response.code
    response = json_decode(response.body)
    assert response['id'] == v1Request['id']
    assert not response['error']
    assert response['result'] == '1.0'

    v2Request = {
        "jsonrpc": "2.0",
        "method": "foo",
        "id": 2
    }
    response = await jsonrpc_fetch(body=json_encode(v2Request))
    assert 200 == response.code
    response = json_decode(response.body)
    assert response['id'] == v2Request['id']
    assert 'error' not in response
    assert response['result'] == '2.0'
