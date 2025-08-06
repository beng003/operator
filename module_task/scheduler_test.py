from datetime import datetime
from module_task.decorator_task import capture_errors_to_queue

@capture_errors_to_queue
def job(*args, **kwargs):
    """
    定时任务执行同步函数示例
    """
    print(args)
    print(kwargs)
    # import time
    # time.sleep(200)
    print(1/0)
    
    print(f'{datetime.now()}同步函数执行了')


async def async_job(*args, **kwargs):
    """
    定时任务执行异步函数示例
    """
    print(args)
    print(kwargs)
    print(f'{datetime.now()}异步函数执行了')
