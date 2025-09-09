from contextlib import asynccontextmanager
from fastapi import FastAPI
from config.env import AppConfig
# from config.get_db import init_create_table
# from config.get_redis import RedisUtil
# from config.get_scheduler import SchedulerUtil  # todo: 定时任务
# from utils.common_util import worship
from utils.log_util import logger
from module_admin.controller.task_controller import taskController
from middlewares.trace_middleware import add_trace_middleware
from module_admin.service.task_service import ProcessManager

# 生命周期事件
# note: contextlib生命周期管理（启动前准备 → 运行 → 关闭清理）
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动阶段
    logger.info(f'{AppConfig.app_name}开始启动')
    
    try:
        # 初始化进程管理器
        ProcessManager.get_instance()
        
        # 记录启动成功日志
        logger.info(f'{AppConfig.app_name}启动成功')
        
        # 运行阶段
        yield
        
    except Exception as e:
        logger.error(f'{AppConfig.app_name}启动或运行过程中发生错误: {str(e)}')
        # 确保在异常情况下也能执行清理操作
        raise
    finally:
        # 关闭阶段
        try:
            # 获取进程管理器实例并关闭
            process_manager = ProcessManager.get_instance()
            process_manager.close()
            logger.info(f'{AppConfig.app_name}已成功关闭所有资源')
        except Exception as e:
            logger.error(f'{AppConfig.app_name}关闭资源时发生错误: {str(e)}')

# FastAPI核心对象初始化
app = FastAPI(
    title=AppConfig.app_name,  # 从配置读取应用名称
    description=f'{AppConfig.app_name}接口文档',  # 自动生成API文档描述
    version=AppConfig.app_version,  # 从配置读取版本号
    lifespan=lifespan,  # 挂载生命周期处理器
)

add_trace_middleware(app)  # 添加请求追踪中间件

# 加载路由列表
controller_list = [
    {'router': taskController, 'tags': ['系统监控-定时任务']},
]

for controller in controller_list:
    app.include_router(router=controller.get('router'), tags=controller.get('tags'))
