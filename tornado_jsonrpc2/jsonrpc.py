import json
from .exceptions import InvalidRequest, ParseError, EmptyBatchRequest

SUPPORTED_VERSIONS = {'2.0', '1.0'}


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
        version = request.get('jsonrpc', '1.0')
        if version == '2.0':
            return JSONRPC2Request(**request)
        elif version == '1.0':
            return JSONRPC1Request(**request)
        elif version not in SUPPORTED_VERSIONS:
            return JSONRPCRequest(**request)
    except KeyError as kerr:
        return InvalidRequest("Missing member {!s}".format(kerr))
    except InvalidRequest:
        raise
    except Exception as err:
        return InvalidRequest(str(err))


class JSONRPCRequest:
    def __init__(self, **kwargs):
        self._version = kwargs.get('jsonrpc', '1.0')
        self._method = kwargs['method']
        self._params = kwargs.get('params')
        self._id = kwargs.get('id')
        self._is_notification = False

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
        if self.version not in SUPPORTED_VERSIONS:
            raise InvalidRequest("Unsupported JSONRPC version!")

        if not isinstance(self._method, str):
            raise InvalidRequest('"method" must be a string!')


class JSONRPC1Request(JSONRPCRequest):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if 'id' not in kwargs:
            raise InvalidRequest('Missing property "id"')

        if self._id is None:
            self._is_notification = True

    def validate(self):
        super().validate()

        if self.version != '1.0':
            raise ValueError("JSONRPC version has been changed")

        if not isinstance(self._params, list):
            raise InvalidRequest('Invalid type for "params"!')


class JSONRPC2Request(JSONRPCRequest):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if 'id' not in kwargs:
            self._is_notification = True

    def validate(self):
        super().validate()

        if self.version != '2.0':
            raise ValueError("JSONRPC version has been changed")

        if (self._params is not None and
           not isinstance(self._params, (list, dict))):

            raise InvalidRequest('Invalid type for "params"!')
