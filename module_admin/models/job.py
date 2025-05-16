from typing import Optional
from pydantic import BaseModel

class Job(BaseModel):
    """任务模型"""
    job_uid: str
    job_executor: str
    invoke_target: str
    job_args: Optional[str] = ""
    job_kwargs: Optional[str] = ""

    class Config:
        json_schema_extra = {
            "example": {
                "job_uid": "psi3",
                "job_executor": "default",
                "invoke_target": "module_task.scheduler_test.psi",
                "job_args": "",
                "job_kwargs": ""
            }
        } 