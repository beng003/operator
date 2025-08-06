a = 111
b=0

import logging
import traceback

logger = logging.getLogger(__name__)

try:
    print(a/b)
except Exception as exc:
    # 获取完整的错误信息
    error_detail =  traceback.format_exc()
    
    # 记录到日志
    logger.error(f"全局异常捕获: {error_detail}")
    



# print(a/b)
# logger = logging.getLogger(__name__)

# @app.middleware("http")
# async def global_exception_handler(request: Request, call_next):
#     try:
#         return await call_next(request)
#     except Exception as exc:
#         # 获取完整的错误信息
#         error_detail = {
#             "endpoint": str(request.url),
#             "method": request.method,
#             "exception_type": type(exc).__name__,
#             "detail": str(exc),
#             "traceback": traceback.format_exc().splitlines()
#         }
        
#         # 记录到日志
#         logger.error(f"全局异常捕获: {error_detail}")
        
#         # 返回结构化的错误信息
#         return JSONResponse(
#             status_code=500,
#             content={
#                 "error": "Internal Server Error",
#                 "detail": error_detail
#             }
#         )