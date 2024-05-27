FROM python:3.12.3-alpine
RUN mkdir /psyho_bot
WORKDIR /psyho_bot
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "bot.py"]