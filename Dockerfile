FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
COPY examples/lightrag_openai_compatible_demo_rabbitmq.py /app/
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN pip install -r requirements.txt

ENTRYPOINT ["python", "/app/lightrag_openai_compatible_demo_rabbitmq.py"]