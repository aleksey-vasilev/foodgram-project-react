FROM python:3.9

RUN python -m pip install --upgrade pip

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:7000", "foodgramm_backend.wsgi"]