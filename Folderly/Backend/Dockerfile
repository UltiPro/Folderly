FROM python:3.13.1
EXPOSE 5000
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir --upgrade -r requirements.txt
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:init()"]