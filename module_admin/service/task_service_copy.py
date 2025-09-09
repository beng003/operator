import multiprocessing
from typing import Callable, Any, Dict, List, Optional
import concurrent.futures
import requests
import threading
import time
from utils.log_util import logger
from config.env import DAGSchedulerConfig
import traceback
from dataclasses import dataclass
import logging


DAGHttp = f"http://{DAGSchedulerConfig.dag_scheduler_host}:{DAGSchedulerConfig.dag_scheduler_port}"
multiprocessing.set_start_method("spawn", force=True)


@dataclass
class ProcessResult:
    """进程执行结果数据类"""

    success: bool
    result: Any
    error: Optional[str]
    process_time: float
    process_id: int


class ProcessManager:
    """
    进程管理类，用于统一管理所有的进程操作
    """

    complated_url = f"{DAGHttp}/scheduler/job_completed"
    stop_url = f"{DAGHttp}/scheduler/job/stop"

    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(
        self,
        max_workers: Optional[int] = None,
        logger: Optional[logging.Logger] = logger,
    ):
        """
        初始化进程管理器

        Args:
            max_workers: 最大工作进程数，默认为CPU核心数
            logger: 自定义日志记录器
        """
        # 防止多次初始化
        if ProcessManager._initialized:
            return

        self.max_workers = max_workers or multiprocessing.cpu_count()
        self.logger = logger or self._setup_default_logger()
        self.futures = {}
        self.executor = concurrent.futures.ProcessPoolExecutor(
            max_workers=self.max_workers
        )

        ProcessManager._initialized = True

    def __del__(self):
        """析构函数，确保资源被释放"""
        self.shutdown()

    @classmethod
    def get_instance(cls, *args, **kwargs):
        """获取单例实例（带参数初始化）"""
        if cls._instance is None:
            cls._instance = cls(*args, **kwargs)
        return cls._instance

    @staticmethod
    def _setup_default_logger() -> logging.Logger:
        """设置默认日志记录器"""
        logger = logging.getLogger("ProcessManager")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def _send_callback_notification(
        self,
        callback_url: str,
        job_uid: str,
        success: bool,
        error_detail: str = None,
    ) -> bool:
        """
        发送回调通知

        Args:
            callback_url: 回调URL
            job_uid: 任务唯一标识
            success: 是否成功
            error_detail: 错误详情

        Returns:
            是否成功发送通知
        """
        try:
            response = requests.post(
                callback_url,
                json={
                    "job_uid": job_uid,
                    "success": success,
                    "error_detail": error_detail,
                },
            )
            self.logger.info(f"回调通知已发送: {response.status_code}")
            return True
        except Exception as e:
            self.logger.error(f"发送回调通知失败: {str(e)}")

        return False

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
        job_uid = kwargs.pop("job_uid", None)
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
            self.logger.info(
                f"Process {process_id} completed in {process_time:.2f}s "
                f"with status: {'SUCCESS' if success else 'FAILED'}"
            )

            self._send_callback_notification(
                self.complated_url, job_uid, success, error
            )

            return {
                "success": success,
                "result": result,
                "error": error,
                "process_time": process_time,
                "process_id": process_id,
            }

    def execute_jobs(
        self,
        job_uid_list: List[str],
        jobs: List[Callable],
        args_list: Optional[List[tuple]] = None,
        kwargs_list: Optional[List[dict]] = None,
    ):
        """
        并行执行多个任务

        Args:
            job_uid_list: 任务唯一标识列表
            jobs: 要执行的任务函数列表
            args_list: 每个任务的位置参数列表，与jobs长度相同
            kwargs_list: 每个任务的关键字参数列表，与jobs长度相同
        """
        if not job_uid_list:
            return []
        if args_list is None:
            args_list = [()] * len(jobs)
        if kwargs_list is None:
            kwargs_list = [{}] * len(jobs)

        if (
            len(jobs) != len(args_list)
            or len(jobs) != len(kwargs_list)
            or len(jobs) != len(job_uid_list)
        ):
            raise ValueError(
                "jobs, args_list, kwargs_list and job_uid_list must have the same length"
            )

        self.logger.info(
            f"Starting execution of {len(jobs)} jobs with {self.max_workers} workers"
        )

        # 不使用with语句，因为executor是类的长期资源
        for job_uid, job, args, kwargs in zip(
            job_uid_list, jobs, args_list, kwargs_list
        ):
            kwargs["job_uid"] = job_uid
            future = self.executor.submit(self._worker_wrapper, job, *args, **kwargs)
            with self._lock:
                self.futures[job_uid] = future
            self.logger.debug(f"Submitted job {job.__name__} to process pool")

    def wait_for_completion(
        self, futures: List[concurrent.futures.Future] = None
    ) -> List[ProcessResult]:
        results = []
        # 收集结果
        for future in concurrent.futures.as_completed(self.futures.values()):
            try:
                result_data = future.result()
                results.append(ProcessResult(**result_data))
            except Exception as e:
                self.logger.error(f"Error retrieving process result: {str(e)}")
                results.append(
                    ProcessResult(
                        success=False,
                        result=None,
                        error=str(e),
                        process_time=0,
                        process_id=-1,
                    )
                )

        self.logger.info(
            f"All jobs completed. Success: {sum(r.success for r in results)}/"
            f"Failed: {sum(not r.success for r in results)}"
        )

        return results

    def shutdown(self, wait: bool = True):
        """关闭进程池"""
        if hasattr(self, "executor") and self.executor:
            self.executor.shutdown(wait=wait)
            self.logger.info("Process pool has been shut down")

    def get_failed_results(self, results: List[ProcessResult]) -> List[ProcessResult]:
        """从结果列表中获取失败的任务"""
        return [r for r in results if not r.success]

    def get_successful_results(
        self, results: List[ProcessResult]
    ) -> List[ProcessResult]:
        """从结果列表中获取成功的任务"""
        return [r for r in results if r.success]
