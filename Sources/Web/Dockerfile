# syntax=docker/dockerfile:1

FROM python:3.12-bullseye
WORKDIR /righten
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
CMD apt-get install update --force-yes && apt-get install upgrade --force-yes
COPY . .
LABEL app="Righten"
LABEL version=0.3


#startscript.sh content: python3 -m flask run
ENTRYPOINT python3 run.py
EXPOSE 443