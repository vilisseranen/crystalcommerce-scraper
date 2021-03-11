FROM tiangolo/uwsgi-nginx-flask:python3.6-alpine3.7
RUN apk --update add bash nano
COPY requirements.txt /var/www/requirements.txt
COPY app /app/app
COPY mtg.py /app/mtg.py
COPY uwsgi.ini /app

RUN pip install -r /var/www/requirements.txt
