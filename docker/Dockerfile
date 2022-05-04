FROM python:3.8.12-bullseye

ADD requirements.txt /app/requirements.txt

RUN set -ex \
    && python -m venv /env \
    && /env/bin/pip install --upgrade pip \
    && /env/bin/pip install --no-cache-dir -r /app/requirements.txt \
    && /env/bin/pip install gunicorn

ADD langstroth /app/langstroth
ADD user_statistics /app/user_statistics
ADD nectar_allocations /app/nectar_allocations
ADD manage.py /app/manage.py


WORKDIR /app

ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH

COPY docker/docker-run.sh /
RUN chmod u+x /docker-run.sh

EXPOSE 80

CMD ["/docker-run.sh"]