from datetime import datetime
from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from config.get_db import get_db
from utils.log_util import logger
from utils.response_util import ResponseUtil
import time
from typing import List, Dict
from module_admin.models.job import Job
import json
import module_task
import multiprocessing
from pydantic import BaseModel
import requests
import os
import signal
from module_admin.service.task_service import ProcessManager

# 定义任务响应模型
class JobResponse(BaseModel):
    job_uid: str
    success: bool

# 获取进程管理器实例
process_manager = ProcessManager.get_instance()

# question: LoginService.get_current_user   
taskController = APIRouter(
    prefix="/operator"
)

@taskController.post(
    "/add_job",
    response_model=List[JobResponse]
)
async def execute_task_list(
    request: Request,
    job_params: List[Job],
):
    # 获取分页数据
    # time.sleep(2)
    logger.info("获取成功")
    for job in job_params:
        function = eval(job.invoke_target) # module_task.scheduler_test.job
        args = json.loads(job.job_args or "[]")
        kwargs = json.loads(job.job_kwargs or "{}")
        logger.info(f"args: {args}, kwargs: {kwargs}")
        
        # 使用进程管理器启动进程
        process_manager.start_process(
            job_uid=job.job_uid,
            function=function,
            args=args,
            kwargs=kwargs,
            job_info=job
        )
    
    response_data = []
    for job in job_params:
        response_data.append(JobResponse(
            job_uid=job.job_uid,
            success=True
        ))
    
    return ResponseUtil.success(data=response_data)


@taskController.post(
    "/stop_job",
    response_model=List[JobResponse]
)
async def stop_job(
    request: Request,
    job_uids: List[str] = Query(..., description="要停止的任务ID列表"),
):
    logger.info(f"停止任务: {job_uids}")
    
    response_data = []
    for job_uid in job_uids:
        success = process_manager.stop_process(job_uid)
        response_data.append(JobResponse(
            job_uid=job_uid,
            success=success
        ))
    
    return ResponseUtil.success(data=response_data)


@taskController.get(
    "/job_status",
    response_model=Dict
)
async def get_job_status(
    request: Request,
    job_uid: str = Query(..., description="任务ID"),
):
    """获取指定任务的状态"""
    process_info = process_manager.get_process_info(job_uid)
    
    if not process_info:
        return ResponseUtil.success(data={
            "job_uid": job_uid,
            "status": "not_found",
            "message": "任务不存在或已完成"
        })
    
    is_running = process_manager.is_process_running(job_uid)
    
    return ResponseUtil.success(data={
        "job_uid": job_uid,
        "status": "running" if is_running else "stopped",
        "pid": process_info.get("pid"),
        "start_time": process_info.get("start_time")
    })


@taskController.get(
    "/all_jobs",
    response_model=Dict
)
async def get_all_jobs(request: Request):
    """获取所有运行中的任务"""
    all_processes = process_manager.get_all_processes()
    
    result = {}
    for job_uid, process_info in all_processes.items():
        is_running = process_manager.is_process_running(job_uid)
        result[job_uid] = {
            "status": "running" if is_running else "stopped",
            "pid": process_info.get("pid"),
            "start_time": process_info.get("start_time")
        }
    
    return ResponseUtil.success(data=result)