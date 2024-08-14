FROM public.ecr.aws/lambda/python:3.11

COPY requirements.txt ./
RUN pip install -r requirements.txt

# add env variables as needed.
# ENV ..

COPY app ./app

CMD ["app.lambda_handler.lambda_handler"]
