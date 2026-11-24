FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir streamlit requests
COPY frontend ./frontend
CMD ["streamlit", "run", "frontend/app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]

