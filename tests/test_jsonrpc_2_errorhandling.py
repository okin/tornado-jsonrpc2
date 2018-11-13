"""
Errorhandling tests for JSONRPC 2.0.
"""

import pytest
import tornado
from tornado.escape import json_encode, json_decode

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
        body=json_encode({"jsonrpc": "2.0", "method": "foo", "id": 1})
    )
    assert 200 == response.code

    response = json_decode(response.body)
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
        body=json_encode({"jsonrpc": "2.0", "id": 1})
    )
    assert 200 == response.code

    response = json_decode(response.body)
    expected_response = {
        'error': {
            'code': -32600,
            'message': "Invalid Request: Missing member 'method'"
        },
        'id': None,
        'jsonrpc': '2.0'
    }
    assert response == expected_response


@pytest.mark.gen_test
def test_unsupported_jsonrpc_version(jsonrpc_fetch):
    response = yield jsonrpc_fetch(
        body=json_encode({"jsonrpc": "3000", "id": 1, "method": "foo"})
    )
    assert 200 == response.code

    response = json_decode(response.body)
    expected_response = {
        'error': {
            'code': -32600,
            'message': 'Invalid Request: Unsupported JSONRPC version!'
        },
        'id': 1,
        'jsonrpc': '2.0'
    }
    assert response == expected_response
