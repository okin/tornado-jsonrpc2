"""
More tests for JSON-RPC 2.0.

Tests for JSON-RPC 2.0 that cover cases not defined as examples in the \
specification.
"""

import json
import pytest
import functools
import tornado.web
from tornado.escape import json_encode, json_decode

from tornado_jsonrpc2.handler import JSONRPCHandler
from tornado_jsonrpc2.exceptions import MethodNotFound


class JSONRPCSpecBackend:
    pass


async def create_response(jsonrpcrequest, backend):
    try:
        method = getattr(backend, jsonrpcrequest.method)
    except AttributeError:
        raise MethodNotFound("Method '{}' not found!".format(jsonrpcrequest.method))

    try:
        params = jsonrpcrequest.params
    except AttributeError:
        return method()

    if isinstance(params, list):
        return method(*params)
    elif isinstance(params, dict):
        return method(**params)
    else:
        raise RuntimeError("We should have never gotten here.")


@pytest.fixture
def app():
    simple_creator = functools.partial(create_response, backend=JSONRPCSpecBackend())

    return tornado.web.Application([
        (r"/jsonrpc", JSONRPCHandler, {"response_creator": simple_creator}),
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
def test_invalid_parameter_type(jsonrpc_fetch):
    request = {
        "method": "foo",
        "params": "nope",  # Has to be list or dict
        "id": 1
    }
    response = yield jsonrpc_fetch(body=json.dumps(request))
    assert 200 == response.code

    response = json.loads(response.body)

    expected_response = {
        'id': 1,
        'result': None,
        'error': {
            'code': -32600,
            'message': 'Invalid Request: Invalid type for "params"!'
        }
    }
    assert response == expected_response
