import json
from tornado.escape import json_decode
from .exceptions import InvalidRequest, ParseError, EmptyBatchRequest

SUPPORTED_VERSIONS = {'2.0', '1.0'}


def decode(request, version=None):
    try:
        obj = json_decode(request)
    except json.JSONDecodeError as jsonError:
        raise ParseError(str(jsonError))

    if isinstance(obj, list):  # Batch request
        requests = [process_request(data, version=version) for data in obj]
        if not requests:
            raise EmptyBatchRequest("Empty batch request")

        return requests
    else:  # Single request
        request = process_request(obj, version=version)
        if isinstance(request, Exception):
            raise request

        return request


def process_request(request, version=None):
    try:
        request_version = request.get('jsonrpc', '1.0')
        if version is not None and request_version != version:
            raise InvalidRequest("Refusing to handle version {}".format(request_version))

        if request_version == '2.0':
            return JSONRPC2Request(**request)
        elif request_version == '1.0':
            return JSONRPC1Request(**request)
        elif request_version not in SUPPORTED_VERSIONS:
            return JSONRPCRequest(**request)
    except KeyError as kerr:
        return InvalidRequest('Missing member {!s}'.format(kerr),
                              JSONRPCStyleRequest(**request))
    except InvalidRequest as inverr:
        return InvalidRequest(str(inverr), JSONRPCStyleRequest(**request))
    except Exception as err:
        return InvalidRequest(str(err))


class JSONRPCStyleRequest:

    def __init__(self, **kwargs):
        self._id = kwargs.get('id')
        self._method = kwargs.get('method')
        self._params = kwargs.get('params')
        self._version = kwargs.get('jsonrpc', '1.0')

    @property
    def id(self):
        return self._id

    @property
    def method(self):
        return self._method

    @property
    def params(self):
        return self._params

    @property
    def version(self):
        return self._version


class JSONRPCRequest(JSONRPCStyleRequest):
    """
    A request in style of JSON-RPC.

    This is a request not following of a specific version.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._method = kwargs['method']

        self._is_notification = False

    def __repr__(self):
        return '{}(version={!r}, method={!r}, params={!r}, id={!r})'.format(
            self.__class__.__name__, self._version, self._method, self._params, self._id)

    @property
    def id(self):
        return self._id

    @property
    def is_notification(self):
        return self._is_notification

    @property
    def params(self):
        if self._params is None:
            raise AttributeError("No params given.")

        return self._params

    @property
    def version(self):
        return self._version

    def validate(self):
        if self.version not in SUPPORTED_VERSIONS:
            raise InvalidRequest("Unsupported JSONRPC version!")

        if not isinstance(self._method, str):
            raise InvalidRequest('"method" must be a string!')


class JSONRPC1Request(JSONRPCRequest):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if 'id' not in kwargs:
            raise InvalidRequest('Missing member "id"')

        if self._id is None:
            self._is_notification = True

    def validate(self):
        super().validate()

        if not isinstance(self._params, list):
            raise InvalidRequest('Invalid type for "params"!')


class JSONRPC2Request(JSONRPCRequest):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if 'id' not in kwargs:
            self._is_notification = True

    def validate(self):
        super().validate()

        if (self._params is not None and
           not isinstance(self._params, (list, dict))):

            raise InvalidRequest('Invalid type for "params"!')
