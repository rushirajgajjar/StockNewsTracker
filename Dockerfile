FROM public.ecr.aws/lambda/python:3.11

RUN pip install --upgrade pip && \
    pip install "numpy<2" && \
    pip install anthropic yfinance boto3 pyyaml jinja2 requests

COPY src/ ./src/
COPY templates/ ./templates/
COPY config.yaml ./

CMD ["src.handler.lambda_handler"]
