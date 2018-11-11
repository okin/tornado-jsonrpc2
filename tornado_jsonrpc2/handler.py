import json
from tornado.web import RequestHandler
from .jsonrpc import decode
from .exceptions import (
    JSONRPCError, ParseError, InvalidRequest, MethodNotFound,
    InvalidParams, InternalError, EmptyBatchRequest)

__all__ = ("JSONRPCHandler", )


class JSONRPCHandler(RequestHandler):
    def initialize(self, response_creator, version=None):
        self.create_response = response_creator
        self.version = version

    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json')

    async def post(self):
        try:
            request = decode(self.request.body, version=self.version)
        except (InvalidRequest, ParseError, EmptyBatchRequest) as error:
            self.write(self.transform_exception(error))
            return

        if isinstance(request, list):  # batch request
            responses = []
            for call in request:
                if isinstance(call, JSONRPCError):
                    responses.append(self.transform_exception(call))
                    continue

                message = await self._get_return_message(call)
                if message:
                    responses.append(message)

            if responses:
                # Twisted won't write lists for security reasons
                # see http://www.tornadoweb.org/en/stable/web.html#tornado.web.RequestHandler.write
                self.write(json.dumps(responses))
        else:
            message = await self._get_return_message(request)
            if message:
                self.write(message)

    async def _get_return_message(self, request):
        try:
            request.validate()
        except InvalidRequest as error:
            return self.transform_exception(error, request)

        try:
            method_result = await self.create_response(request)
            if not request.is_notification:
                if request.version == '1.0':
                    return {
                        "id": request.id,
                        "result": method_result,
                        "error": None
                    }
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": request.id,
                        "result": method_result
                    }
        except (MethodNotFound, InvalidParams) as error:
            if not request.is_notification:
                return self.transform_exception(error, request)
        except Exception as error:
            if not request.is_notification:
                return self.transform_exception(InternalError(str(error)), request)

    def transform_exception(self, exception, request=None):
        assert isinstance(exception, JSONRPCError)

        try:
            request = exception.args[1]
            exception = exception.__class__(exception.args[0])
        except (IndexError, TypeError):
            pass

        try:
            request_id = request.id
        except AttributeError:
            request_id = None

        try:
            version = self.version or request.version
        except AttributeError:
            version = self.version

        if version == '1.0':
            return {
                "id": request_id,
                "result": None,
                "error": {
                    "code": exception.error_code,
                    "message": "{}: {}".format(exception.short_message, str(exception))
                }
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": exception.error_code,
                    "message": "{}: {}".format(exception.short_message, str(exception))
                }
            }
