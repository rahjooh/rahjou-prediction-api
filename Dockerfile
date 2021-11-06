FROM python:3.8

WORKDIR /root

ADD . .

ENV VIRTUAL_ENV=/root/venv
ENV PATH="/root/venv/bin:$PATH"

# RUN PATH=$PATH:/root/.local/bin
# RUN PYTHONPATH=$PYTHONPATH:/root/lib/bin

EXPOSE 8585

ENTRYPOINT ["python", "/root/src/app.py"]
