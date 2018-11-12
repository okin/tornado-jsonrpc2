# 🐍🌪️ tornado-jsonrpc2

[![Build Status](https://travis-ci.org/okin/tornado-jsonrpc2.svg?branch=master)](https://travis-ci.org/okin/tornado-jsonrpc2)
[![codecov](https://codecov.io/gh/okin/tornado-jsonrpc2/branch/master/graph/badge.svg)](https://codecov.io/gh/okin/tornado-jsonrpc2)

A request handler for tornado that implements the [JSON-RPC 2.0 specification](https://www.jsonrpc.org/specification).

The aim is to have a spec-compliant handler that can be set up in a flexible way.


## Requirements

The current requirement for this is to have at least Python 3.6 and Tornado 5.


### Python

The usage of `json.JSONDecodeError` leads to the minimum version Python 3.6.

The usage of `async` / `await` means the lowest ever supported version will be Python 3.5.
While currently not in focus having this running on Python 3.5 may become an option.


## Usage

To allow for flexible configuration the `JSONRPCHandler` will have to be passed a parameter `response_creator` which takes an callable that the request in form will get passed to.
The request is an instance of `tornado_jsonrpc2.jsonrpc.JSONRPCRequest` with the attributes `method` and `params` (and `id` and `version` should they be required).

The following example shows how this can be used to execute methods on a backend instance.
By using functools we are able to create a function that only requires the request as an parameter.


```Python
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
        ])


    if __name__ == "__main__":
        app = make_app()
        app.listen(8888)
        tornado.ioloop.IOLoop.current().start()
```

You can access this example app on port 8888 with curl:

```
$ curl --insecure --data '{"jsonrpc": "2.0", "method": "subtract", "params": [5, 1], "id": 1}' http://localhost:8888/jsonrpc

{"jsonrpc": "2.0", "id": 1, "result": 4}
```

You can also name the parameters:
```
$ curl --insecure --data '{"jsonrpc": "2.0", "method": "subtract", "params": {"minuend": 5, "subtrahend": 1}, "id": 1}' http://localhost:8888/jsonrpc

{"jsonrpc": "2.0", "id": 1, "result": 4}
```