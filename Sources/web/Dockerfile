# syntax=docker/dockerfile:1

FROM python:3.10-buster
WORKDIR /righten
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .
#startscript.sh content: python3 -m flask run
CMD python3 run.py
EXPOSE 5000