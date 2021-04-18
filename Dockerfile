FROM tiangolo/uwsgi-nginx-flask:python3.8-alpine
RUN apk --update add bash nano
COPY requirements.txt /var/www/requirements.txt
COPY app /app/app
COPY mtg.py /app/mtg.py
COPY uwsgi.ini /app

RUN echo "uwsgi_read_timeout 300s;" > /etc/nginx/conf.d/custom_timeout.conf
RUN pip install -r /var/www/requirements.txt
