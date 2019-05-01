"""
Implementing a custom handler.

For testing you can use the following commands:
    * curl --insecure --data '{"id": "1", "method": "fast", "params": []}' http://localhost:8888/coolstuff
    * curl --insecure --data '{"id": "1", "method": "slow", "params": []}' http://localhost:8888/coolstuff
    * curl --insecure --data '{"id": "1", "method": "oops", "params": []}' http://localhost:8888/coolstuff
"""

import asyncio
import tornado.web

from tornado_jsonrpc2.handler import BasicJSONRPCHandler


class MyHandler(BasicJSONRPCHandler):
        async def post(self):
            await self.handle_jsonrpc(self.request)

        async def compute_result(self, request):
            if request.method == 'fast':
                await asyncio.sleep(1)
                return 'That was fast!'
            elif request.method == 'slow':
                await asyncio.sleep(10)
                return 'Doing the best I can...'
            else:
                raise RuntimeError("Oops, unhandled!")


def make_app():
    return tornado.web.Application([
        (r"/coolstuff", MyHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
