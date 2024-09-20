FROM python:3.11-bullseye

WORKDIR /ui

COPY requirements.txt /ui
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . /ui

EXPOSE 8001

CMD ["chainlit", "run", "app.py", "-w", "--port", "8001"]