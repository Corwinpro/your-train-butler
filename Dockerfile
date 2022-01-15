FROM python:3.9-slim-buster

COPY requirements.txt requirements.txt
RUN pip3 install --verbose -r requirements.txt

COPY rail_bot rail_bot
COPY setup.py setup.py
RUN python setup.py install

CMD ["python3", "rail_bot"]