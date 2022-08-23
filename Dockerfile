FROM python:3.10

COPY ./requirements.txt /code/requirements.txt
COPY ./dynamite/ /code/dynamite/
RUN pip install -r /code/requirements.txt
CMD ["uvicorn", "dynamite.main:app", "--host", "0.0.0.0", "--port", "80"]