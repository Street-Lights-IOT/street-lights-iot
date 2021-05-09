FROM python:3.8.10

COPY requirements.txt .
RUN pip install -r requirements.txt && rm requirements.txt

RUN useradd -ms /bin/bash user
WORKDIR /home/user/edge

COPY resources/ ./resources
COPY services/ ./services
COPY utils.py mock.py edge.py logging.conf ./

RUN chown -R user:user .
USER user

EXPOSE 5683
ENTRYPOINT ["python", "edge.py"]