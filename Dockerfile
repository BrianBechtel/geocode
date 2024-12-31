# 使用 Python 官方基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制项目文件到容器中
COPY . /app

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 启动服务
CMD ["uvicorn", "geocode_api:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
