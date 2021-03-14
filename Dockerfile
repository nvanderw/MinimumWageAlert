# set base image (host OS)
# FROM python:3.8
FROM public.ecr.aws/lambda/python:3.8

COPY requirements.txt .

RUN yum install -y git
RUN pip install -r requirements.txt

COPY app.py .

CMD [ "app.handler" ]