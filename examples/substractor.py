import functools
import tornado.web

from tornado_jsonrpc2.handler import JSONRPCHandler
from tornado_jsonrpc2.exceptions import MethodNotFound


class MyBackend:
    def subtract(self, minuend, subtrahend):
        return minuend - subtrahend


async def create_response(request, backend):
    try:
        method = getattr(backend, request.method)
    except AttributeError:
        raise MethodNotFound("Method {!r} not found!".format(request.method))

    try:
        params = request.params
    except AttributeError:
        return method()

    if isinstance(params, list):
        return method(*params)
    elif isinstance(params, dict):
        return method(**params)


def make_app():
    simple_creator = functools.partial(create_response,
                                       backend=MyBackend())

    return tornado.web.Application([
        (r"/jsonrpc", JSONRPCHandler, {"response_creator": simple_creator}),
        (r"/jsonrpc1", JSONRPCHandler, {"version": "1.0",
                                        "response_creator": simple_creator}),
        (r"/jsonrpc2", JSONRPCHandler, {"version": "2.0",
                                        "response_creator": simple_creator}),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
