# syntax=docker/dockerfile:1

FROM python:3


COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD uvicorn server:app --host 0.0.0.0 --port 8002

EXPOSE 8002