import json
from .exceptions import InvalidRequest, ParseError, EmptyBatchRequest


def decode(request):
    try:
        obj = json.loads(request)
    except json.JSONDecodeError as jsonError:
        raise ParseError(str(jsonError))

    if isinstance(obj, list):  # Batch request
        requests = [process_request(data) for data in obj]
        if not requests:
            raise EmptyBatchRequest("Empty batch request")

        return requests
    else:  # Single request
        request = process_request(obj)
        if isinstance(request, Exception):
            raise request

        return request


def process_request(request):
    try:
        return JSONRPCRequest(**request)
    except KeyError as kerr:
        return InvalidRequest("Missing member {!s}".format(kerr))
    except Exception as err:
        return InvalidRequest(str(err))


class JSONRPCRequest:
    def __init__(self, **kwargs):
        self._version = kwargs.get('jsonrpc', 1.0)
        # TODO: check for supported version
        self._method = kwargs['method']

        try:
            self._id = kwargs['id']
            self._is_notification = False
        except KeyError:
            self._id = None
            self._is_notification = True

        self._params = kwargs.get('params')

    @property
    def version(self):
        return self._version

    @property
    def id(self):
        return self._id

    @property
    def method(self):
        return self._method

    @property
    def params(self):
        if self._params is None:
            raise AttributeError("No params given.")

        return self._params

    @property
    def is_notification(self):
        return self._is_notification

    def validate(self):
        if not isinstance(self._method, str):
            raise InvalidRequest("'method' must be a string!")

        if self._params is not None and not isinstance(self._params, (list, dict)):
            raise InvalidRequest("Invalid type for 'params'!")
