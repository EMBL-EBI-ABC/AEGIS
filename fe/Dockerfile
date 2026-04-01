FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN pip install --quiet --no-cache-dir -r requirements.txt
ENV PORT=8080
EXPOSE ${PORT}
CMD gunicorn -b 0.0.0.0:${PORT} app:server