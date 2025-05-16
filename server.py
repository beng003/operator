from contextlib import asynccontextmanager
from fastapi import FastAPI
from config.env import AppConfig
# from config.get_db import init_create_table
# from config.get_redis import RedisUtil
# from config.get_scheduler import SchedulerUtil  # todo: 定时任务
from utils.common_util import worship
from utils.log_util import logger
from module_admin.controller.task_controller import taskController
from middlewares.trace_middleware import add_trace_middleware
from module_admin.service.task_service import ProcessManager
from fastapi import Request

# 生命周期事件
# note: contextlib生命周期管理（启动前准备 → 运行 → 关闭清理）
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动阶段
    logger.info(f'{AppConfig.app_name}开始启动')
    worship()  # 打印启动艺术字
    # await init_create_table()  # 初始化数据库表结构
    # app.state.redis = await RedisUtil.create_redis_pool()  # 创建Redis连接池
    logger.info(f'{AppConfig.app_name}启动成功')
    ProcessManager.get_instance().initialize()
    
    # 运行阶段
    yield
    
    # 关闭阶段
    # await RedisUtil.close_redis_pool(app)  # 关闭Redis连接池

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
