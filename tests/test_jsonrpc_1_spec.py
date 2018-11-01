import json
import pytest
import functools
import tornado.web

from tornado_jsonrpc2.handler import JSONRPCHandler
from tornado_jsonrpc2.exceptions import MethodNotFound


class JSONRPCSpecBackend:
    """
    Test backend modeled after the JSON-RPC 1.0 spec.
    """
    def echo(self, message):
        return message

    def postMessage(self, message):
        return 1

    def handleMessage(self, who, message):
        pass

    def userLeft(sefl, who):
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


@pytest.mark.parametrize("client_request, expected_response", [
    [{"method": "echo", "params": ["Hello JSON-RPC"], "id": 1},
     {"result": "Hello JSON-RPC", "error": None, "id": 1}],
    [{"method": "postMessage", "params": ["Hello all!"], "id": 99},
     {"result": 1, "error": None, "id": 99}],
    [{"method": "postMessage", "params": ["I have a question:"], "id": 101},
     {"result": 1, "error": None, "id": 101}]
])
@pytest.mark.gen_test
def test_succesful_rpc(jsonrpc_fetch, client_request, expected_response):
    response = yield jsonrpc_fetch(body=json.dumps(client_request))
    assert 200 == response.code

    jresponse = json.loads(response.body)
    assert_response_conformity(jresponse)
    assert jresponse == expected_response


def assert_response_conformity(response):
    assert len(response) == 3, "Found additional elements in {}".format(response)
    assert 'result' in response
    assert 'error' in response
    assert 'id' in response


@pytest.mark.parametrize("client_request", [
    {"method": "handleMessage", "params": ["user1", "we were just talking"], "id": None},
    {"method": "handleMessage", "params": ["user3", "sorry, gotta go now, ttyl"], "id": None},
    {"method": "userLeft", "params": ["user3"], "id": None},
])
@pytest.mark.gen_test
def test_notification(jsonrpc_fetch, client_request):
    response = yield jsonrpc_fetch(body=json.dumps(client_request))
    assert 200 == response.code

    assert not response.body
