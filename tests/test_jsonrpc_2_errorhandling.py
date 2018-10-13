"""
More tests for JSON-RPC 2.0.

Tests for JSON-RPC 2.0 that cover cases not defined as examples in the \
specification.
"""

import json
import pytest
import tornado

from .test_jsonrpc_2_spec import jsonrpc_fetch, test_url
from tornado_jsonrpc2 import JSONRPCHandler


@pytest.fixture
def app():
    def response():
        raise TypeError("Foobar")

    return tornado.web.Application([
        (r"/jsonrpc", JSONRPCHandler, {"response_creator": response}),
    ])


@pytest.mark.gen_test
def test_invalid_error_in_responder(jsonrpc_fetch):
    response = yield jsonrpc_fetch(
        body=json.dumps({"jsonrpc": "2.0", "method": "foo", "id": 1})
    )
    assert 200 == response.code

    response = json.loads(response.body)
    expected_response = {
        'jsonrpc': '2.0',
        'id': 1,
        'error': {
            'code': -32603,
            'message': "Internal error: response() takes 0 positional arguments but 1 was given"
        }
    }
    assert response == expected_response


@pytest.mark.gen_test
def test_invalid_request(jsonrpc_fetch):
    response = yield jsonrpc_fetch(
        body=json.dumps({"jsonrpc": "2.0", "id": 1})
    )
    assert 200 == response.code

    response = json.loads(response.body)
    expected_response = {
        'error': {
            'code': -32600,
            'message': "Invalid Request: Missing member 'method'"
        },
        'id': None,
        'jsonrpc': '2.0'
    }
    assert response == expected_response
