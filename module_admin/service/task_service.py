import os
import signal
import multiprocessing
from typing import Dict, Any, List, Optional
# import json
import requests
import threading
import time
from utils.log_util import logger
from config.env import DAGSchedulerConfig

DAGHttp = f"http://{DAGSchedulerConfig.dag_scheduler_host}:{DAGSchedulerConfig.dag_scheduler_port}"

class ProcessManager:
    """
    进程管理类，用于统一管理所有的进程操作
    """
    _instance = None
    _running_processes = {}
    _monitor_thread = None
    _monitor_running = False
    _lock = threading.RLock()  # 添加线程锁以保证线程安全
    complated_url = f"{DAGHttp}/scheduler/job_completed"
    stop_url = f"{DAGHttp}/scheduler/task/stop"

    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super(ProcessManager, cls).__new__(cls)
            # 不在这里启动监控线程，而是在显式调用时启动
        return cls._instance

    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def initialize(self):
        """显式初始化方法，只在服务器进程中调用"""
        self._start_monitor()
    
    def _start_monitor(self):
        """启动进程监控线程"""
        if self._monitor_thread is None or not self._monitor_thread.is_alive():
            self._monitor_running = True
            self._monitor_thread = threading.Thread(target=self._monitor_processes, daemon=True)
            self._monitor_thread.start()
            logger.info("进程监控线程已启动")
    
    def _monitor_processes(self):
        """监控进程状态，清理已结束的进程"""
        while self._monitor_running:
            try:
                # 复制键列表以避免在迭代过程中修改字典
                with self._lock:
                    job_uids = list(self._running_processes.keys())
                
                for job_uid in job_uids:
                    try:
                        with self._lock:
                            if job_uid not in self._running_processes:
                                continue
                            
                            process_info = self._running_processes[job_uid]
                            process = process_info["process"]
                            
                            # 检查进程是否已结束
                            if not process.is_alive():
                                # 获取进程退出码（如果可用）
                                exit_code = process.exitcode
                                success = True if exit_code == 0 else False
                                
                                # 从运行中进程列表中移除
                                del self._running_processes[job_uid]
                                
                                # 发送回调通知
                                self._send_callback_notification(self.complated_url, job_uid, success)
                                
                                logger.info(f"任务 {job_uid} 已结束，已从进程列表中移除")
                    except Exception as e:
                        logger.error(f"监控任务 {job_uid} 时发生错误: {str(e)}")
                
                # 每隔一段时间检查一次
                time.sleep(5)
            except Exception as e:
                logger.error(f"进程监控线程发生错误: {str(e)}")
    
    def start_process(self, job_uid: str, function, args: List = None, kwargs: Dict = None, job_info: Any = None) -> Dict:
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
        if job_uid in self._running_processes:
            logger.warning(f"任务 {job_uid} 已在运行中")
            return self._running_processes[job_uid]
        
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
            
        # 创建并启动进程
        process = multiprocessing.Process(target=function, args=args, kwargs=kwargs)
        process.start()
        
        # 记录进程信息
        process_info = {
            "process": process,
            "pid": process.pid,
            "job": job_info,
            "start_time": multiprocessing.current_process()._config.get('start_time', None)
        }
        
        # 存储进程信息
        with self._lock:
            self._running_processes[job_uid] = process_info
        
        logger.info(f"已在进程 {process.pid} 中启动任务 {job_uid}")
        return process_info
    
    def stop_process(self, job_uid: str, timeout: int = 5) -> bool:
        """
        停止指定的进程
        
        Args:
            job_uid: 任务唯一标识
            timeout: 等待进程结束的超时时间（秒）
            
        Returns:
            是否成功停止进程
        """
        with self._lock:
            if job_uid not in self._running_processes:
                logger.warning(f"任务 {job_uid} 不在运行中")
                return True
                
            process_info = self._running_processes[job_uid]
            process = process_info["process"]
        
        try:
            # 尝试终止进程
            process.terminate()
            process.join(timeout=timeout)
            
            # hack: 强制结束进程
            # # 如果进程仍然运行，强制结束
            # if process.is_alive():
            #     os.kill(process.pid, signal.SIGKILL)
            
            with self._lock:
                # 从运行中进程列表中移除
                if job_uid in self._running_processes:
                    del self._running_processes[job_uid]
            
            # # 发送任务完成通知（如果有回调URL）
            # self._send_callback_notification(self.stop_url, job_uid, success)
            
            logger.info(f"任务 {job_uid} 已停止")
            return True
        except Exception as e:
            logger.error(f"停止任务 {job_uid} 失败: {str(e)}")
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
        return self._running_processes.get(job_uid)
    
    def get_all_processes(self) -> Dict[str, Dict]:
        """
        获取所有运行中的进程信息
        
        Returns:
            所有进程信息的字典
        """
        # 返回一个新的字典，避免外部修改内部状态
        return self._running_processes.copy()
    
    def is_process_running(self, job_uid: str) -> bool:
        """
        检查指定的进程是否正在运行
        
        Args:
            job_uid: 任务唯一标识
            
        Returns:
            进程是否正在运行
        """
        with self._lock:
            if job_uid not in self._running_processes:
                return False
                
            process_info = self._running_processes[job_uid]
            process = process_info["process"]
        
        return process.is_alive()
    
    def _send_callback_notification(self, callback_url: str, job_uid: str, success: bool) -> bool:
        """
        发送回调通知
        
        Args:
            job_uid: 任务唯一标识
            process_info: 进程信息
            status: 任务状态
            message: 通知消息
            
        Returns:
            是否成功发送通知
        """
        try:
            response = requests.post(
                callback_url,
                json={
                    "job_uid": job_uid,
                    "success": success,
                }
            )
            logger.info(f"回调通知已发送: {response.status_code}")
            return True
        except Exception as e:
            logger.error(f"发送回调通知失败: {str(e)}")
        
        return False
    
    def __del__(self):
        """析构函数，确保监控线程停止"""
        self._monitor_running = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1)