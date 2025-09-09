import multiprocessing
import concurrent.futures
from typing import Callable, Any, Dict, List, Optional
import traceback
import time
from dataclasses import dataclass
import logging

@dataclass
class ProcessResult:
    """进程执行结果数据类"""
    success: bool
    result: Any
    error: Optional[str]
    process_time: float
    process_id: int

class AsyncProcessManager:
    """异步进程管理类"""
    
    def __init__(self, max_workers: Optional[int] = None, logger: Optional[logging.Logger] = None):
        """
        初始化进程管理器
        
        Args:
            max_workers: 最大工作进程数，默认为CPU核心数
            logger: 自定义日志记录器
        """
        self.max_workers = max_workers or multiprocessing.cpu_count()
        self.logger = logger or self._setup_default_logger()
        self._executor = None
        
    @staticmethod
    def _setup_default_logger() -> logging.Logger:
        """设置默认日志记录器"""
        logger = logging.getLogger("AsyncProcessManager")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
        
    def _worker_wrapper(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """
        工作进程包装函数，用于捕获异常和记录执行时间
        
        Args:
            func: 要执行的函数
            args: 函数位置参数
            kwargs: 函数关键字参数
            
        Returns:
            包含执行结果的字典
        """
        process_id = multiprocessing.current_process().pid
        start_time = time.time()
        result = None
        error = None
        success = False
        
        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            error = f"{str(e)}\n{traceback.format_exc()}"
            self.logger.error(f"Process {process_id} failed: {error}")
        finally:
            process_time = time.time() - start_time
            self.logger.info(f"Process {process_id} completed in {process_time:.2f}s "
                           f"with status: {'SUCCESS' if success else 'FAILED'}")
            
            return {
                "success": success,
                "result": result,
                "error": error,
                "process_time": process_time,
                "process_id": process_id
            }
    
    def execute_tasks(
        self,
        tasks: List[Callable],
        args_list: Optional[List[tuple]] = None,
        kwargs_list: Optional[List[dict]] = None
    ) -> List[ProcessResult]:
        """
        并行执行多个任务
        
        Args:
            tasks: 要执行的任务函数列表
            args_list: 每个任务的位置参数列表，与tasks长度相同
            kwargs_list: 每个任务的关键字参数列表，与tasks长度相同
            
        Returns:
            包含所有任务执行结果的列表
        """
        if args_list is None:
            args_list = [()] * len(tasks)
        if kwargs_list is None:
            kwargs_list = [{}] * len(tasks)
            
        if len(tasks) != len(args_list) or len(tasks) != len(kwargs_list):
            raise ValueError("tasks, args_list and kwargs_list must have the same length")
            
        self.logger.info(f"Starting execution of {len(tasks)} tasks with {self.max_workers} workers")
        
        results = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            # 提交所有任务
            for task, args, kwargs in zip(tasks, args_list, kwargs_list):
                future = executor.submit(self._worker_wrapper, task, *args, **kwargs)
                futures.append(future)
                self.logger.debug(f"Submitted task {task.__name__} to process pool")
            
            # 收集结果
            for future in concurrent.futures.as_completed(futures):
                try:
                    result_data = future.result()
                    results.append(ProcessResult(**result_data))
                except Exception as e:
                    self.logger.error(f"Error retrieving process result: {str(e)}")
                    results.append(ProcessResult(
                        success=False,
                        result=None,
                        error=str(e),
                        process_time=0,
                        process_id=-1
                    ))
                    
        self.logger.info(f"All tasks completed. Success: {sum(r.success for r in results)}/"
                        f"Failed: {sum(not r.success for r in results)}")
        
        return results
    
    # 为 AsyncProcessManager 添加异步执行方法
    async def execute_tasks_async(
        self,
        tasks: List[Callable],
        args_list: Optional[List[tuple]] = None,
        kwargs_list: Optional[List[dict]] = None
    ) -> List[ProcessResult]:
        """异步执行多个任务"""
        import asyncio
        loop = asyncio.get_running_loop()
        # 使用线程池来执行同步的 execute_tasks 方法
        results = await loop.run_in_executor(
            None,  # 使用默认的线程池
            self.execute_tasks,
            tasks, args_list, kwargs_list
        )
        return results
    
    def get_failed_results(self, results: List[ProcessResult]) -> List[ProcessResult]:
        """从结果列表中获取失败的任务"""
        return [r for r in results if not r.success]
    
    def get_successful_results(self, results: List[ProcessResult]) -> List[ProcessResult]:
        """从结果列表中获取成功的任务"""
        return [r for r in results if r.success]
    
    
# 示例任务函数
def task_successful(x):
    import time
    time.sleep(100)
    return x * x

def task_failing():
    raise ValueError("Intentional error for demonstration")



if __name__ == "__main__":
    # 创建进程管理器
    manager = AsyncProcessManager(max_workers=2)
    
    # 准备任务
    tasks = [task_successful, task_successful, task_failing, task_successful]
    args_list = [(2,), (3,), (), (4,)]
    
    # 执行任务
    results = manager.execute_tasks(tasks, args_list)
    print("****************************************")
    # 分析结果
    print("\nExecution Summary:")
    for i, result in enumerate(results):
        # status = "SUCCESS" if result.success else "FAILED"
        # print(f"Task {i} ({status}): PID={result.process_id}, Time={result.process_time:.2f}s")
        # if not result.success:
        #     print(f"  Error: {result.error.splitlines()[0]}")
        print("=====================================================================")
        print(result)
    
    # 获取失败的任务
    failed = manager.get_failed_results(results)
    print(f"\nTotal failed tasks: {len(failed)}")