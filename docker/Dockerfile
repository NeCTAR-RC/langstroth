FROM python:3.10-bookworm

ADD requirements.txt /app/requirements.txt

RUN set -ex \
    && python -m venv /env \
    && /env/bin/pip install --no-cache-dir --upgrade pip \
    && /env/bin/pip install --no-cache-dir -r /app/requirements.txt \
    && /env/bin/pip install --no-cache-dir django-storage-swift \
    && /env/bin/pip install --no-cache-dir gunicorn

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
