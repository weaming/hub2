FROM python:3.7-alpine

WORKDIR /usr/src/app

COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock

COPY . .

CMD [ "python", "./main.py" ]

