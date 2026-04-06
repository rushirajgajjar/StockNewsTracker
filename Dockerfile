FROM public.ecr.aws/lambda/python:3.11

COPY Pipfile Pipfile.lock ./
RUN pip install pipenv && pipenv install --system --deploy

COPY src/ ./src/
COPY templates/ ./templates/
COPY config.yaml ./

CMD ["src.handler.lambda_handler"]
