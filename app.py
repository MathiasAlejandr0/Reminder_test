from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
import datetime

# Configuración de Flask y SQLite
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///exams.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo de base de datos para las pruebas
class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)

# Crear la base de datos si no existe
with app.app_context():
    db.create_all()

# Rutas de la aplicación
@app.route('/')
def index():
    exams = Exam.query.order_by(Exam.date).all()
    return render_template('index.html', exams=exams)

@app.route('/add', methods=['POST'])
def add_exam():
    name = request.form['name']
    date = request.form['date']
    new_exam = Exam(name=name, date=datetime.datetime.strptime(date, "%Y-%m-%d").date())
    db.session.add(new_exam)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_exam(id):
    exam = Exam.query.get(id)
    if exam:
        db.session.delete(exam)
        db.session.commit()
    return redirect(url_for('index'))

# Función para los recordatorios
def check_reminders():
    today = datetime.date.today()
    exams = Exam.query.all()
    for exam in exams:
        days_left = (exam.date - today).days
        if days_left in [7, 1, 0]:
            print(f"Recordatorio: La prueba '{exam.name}' es en {days_left} días.")

# Programador de tareas con APScheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=check_reminders, trigger="interval", hours=24)  # Revisión diaria
scheduler.start()

# Ejecución principal de la aplicación
if __name__ == "__main__":
    app.run(debug=True)