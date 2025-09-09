#!/usr/bin/env python3
import yaml
import json
import os
import sys


# 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录（假设tests目录在项目根目录下）
project_root = os.path.dirname(os.path.dirname(current_dir))
# 将项目根目录添加到Python路径
sys.path.insert(0, project_root)

# 构建YAML文件的绝对路径
yaml_file_path = os.path.join(project_root, 'JobConfig', 'sgb_v', 'local','sgb_v_train.yaml')

# 读取YAML文件
with open(yaml_file_path, 'r') as file:
    yaml_data = yaml.safe_load(file)

yaml_data["job_uid"] = "qq"

if __name__ == "__main__":
    from module_task.sgb_v import sgb_v_train
    from module_admin.service.task_service_copy import ProcessManager

    # sgb_v_train(**yaml_data)

    manager = ProcessManager(max_workers=2)
    manager.execute_jobs(
        job_uid_list=["qq"],
        jobs=[sgb_v_train],
        kwargs_list=[yaml_data]
    )
    results = manager.wait_for_completion()
    
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
    
    # import time
    # time.sleep(100)