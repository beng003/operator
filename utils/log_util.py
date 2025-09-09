import os
import sys
import time
import os  # 添加缺失的导入
from loguru import logger as _logger
from typing import Dict
from middlewares.trace_middleware import TraceCtx

class LoggerInitializer:
    def __init__(self):
        self.log_path = os.path.join(os.getcwd(), 'logs')
        self.__ensure_log_directory_exists()
        self.log_path_error = os.path.join(self.log_path, f'{time.strftime("%Y-%m-%d")}_error.log')

    def __ensure_log_directory_exists(self):
        """确保日志目录存在，如果不存在则创建"""
        if not os.path.exists(self.log_path):
            os.mkdir(self.log_path)

    @staticmethod
    def __filter(log: Dict):
        """自定义日志过滤器，添加trace_id"""
        log['trace_id'] = TraceCtx.get_id()
        return log

    def init_log(self):
        """初始化日志配置"""
        # 自定义日志格式
        format_str = (
            '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | '
            '<cyan>{extra[trace_id]}</cyan> | '
            '<level>{level: <8}</level> | '
            '<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - '
            '<level>{message}</level>'
        )
        _logger.remove()
        
        # 使用loguru的extra功能代替filter注入trace_id
        _logger.configure(extra={"trace_id": "-"})
        
        # 输出到控制台
        _logger.add(sys.stderr, format=format_str, enqueue=True)
        # 输出到文件
        _logger.add(
            self.log_path_error,
            format=format_str,
            rotation='50MB',
            encoding='utf-8',
            enqueue=True,
            compression='zip',
        )

        return _logger

# 初始化日志处理器
log_initializer = LoggerInitializer()
logger = log_initializer.init_log()