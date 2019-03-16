from tornado.escape import json_encode
from tornado.web import RequestHandler

from .jsonrpc import decode
from .exceptions import (
    JSONRPCError, ParseError, InvalidRequest, MethodNotFound,
    InvalidParams, InternalError, EmptyBatchRequest)

__all__ = ("BasicJSONRPCHandler", "JSONRPCHandler")


class BasicJSONRPCHandler(RequestHandler):
    def initialize(self, version=None):
        self.version = version

    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json')

    async def handle_jsonrpc(self, request):
        request = self.decode_jsonrpc_request(request)
        if not request:
            return

        await self.process_jsonrpc_request(request)

    def decode_jsonrpc_request(self, request):
        try:
            return decode(request.body, version=self.version)
        except (InvalidRequest, ParseError, EmptyBatchRequest) as error:
            self.write(self.exception_to_jsonrpc(error))

    async def process_jsonrpc_request(self, request):
        if isinstance(request, list):  # batch request
            responses = await self.process_jsonrpc_batch_request(request)
            if responses:
                # Twisted won't write lists for security reasons
                # see http://www.tornadoweb.org/en/stable/web.html#tornado.web.RequestHandler.write
                self.write(json_encode(responses))
        else:
            message = await self.process_jsonrpc_single_request(request)
            if message:
                self.write(message)

    async def process_jsonrpc_batch_request(self, request):
        responses = []
        for call in request:
            if isinstance(call, JSONRPCError):
                responses.append(self.exception_to_jsonrpc(call))
                continue

            message = await self.create_jsonrpc_response(call)
            if message:
                responses.append(message)

        return responses

    async def process_jsonrpc_single_request(self, request):
        return await self.create_jsonrpc_response(request)

    async def create_jsonrpc_response(self, request):
        try:
            request.validate()
        except InvalidRequest as error:
            return self.exception_to_jsonrpc(error, request)

        try:
            method_result = await self.compute_result(request)
            if not request.is_notification:
                if request.version == '1.0':
                    return {"id": request.id,
                            "result": method_result,
                            "error": None}
                else:
                    return {"jsonrpc": "2.0",
                            "id": request.id,
                            "result": method_result}
        except (MethodNotFound, InvalidParams) as error:
            if not request.is_notification:
                return self.exception_to_jsonrpc(error, request)
        except Exception as error:
            if not request.is_notification:
                return self.exception_to_jsonrpc(InternalError(str(error)), request)

    def exception_to_jsonrpc(self, exception, request=None):
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
            # No version set and could not be determined from request
            # We want to answer with the latest version in that case.
            version = '2.0'

        error = {"code": exception.error_code,
                 "message": "{}: {}".format(exception.short_message,
                                            str(exception))}

        if version == '1.0':
            return {"id": request_id,
                    "result": None,
                    "error": error}
        else:
            return {"jsonrpc": "2.0",
                    "id": request_id,
                    "error": error}

    async def compute_result(self, request):
        raise NotImplementedError("Handler does not create an result.")


class JSONRPCHandler(BasicJSONRPCHandler):
    def initialize(self, response_creator, version=None):
        super().initialize(version=version)
        self.create_response = response_creator

    async def post(self):
        return await self.handle_jsonrpc(self.request)

    async def compute_result(self, request):
        return await self.create_response(request)
