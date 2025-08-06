import functools
import traceback
from typing import Callable
from utils.log_util import logger

# 错误捕获装饰器
def capture_errors_to_queue(func: Callable):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):  # 修改1: 支持任意参数形式
        # 获取job_uid（必须通过关键字参数传递）
        job_uid = kwargs.get('job_uid')
        error_queue = kwargs.get('error_queue')        
        
        if job_uid is None or error_queue is None:
            logger.error("job_uid and error_queue must be provided as keyword argument")
            raise ValueError("Missing required job_uid or error_queue parameter")
        
        try:
            return func(*args, **kwargs)  # 修改2: 保持原有参数传递
        except Exception as exc:
            # 获取错误堆栈
            error_detail = traceback.format_exc()
            
            logger.debug(f"已记录任务 {job_uid} 的错误到队列")
            # 入队错误信息
            if hasattr(error_queue, 'put'):
                error_queue.put((job_uid, error_detail))
                logger.debug(f"已记录任务 {job_uid} 的错误到队列")
            
            raise exc
    return wrapper