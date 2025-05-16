# -*- coding: utf-8 -*-
"""
@author: peng
@file: middle.py
@time: 2025/1/17  16:57
"""

from functools import wraps
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from .span import get_current_span, Span

# note: 添加中间件TraceASGIMiddleware
"""
整个http生命周期：
    request(before) --> request(after) --> response(before) --> response(after)
"""

class TraceASGIMiddleware:
    """
    fastapi-example:
        app = FastAPI()
        app.add_middleware(TraceASGIMiddleware)
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
    
    @staticmethod
    async def my_receive(receive: Receive, span: Span):
        # 重写receive方法
        # 1. 在请求前记录请求ID
        # 2. 在请求后记录请求参数，这里未做修改
        await span.request_before()

        @wraps(receive)
        async def my_receive():
            message = await receive()
            await span.request_after(message)
            return message

        return my_receive

    # note: 中间件的固定参数
    # scope: 请求上下文信息，包含请求类型、请求方法、请求路径等信息
    # receive: 接收请求消息的异步函数,执行之后会返回一个消息对象
    # send: 发送响应消息的异步函数
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return

        async with get_current_span(scope) as span:
            handle_outgoing_receive = await self.my_receive(receive, span)

            async def handle_outgoing_request(message: 'Message') -> None:
                # 重写send方法
                # 在响应前在消息中添加request-id
                await span.response(message)
                await send(message)

            await self.app(scope, handle_outgoing_receive, handle_outgoing_request)
