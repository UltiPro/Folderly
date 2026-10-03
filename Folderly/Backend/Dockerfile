FROM python:3.14-slim
EXPOSE 5000
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY . .
# Workers, threads, timeout and the rest are explained in gunicorn.conf.py.
CMD ["gunicorn", "--config", "gunicorn.conf.py"]