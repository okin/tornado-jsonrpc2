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


@pytest.fixture
def app():
    async def fail(jsonrpcrequest):
        raise RuntimeError("We should have never gotten here.")

    return tornado.web.Application([
        (r"/jsonrpc", JSONRPCHandler, {"response_creator": fail}),
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
        "params": "nope",  # Has to be list
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


@pytest.mark.gen_test
def test_request_with_missing_id(jsonrpc_fetch):
    request = {
        "method": "foo",
        "params": []
    }
    response = yield jsonrpc_fetch(body=json.dumps(request))
    assert 200 == response.code

    response = json.loads(response.body)
    print(response)

    expected_response = {
        'id': None,
        'result': None,
        'error': {
            'code': -32600,
            'message': 'Invalid Request: Missing property "id"!'
        }
    }
    assert 'jsonrpc' not in response, "Got a JSON-RPC 2.0 response"
    assert response == expected_response
