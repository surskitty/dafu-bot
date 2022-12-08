FROM python:3.9
ADD requirements.txt .
RUN pip install -r requirements.txt
ADD config.cfg .
ADD main.py .
ADD bot/bot.py ./bot
CMD ["python", "./main.py"] 
