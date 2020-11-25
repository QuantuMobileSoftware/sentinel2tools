FROM python:3.7

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y gcc libspatialindex-dev python3-dev

RUN mkdir /code

WORKDIR /code

COPY requirements.txt /code/
RUN pip install -r requirements.txt

COPY . /code/

CMD ["python", "example.py"]
