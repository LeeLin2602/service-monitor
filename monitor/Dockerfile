FROM python:3.12


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN apt update && apt install -y dnsutils
RUN rm requirements.txt

WORKDIR /usr/src/app
COPY src/ .


CMD [ "python", "-u" ,"./main.py"]
