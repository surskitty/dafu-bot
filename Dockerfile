FROM python:3.9
ADD requirements.txt .
RUN pip install -r requirements.txt
ADD config.cfg .
ADD main.py .
COPY bot/ bot/
ENV PYTHONPATH "${PYTHONPATH}:/usr/src/app"
CMD ["python", "./main.py"] 
