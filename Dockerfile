FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libexpat1 \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt requirements.txt
COPY geocode_api.py geocode_api.py
COPY geodata/ geodata/

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 设置启动命令
CMD ["uvicorn", "geocode_api:app", "--host", "0.0.0.0", "--port", "8000"]
