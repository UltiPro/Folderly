FROM python:3.14-slim
EXPOSE 5000
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY . .
RUN useradd --system --uid 10001 --no-create-home folderly && chown -R 10001:10001 /app
USER 10001
# Workers, threads, timeout and the rest are explained in gunicorn.conf.py.
CMD ["gunicorn", "--config", "gunicorn.conf.py"]
