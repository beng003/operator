# 根目录执行
# docker build -f Dockerfile -t crpi-84gohwg2zpoyckdg.cn-hangzhou.personal.cr.aliyuncs.com/beng003_docker/dagscheduler-backend:v0.1.0 .
# docker build -f Dockerfile -t dagscheduler-backend:v0.1.0 .

FROM crpi-84gohwg2zpoyckdg.cn-hangzhou.personal.cr.aliyuncs.com/beng003_docker/python:3.10-slim
# 更新并安装 libgomp 以及 gcc 
RUN apt-get update && apt-get install -y libgomp1 gcc && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements-docker.txt .
RUN pip install -r requirements-docker.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY . .
EXPOSE 9099
CMD ["python3", "app.py"]