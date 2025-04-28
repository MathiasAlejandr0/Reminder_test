from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
import datetime
from database import Exam

scheduler = BackgroundScheduler()

def check_reminders():
    today = datetime.date.today()
    exams = Exam.query.all()
    for exam in exams:
        days_left = (exam.date - today).days
        if days_left in [7, 1, 0]:
            print(f"Recordatorio: La prueba '{exam.name}' es en {days_left} días.")

app = Flask(__name__)
scheduler.add_job(func=check_reminders, trigger="interval", hours=24)  # Revisión diaria.
scheduler.start()