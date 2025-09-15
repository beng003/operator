import os
import signal
import multiprocessing
import threading
import time
import datetime
from typing import Callable, Any, Dict, List, Optional
import traceback
import requests
from utils.log_util import logger
from config.env import DAGSchedulerConfig, AppConfig

class ProcessManager:
    """
    进程管理类，用于统一管理所有的进程操作
    """
    
    _instance = None
    _lock = threading.RLock()  # 类级别的锁，用于单例模式

    DAGHttp = f"http://{DAGSchedulerConfig.dag_scheduler_host}:{DAGSchedulerConfig.dag_scheduler_port}"
    stop_url = f"{DAGHttp}/scheduler/task/stop"

    def __new__(cls):
        """单例模式实现"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ProcessManager, cls).__new__(cls)
                cls._instance._initialize_instance()
                # 移除这里的Manager创建，移到initialize方法中
                # cls._instance._manager = multiprocessing.Manager()
        return cls._instance

    def _initialize_instance(self):
        """初始化实例变量"""
        self._running_processes = {}
        self._instance_lock = threading.RLock()

    def close(self):
        # 先停止所有进程
        self.stop_all_processes()
        
    def __del__(self):
        """析构函数"""
        self.close()

    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def start_process(
        self,
        job_uid: str,
        function,
        args: List = None,
        kwargs: Dict = None,
        job_info: Any = None,
    ) -> Dict:
        """
        启动一个新进程

        Args:
            job_uid: 任务唯一标识
            function: 要执行的函数
            args: 位置参数
            kwargs: 关键字参数
            job_info: 任务相关信息

        Returns:
            进程信息字典
        """
        with self._instance_lock:
            if job_uid in self._running_processes:
                logger.warning(f"任务 {job_uid} 已在运行中")
                return self._running_processes[job_uid]

        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        kwargs["job_uid"] = job_uid

        # 创建并启动进程
        process = multiprocessing.Process(target=worker_wrapper, args=(function, *args), kwargs=kwargs)
        process.start()

        # 记录进程信息
        process_info = {
            "process": process,
            "pid": process.pid,
            "job": job_info,
            "start_time": datetime.datetime.now().timestamp()  # 使用当前时间戳作为启动时间
        }

        # 存储进程信息
        with self._instance_lock:
            self._running_processes[job_uid] = process_info

        logger.info(f"已在进程 {process.pid} 中启动任务 {job_uid}")
        return process_info

    def stop_process(self, job_uid: str, timeout: int = 5) -> bool:
        """
        改进的进程停止方法
        """
        process = None
        try:
            with self._instance_lock:
                if job_uid not in self._running_processes:
                    logger.warning(f"任务 {job_uid} 不在运行中")
                    return True

                process_info = self._running_processes[job_uid]
                process = process_info["process"]
                
                # 立即从字典中移除，避免竞争条件
                del self._running_processes[job_uid]

            # 尝试优雅终止
            if process.is_alive():
                process.terminate()
                process.join(timeout=timeout)

                # 如果仍然运行，强制终止
                if process.is_alive():
                    try:
                        os.kill(process.pid, signal.SIGKILL)
                        process.join(timeout=1)
                    except ProcessLookupError:
                        pass  # 进程可能已经结束

            # 确保进程资源被清理
            if hasattr(process, 'close'):
                process.close()
                
            # 发送任务停止通知
            send_callback_notification(self.stop_url, job_uid, False, "任务被手动停止")
            
            logger.info(f"任务 {job_uid} 已停止")
            return True
            
        except Exception as e:
            logger.error(f"停止任务 {job_uid} 失败: {str(e)}")
            # 确保即使出错也清理资源
            if process and hasattr(process, 'close'):
                try:
                    process.close()
                except:
                    pass
            return False

    def stop_all_processes(self, timeout: int = 5) -> Dict[str, bool]:
        """
        停止所有运行中的进程

        Args:
            timeout: 等待进程结束的超时时间（秒）

        Returns:
            任务ID与停止结果的映射
        """
        results = {}
        with self._instance_lock:
            job_uids = list(self._running_processes.keys())

        for job_uid in job_uids:
            results[job_uid] = self.stop_process(job_uid, timeout)

        return results

    def get_process_info(self, job_uid: str) -> Optional[Dict]:
        """
        获取指定进程的信息

        Args:
            job_uid: 任务唯一标识

        Returns:
            进程信息字典，如果不存在则返回None
        """
        with self._instance_lock:
            process_info = self._running_processes.get(job_uid)
            if process_info:
                # 返回副本以避免外部修改
                return process_info.copy()
            return None

    def get_all_processes(self) -> Dict[str, Dict]:
        """
        获取所有运行中的进程信息

        Returns:
            所有进程信息的字典
        """
        with self._instance_lock:
            # 返回所有进程信息的深拷贝
            return {uid: info.copy() for uid, info in self._running_processes.items()}

    def is_process_running(self, job_uid: str) -> bool:
        """
        检查指定的进程是否正在运行

        Args:
            job_uid: 任务唯一标识

        Returns:
            进程是否正在运行
        """
        with self._instance_lock:
            if job_uid not in self._running_processes:
                return False

            process_info = self._running_processes[job_uid]
            process = process_info["process"]

        return process.is_alive()

def worker_wrapper(func: Callable, *args, **kwargs) -> Dict[str, Any]:
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
        logger.error(f"Process {process_id} failed: {error}")
    finally:
        process_time = time.time() - start_time
        logger.info(
            f"Process {process_id} completed in {process_time:.2f}s "
            f"with status: {'SUCCESS' if success else 'FAILED'}"
        )

        # 获取complated_url

        
        send_callback_notification(job_uid, success, error)
        send_delete_notification(job_uid)

        return {
            "success": success,
            "result": result,
            "error": error,
            "process_time": process_time,
            "process_id": process_id,
        }


def send_callback_notification(
    job_uid: str,
    success: bool,
    error_detail: str = None,
) -> bool:
    """
    发送回调通知

    Args:
        job_uid: 任务唯一标识
        success: 是否成功
        error_detail: 错误详情

    Returns:
        是否成功发送通知
    """
    DAGHttp = f"http://{DAGSchedulerConfig.dag_scheduler_host}:{DAGSchedulerConfig.dag_scheduler_port}"
    callback_url = f"{DAGHttp}/scheduler/job_completed"
    
    try:
        response = requests.post(
            callback_url,
            json={
                "job_uid": job_uid,
                "success": success,
                "error_detail": error_detail,
            },
            timeout=10  # 添加超时设置
        )
        logger.info(f"回调通知已发送: {response.status_code}")
        return True
    except Exception as e:
        logger.error(f"发送回调通知失败: {str(e)}")
        return False

def send_delete_notification(
    job_uid: str,
) -> bool:
    """
    发送删除通知

    Args:
        callback_url: 回调URL
        job_uid: 任务唯一标识

    Returns:
        是否成功发送通知
    """
    DAGHttp = f"http://127.0.0.1:{AppConfig.app_port}"
    callback_url = f"{DAGHttp}/operator/delete_job"
    
    try:
        response = requests.post(
            callback_url,
            params={"job_uid": job_uid},
            timeout=10  # 添加超时设置
        )
        logger.info(f"回调通知已发送: {response.status_code}")
        return True
    except Exception as e:
        logger.error(f"发送回调通知失败: {str(e)}")
        return False