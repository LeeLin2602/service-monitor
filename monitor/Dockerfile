# 使用官方 Python 镜像作为基础镜像
FROM python:3.8


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN rm requirements.txt

WORKDIR /usr/src/app
COPY src/ .


CMD [ "python", "./main.py" ]
# CMD [ "/bin/sh", "-c", "ls -ls && pwd" ]
