FROM python:3.11-bullseye

WORKDIR /api

COPY requirements.txt /api
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . /api

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
