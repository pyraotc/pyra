FROM python:3.11.9-slim AS builder

WORKDIR /app

ENV POETRY_VERSION=2.2.1

# 安装构建工具（必须要在安装 poetry 之前）
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    build-essential \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 poetry
RUN pip install --no-cache-dir "poetry==$POETRY_VERSION" -i https://pypi.tuna.tsinghua.edu.cn/simple/

COPY pyproject.toml poetry.lock* ./

# 使用 --no-root 参数，不安装当前项目
RUN python -m poetry config virtualenvs.create false && \
    python -m poetry install --only main --no-interaction --no-ansi --no-root


FROM python:3.11.9-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

RUN mkdir -p /var/pyra/logs /var/pyra/conf /var/pyra/data && \
    chmod -R 777 /var/pyra && chmod -R 777 /var/pyra/logs && chmod 777 /var/pyra/data

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app /app

EXPOSE 9815

#CMD ["python", "main.py", "run-server", "-c", "/var/pyra/conf/application.yml"]