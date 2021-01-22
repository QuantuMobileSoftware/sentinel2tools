FROM python:3.7

ENV PATH=/opt/sen2cor/bin:$PATH
ENV PYTHONPATH=/code

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y gcc libspatialindex-dev python3-dev

# Sen2cor installation
RUN wget -nv http://step.esa.int/thirdparties/sen2cor/2.8.0/Sen2Cor-02.08.00-Linux64.run \
    && bash Sen2Cor-02.08.00-Linux64.run --target /opt/sen2cor

RUN mkdir /code

WORKDIR /code

COPY requirements.txt /code/
RUN pip install -r requirements.txt

COPY . /code/

CMD ["python3", "examples/conversion.py"]
