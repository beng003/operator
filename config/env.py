import argparse
import os
import sys
from dotenv import load_dotenv
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Literal


# # note: BaseSettings 自动获得以下核心功能：
# 1. 环境变量自动加载（支持.env文件和环境变量）
# 2. 类型验证（如app_port必须是int类型）
# 3. 嵌套配置支持（当前工程的JwtConfig等子配置）
# 4. 优先级管理（环境变量 > .env文件 > 类属性默认值）


class AppSettings(BaseSettings):
    """
    应用配置
    """

    app_env: str = "dev"
    app_name: str = "RuoYi-FasAPI"
    app_root_path: str = "/dev-api"
    app_host: str = "0.0.0.0"
    app_port: int = 8088
    app_version: str = "1.0.0"
    app_reload: bool = False
    app_ip_location_query: bool = True  # IP属地查询开关
    app_same_time_login: bool = True  # 多端登录控制

class DataBaseSettings(BaseSettings):
    """
    数据库配置
    """

    db_type: Literal["mysql", "postgresql"] = "mysql"
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_username: str = "root"
    db_password: str = "mysqlroot"
    db_database: str = "ruoyi-fastapi"
    db_echo: bool = True
    db_max_overflow: int = 10
    db_pool_size: int = 50
    db_pool_recycle: int = 3600
    db_pool_timeout: int = 30


class RedisSettings(BaseSettings):
    """
    Redis配置
    """

    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_username: str = ""
    redis_password: str = ""
    redis_database: int = 2

class DAGSchedulerSettings(BaseSettings):
    """
    DAGScheduler算子层配置
    """
    dag_scheduler_host: str = "127.0.0.1"
    dag_scheduler_port: int = 9099

class GetConfig:
    """
    获取配置
    """

    def __init__(self):
        self.parse_cli_args()

    @lru_cache()
    def get_app_config(self):
        """
        获取应用配置
        """
        # 实例化应用配置模型
        return AppSettings()

    @lru_cache()
    def get_database_config(self):
        """
        获取数据库配置
        """
        # 实例化数据库配置模型
        return DataBaseSettings()

    @lru_cache()
    def get_redis_config(self):
        """
        获取Redis配置
        """
        # 实例化Redis配置模型
        return RedisSettings()
    
    @lru_cache()
    def get_dag_scheduler_config(self):
        """
        获取算子层配置
        """
        # 实例化算子层配置模型
        return DAGSchedulerSettings()
    
    @staticmethod
    def parse_cli_args():
        """
        # note: argparse.ArgumentParser解析命令行参数，默认忽略大小写
        功能说明：
        1. 智能识别启动方式（uvicorn直接启动 或 自定义启动）
        2. 解析--env参数控制运行环境
        3. 自动加载对应环境的配置文件（.env.dev/.env.prod等）

        流程逻辑：
        if 通过uvicorn启动:
            保持uvicorn原生参数处理
        else:
            添加自定义参数解析（当前只支持--env）
        根据参数设置APP_ENV环境变量
        加载对应的.env环境文件
        """
        if "uvicorn" in sys.argv[0]:
            # 使用uvicorn启动时，命令行参数需要按照uvicorn的文档进行配置，无法自定义参数
            pass
        elif "pytest" in sys.argv[0] or any("pytest" in arg for arg in sys.argv):
            # 使用pytest运行测试时，不解析命令行参数
            # os.environ["APP_ENV"] = "test"
            pass
        else:
            # 使用argparse定义命令行参数
            parser = argparse.ArgumentParser(description="命令行参数")
            parser.add_argument("--env", type=str, default="", help="运行环境")
            # 解析命令行参数
            # args = parser.parse_args()
            # 设置环境变量，如果未设置命令行参数，默认APP_ENV为dev
            # os.environ["APP_ENV"] = args.env if args.env else "dev"
        # 读取运行环境
        run_env = os.environ.get("APP_ENV", "")
        # 运行环境未指定时默认加载.env.dev
        env_file = ".env.dev"
        
        # 运行环境不为空时按命令行参数加载对应.env文件
        if run_env != "":
            env_file = f".env.{run_env}"
            
        # 加载配置
        load_dotenv("./env/" + env_file)


# 实例化获取配置类
get_config = GetConfig()
# 应用配置
AppConfig = get_config.get_app_config()
# 数据库配置
DataBaseConfig = get_config.get_database_config()
# Redis配置
RedisConfig = get_config.get_redis_config()
# DAGScheduler算子层配置
DAGSchedulerConfig = get_config.get_dag_scheduler_config()
