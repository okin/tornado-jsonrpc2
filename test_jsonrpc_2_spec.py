import json
import pytest
import functools
import tornado.web

from tornado_jsonrpc2.handler import JSONRPCHandler
from tornado_jsonrpc2.exceptions import MethodNotFound


class JSONRPCSpecBackend:
    """
    Test backend modeled after the JSON-RPC 2.0 soec,
    """
    def subtract(self, minuend, subtrahend):
        return minuend - subtrahend

    def update(self, one, two, three, four, five):
        print("Updated {}, {}, {}, {}, {}".format(one, two, three, four, five))

    def foobar2(self):
        # Used for notification test.
        pass

    def fail(self):
        raise ValueError("Ooops, something went wrong.")

    def sum(self, a, b, c):
        return a + b + c

    def get_data(self):
        return ["hello", 5]


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


@pytest.mark.parametrize("jrequest, expected_response", [
    [{"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": 1},
     {"jsonrpc": "2.0", "result": 19, "id": 1}],
    [{"jsonrpc": "2.0", "method": "subtract", "params": [23, 42], "id": 2},
     {"jsonrpc": "2.0", "result": -19, "id": 2}]
])
@pytest.mark.gen_test
def testRPCWithConditionalParameters(jsonrpc_fetch, jrequest, expected_response):
    response = yield jsonrpc_fetch(
        body=json.dumps(jrequest)
    )
    assert 200 == response.code

    json_response = json.loads(response.body)
    assert json_response == expected_response


@pytest.mark.parametrize("jrequest, expected_response", [
    [{"jsonrpc": "2.0", "method": "subtract", "params": {"subtrahend": 23, "minuend": 42}, "id": 3},
     {"jsonrpc": "2.0", "result": 19, "id": 3}],
    [{"jsonrpc": "2.0", "method": "subtract", "params": {"minuend": 42, "subtrahend": 23}, "id": 4},
     {"jsonrpc": "2.0", "result": 19, "id": 4}]
])
@pytest.mark.gen_test
def testRPCWithNamedParameters(jsonrpc_fetch, jrequest, expected_response):
    response = yield jsonrpc_fetch(
        body=json.dumps(jrequest)
    )
    assert 200 == response.code

    json_response = json.loads(response.body)
    assert json_response == expected_response


@pytest.mark.parametrize("notification_request", [
    {"jsonrpc": "2.0", "method": "update", "params": [1, 2, 3, 4, 5]},
    {"jsonrpc": "2.0", "method": "foobar"}
])
@pytest.mark.gen_test
def testRPCNotification(jsonrpc_fetch, notification_request):
    response = yield jsonrpc_fetch(
        body=json.dumps(notification_request)
    )
    assert 200 == response.code
    assert not response.body  # nothing returned for notification


@pytest.mark.gen_test
def testNonExistingMethod(jsonrpc_fetch):
    response = yield jsonrpc_fetch(
        raise_error=False,
        body=json.dumps({"jsonrpc": "2.0", "method": "foobar", "id": "1"})
    )

    json_response = json.loads(response.body)

    # tornado_jsonrpc2 uses a more detailed response and therefore this isn't
    # the exact return value as found in the specification.
    rmessage = json_response["error"].pop('message')
    emessage = "Method not found"
    assert rmessage.startswith(emessage)

    assert json_response == {"jsonrpc": "2.0", "error": {"code": -32601}, "id": "1"}


@pytest.mark.gen_test
def testCallWithInvalidJSON(jsonrpc_fetch):
    response = yield jsonrpc_fetch(
        raise_error=False,
        body='{"jsonrpc": "2.0", "method": "foobar, "params": "bar", "baz]'
    )

    json_response = json.loads(response.body)

    # tornado_jsonrpc2 uses a more detailed response and therefore this isn't
    # the exact return value as found in the specification.
    rmessage = json_response["error"].pop('message')
    emessage = "Parse error"
    assert rmessage.startswith(emessage)

    assert json_response == {"jsonrpc": "2.0", "error": {"code": -32700}, "id": None}


@pytest.mark.gen_test
def testCallWithInvalidRequest(jsonrpc_fetch):
    response = yield jsonrpc_fetch(
        raise_error=False,
        body=json.dumps({"jsonrpc": "2.0", "method": 1, "params": "bar"})
    )

    json_response = json.loads(response.body)

    # tornado_jsonrpc2 uses a more detailed response and therefore this isn't
    # the exact return value as found in the specification.
    rmessage = json_response["error"].pop('message')
    emessage = "Invalid Request"
    assert rmessage.startswith(emessage)

    assert json_response == {"jsonrpc": "2.0", "error": {"code": -32600}, "id": None}


@pytest.mark.gen_test
def testBatchCallWithInvalidJSON(jsonrpc_fetch):
    response = yield jsonrpc_fetch(
        raise_error=False,
        body='''[
  {"jsonrpc": "2.0", "method": "sum", "params": [1,2,4], "id": "1"},
  {"jsonrpc": "2.0", "method"
]'''
    )

    json_response = json.loads(response.body)

    # tornado_jsonrpc2 uses a more detailed response and therefore this isn't
    # the exact return value as found in the specification.
    rmessage = json_response["error"].pop('message')
    emessage = "Parse error"
    assert rmessage.startswith(emessage)

    assert json_response == {"jsonrpc": "2.0", "error": {"code": -32700}, "id": None}


@pytest.mark.gen_test
def testEmptyBatchCall(jsonrpc_fetch):
    response = yield jsonrpc_fetch(
        raise_error=False,
        body='[]'
    )

    json_response = json.loads(response.body)

    # tornado_jsonrpc2 uses a more detailed response and therefore this isn't
    # the exact return value as found in the specification.
    rmessage = json_response["error"].pop('message')
    emessage = "Invalid Request"
    assert rmessage.startswith(emessage)

    assert json_response == {"jsonrpc": "2.0", "error": {"code": -32600}, "id": None}


@pytest.mark.gen_test
def testBatchCallWithInvalidRequest(jsonrpc_fetch):
    response = yield jsonrpc_fetch(
        raise_error=False,
        body='[1]'
    )

    json_response = json.loads(response.body)

    assert isinstance(json_response, list)
    assert 1 == len(json_response)
    json_response = json_response[0]

    # tornado_jsonrpc2 uses a more detailed response and therefore this isn't
    # the exact return value as found in the specification.
    rmessage = json_response["error"].pop('message')
    emessage = "Invalid Request"
    assert rmessage.startswith(emessage)

    assert json_response == {"jsonrpc": "2.0", "error": {"code": -32600}, "id": None}


@pytest.mark.gen_test
def testBatchCallWithInvalidRequests(jsonrpc_fetch):
    response = yield jsonrpc_fetch(
        raise_error=False,
        body='[1,2,3]'
    )

    json_responses = json.loads(response.body)

    assert isinstance(json_responses, list)
    assert 3 == len(json_responses)

    # All results are the same
    for json_response in json_responses:
        # tornado_jsonrpc2 uses a more detailed response and therefore this
        # isn't the exact return value as found in the specification.
        rmessage = json_response["error"].pop('message')
        emessage = "Invalid Request"
        assert rmessage.startswith(emessage)

        assert json_response == {"jsonrpc": "2.0", "error": {"code": -32600}, "id": None}


@pytest.mark.gen_test
def testBatchCall(jsonrpc_fetch):
    response = yield jsonrpc_fetch(
        raise_error=False,
        body='''[
    {"jsonrpc": "2.0", "method": "sum", "params": [1,2,4], "id": "1"},
    {"jsonrpc": "2.0", "method": "notify_hello", "params": [7]},
    {"jsonrpc": "2.0", "method": "subtract", "params": [42,23], "id": "2"},
    {"foo": "boo"},
    {"jsonrpc": "2.0", "method": "foo.get", "params": {"name": "myself"}, "id": "5"},
    {"jsonrpc": "2.0", "method": "get_data", "id": "9"}
]'''
    )

    json_responses = json.loads(response.body)

    assert isinstance(json_responses, list)
    assert 5 == len(json_responses)

    expected_responses = [
        {"jsonrpc": "2.0", "result": 7, "id": "1"},
        {"jsonrpc": "2.0", "result": 19, "id": "2"},
        {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}, "id": None},
        {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": "5"},
        {"jsonrpc": "2.0", "result": ["hello", 5], "id": "9"}
    ]

    for json_response in json_responses:
        print("Searching match for {}".format(json_response))
        for expected_response in expected_responses:
            if json_response['id'] == expected_response['id']:
                if 'error' in json_response:
                    # tornado_jsonrpc2 uses a more detailed response and
                    # therefore this isn't the exact return value as
                    # found in the specification.
                    rmessage = json_response["error"].pop('message')
                    try:
                        emessage = expected_response['error'].pop('message')
                    except KeyError:
                        print("expected_response: {}".format(expected_response))
                        raise

                    assert rmessage.startswith(emessage)

                    assert json_response == expected_response
                else:
                    assert expected_response == json_response

                break
        else:
            raise RuntimeError("No response with matching for {} found!".format(json_response))


@pytest.mark.gen_test
def testNotificationOnlyBatchCall(jsonrpc_fetch):
    response = yield jsonrpc_fetch(
        raise_error=False,
        body='''[
    {"jsonrpc": "2.0", "method": "notify_sum", "params": [1,2,4]},
    {"jsonrpc": "2.0", "method": "notify_hello", "params": [7]}
]''')

    assert not response.body
