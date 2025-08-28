FROM python:3.11-slim
WORKDIR /work

# deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# include your scripts so ENTRYPOINT always exists
COPY src/ ./src

ENTRYPOINT ["python", "src/prepare_scorecard.py"]
