# JSONRPC exception classes.
#
# From the JSON-RPC 2.0 spec:
# -32700  Parse error
#         Invalid JSON was received by the server.
#         An error occurred on the server while parsing the JSON text.
# -32600  Invalid Request
#         The JSON sent is not a valid Request object.
# -32601  Method not found
#         The method does not exist / is not available.
# -32602  Invalid params
#         Invalid method parameter(s).
# -32603  Internal error
#         Internal JSON-RPC error.
#
# -32000 to -32099 Server error
#         Reserved for implementation-defined server-errors.


class JSONRPCError(Exception):
    error_code = -1
    short_message = "This message should be overridden by subclass."


class ParseError(JSONRPCError):
    error_code = -32700
    short_message = "Parse error"


class InvalidRequest(JSONRPCError):
    error_code = -32600
    short_message = "Invalid Request"


class EmptyBatchRequest(InvalidRequest):
    # Non-standard variant used for handling empty requests.
    pass


class MethodNotFound(JSONRPCError):
    error_code = -32601
    short_message = "Method not found"


class InvalidParams(JSONRPCError):
    error_code = -32602
    short_message = "Invalid params"


class InternalError(JSONRPCError):
    error_code = -32603
    short_message = "Internal error"
