"""
More tests for JSON-RPC 2.0.

Tests for JSON-RPC 2.0 that cover cases not defined as examples in the \
specification.
"""

from .test_jsonrpc_2_spec import app, jsonrpc_fetch, test_url

import json
import pytest


@pytest.mark.gen_test
def test_invalid_parameter_type(jsonrpc_fetch):
    request = {
        "jsonrpc": "2.0",
        "method": "foo",
        "params": "nope",  # Has to be list or dict
        "id": 1
    }
    response = yield jsonrpc_fetch(
        body=json.dumps(request)
    )
    assert 200 == response.code

    response = json.loads(response.body)

    expected_response = {
        'jsonrpc': '2.0',
        'id': 1,
        'error': {
            'code': -32600,
            'message': 'Invalid Request: Invalid type for "params"!'
        }
    }
    assert response == expected_response
