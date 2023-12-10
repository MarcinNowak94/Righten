# syntax=docker/dockerfile:1

FROM postgres:latest
WORKDIR /Righten
COPY . .
EXPOSE 5432
#pgloader to migrate data from SQLITE to PostgreSQL
#https://pgloader.readthedocs.io/en/latest/ref/sqlite.html
#RUN apt-get update --assume-yes
#RUN apt-get install pgloader --assume-yes
#RUN pgloader RightenDB.load