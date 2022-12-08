FROM python:3.9
ADD main.py .
ADD requirements.txt .
ADD bot/bot.py ./bot
RUN pip install -r requirements.txt
CMD ["python", "./main.py"] 
