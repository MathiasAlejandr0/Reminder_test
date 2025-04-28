import datetime
import json
import os
import time

from flask import Flask, flash, redirect, render_template, request, url_for
from apscheduler.schedulers.background import BackgroundScheduler
from plyer import notification

# Colores para la consola
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'

app = Flask(__name__, template_folder='.')

def show_tutorial():
    def tutorial_section(title, content, expected_answer="si"):
        print(f"\n{Colors.HEADER}{title}{Colors.END}")
        print(f"{Colors.BLUE}{'-' * len(title)}\n{Colors.END}")
        for line in content:
            print(line)
        if expected_answer is not None:
            while True:
                user_answer = input("\n¿Entendiste esta sección? (si/no): ").lower()
                if user_answer == expected_answer or user_answer == 'y':
                    print("¡Excelente! Continuemos.")
                    break
                elif user_answer == "no":
                    print("Repasemos nuevamente...")
                    for line in content:
                       print(line)
                else:
                    print(f"{Colors.FAIL}")
                    print("Respuesta no válida. Por favor, responde 'si' o 'no'.")

    tutorial_section(
        "Bienvenido al Tutorial de Recordatorios de Exámenes",
        [
            "Este tutorial te guiará a través de las funcionalidades de la aplicación.",
            "Sigue las instrucciones y responde las preguntas para avanzar.",
        ],
    )
    add_reminder_tutorial = [
        "Para agregar un recordatorio, necesitas seleccionar la opcion '1'.",
        "Ingresa el nombre de la materia.",
        "Ingresa el tipo de examen.",
        "Ingresa la sala.",
        "Ingresa la fecha del examen (en formato AAAA-MM-DD).",
        "Finalmente, se agregara el recordatorio."
    ]
    tutorial_section("Agregar un Recordatorio", add_reminder_tutorial)
    tutorial_section(
        "Marcar un Examen como Completado",
        [
            "Para marcar un examen como completado, primero debes ver la lista de examenes con la opcion '2'.",
            "Selecciona el examen que has completado ingresando el numero que aparece al lado de el.",
            "Luego elije la opcion 'marcar como completado' e ingresa el numero del examen que ya completaste"
        ],
    )
    recurring_reminders_tutorial = [
        "Para crear un recordatorio recurrente, necesitas ir a la opcion '1'.",
        "Luego de completar el formulario, el programa te preguntara si quieres que el recordatorio se repita.",
        "Si respondes 'si', el programa te preguntara con que frecuencia se debe repetir.",
        "Si respondes que no, el programa guardara el recordatorio y terminara.",
    ]
    tutorial_section("Recordatorios recurrentes", recurring_reminders_tutorial)
    priority_reminders_tutorial = [
        "Puedes establecer un nivel de prioridad para un recordatorio.",
        "Para hacerlo, debes agregar un nuevo recordatorio.",
        "Luego de completar el formulario, el programa te preguntara que prioridad le quieres asignar al recordatorio.",
        "Puedes elegir entre: Alta, Media, y Baja.",
        "Si no ingresas ninguna opcion, por defecto se asignara Baja."
    ]
    tutorial_section("Prioridad de recordatorios", priority_reminders_tutorial)
    tutorial_section("Eliminar un recordatorio", ["Para eliminar un recordatorio primero debes ver la lista de examenes, con la opcion '2'.",
    "Luego de ver la lista, selecciona la opcion 'eliminar recordatorio'.",
    "El programa te pedira el numero del recordatorio que quieres eliminar."])
    backup_tutorial = [
        [
            "Puedes guardar todos los recordatorios en un archivo de seguridad.",
            "Para guardar los recordatorios, ejecuta la opción 'guardar_recordatorios'.",
            "Los recordatorios se guardarán en un archivo llamado 'backup.json'.",
            "Para cargar recordatorios, ejecuta la opción 'cargar_recordatorios'.",
            "Esto reemplazará los recordatorios actuales."
        ],
    ]
    tutorial_section("Copias de Seguridad", backup_tutorial)

    print(
        f"{Colors.GREEN}\n¡Has completado el tutorial! Ya puedes empezar a usar la aplicación.{Colors.END}"
    )


reminders = []


def save_reminders_to_file():
    while True:
        filename = input("Ingrese el nombre del archivo para guardar los recordatorios (ej: backup.json): ")
        if not filename.endswith('.json'):
            print(f"{Colors.FAIL}Error: El nombre del archivo debe terminar con '.json'{Colors.END}")
        else:
            try:
                with open(filename, "w") as f:
                    json.dump(reminders, f, indent=4, default=str)

                print(
                    f"{Colors.GREEN}Recordatorios guardados con éxito en {filename}{Colors.END}"
                )
                return filename
            except Exception as e:
                print(f"{Colors.FAIL}Error al guardar recordatorios: {e}{Colors.END}")


def load_reminders_from_file(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                data = json.load(f)
                reminders.clear()
                reminders.extend(data)
                print(
                    f"{Colors.GREEN}Recordatorios cargados con éxito desde {filename}{Colors.END}"
                )
        except json.JSONDecodeError:
            print(
                f"{Colors.FAIL}Error: El archivo {filename} no contiene datos válidos.{Colors.END}"
            )
    else:
        print(f"{Colors.FAIL}El archivo {filename} no existe.{Colors.END}")

def export_reminders_to_text():
    while True:
        filename = input("Ingrese el nombre del archivo para exportar los recordatorios (ej: calendar_export.txt): ")
        if not filename.endswith('.txt'):
            print(f"{Colors.FAIL}Error: El nombre del archivo debe terminar con '.txt'.{Colors.END}")
        else:
            try:
                with open(filename, "w") as f:
                    for reminder in reminders:
                        f.write(f"{reminder.date.isoformat()} - {reminder.subject} ({reminder.test_type}) en {reminder.room}\n")
                print(f"{Colors.GREEN}Recordatorios exportados a {filename} con éxito.{Colors.END}")
                return filename
            except Exception as e:
                print(f"{Colors.FAIL}Error al exportar recordatorios: {e}{Colors.END}")


def show_upcoming_exams():
    while True:
        try:
            days_to_check = int(input("Ingrese la cantidad de días para mostrar los exámenes próximos (ej: 3): "))
            if days_to_check < 0:
                print(f"{Colors.FAIL}Por favor, ingrese un número de días positivo.{Colors.END}")
            else:
                break
        except ValueError:
            print(f"{Colors.FAIL}Por favor, ingrese un número válido.{Colors.END}")

    today = datetime.date.today()
    upcoming_exams = [exam for exam in reminders if (datetime.datetime.strptime(exam['date'], "%Y-%m-%d").date() - today).days <= days_to_check]
    upcoming_exams.sort(key=lambda x: x['date'])
    if upcoming_exams:
        print(f"\nPróximos Exámenes en los próximos {days_to_check} días:")
        for exam in upcoming_exams:
            exam_date = datetime.datetime.strptime(exam['date'], "%Y-%m-%d").date()
            days_until = (exam_date - today).days
            print(f"{Colors.GREEN}  - {exam['subject']} ({exam['test_type']}) en {exam['room']} el {exam['date']}. {days_until} días restantes.{Colors.END}")
    else:
        print(f"{Colors.WARNING}\nNo hay exámenes próximos programados en los próximos {days_to_check} días.{Colors.END}")
        
def show_notification(title, message):
    notification.notify(
        title=title,
        message=message,
        app_icon=None,  # Puedes especificar un icono si lo tienes
        timeout=10  # Duración de la notificación en segundos
    )

def search_reminders():
    if not reminders:
        print(f"{Colors.WARNING}No hay recordatorios guardados.{Colors.END}")
        return
    
    print(f"\n{Colors.HEADER}Buscar recordatorios{Colors.END}")
    print(f"{Colors.BLUE}1. Buscar por materia{Colors.END}")
    print(f"{Colors.BLUE}2. Buscar por tipo de examen{Colors.END}")
    print(f"{Colors.BLUE}3. Buscar por fecha{Colors.END}")
    print(f"{Colors.BLUE}4. Cancelar{Colors.END}")
    
    while True:
        try:
            option = int(input("Seleccione una opción: "))            
            if option in [1, 2, 3, 4]:
                break
            else:
                print(f"{Colors.FAIL}Opción no válida. Por favor, seleccione una opción del 1 al 4.{Colors.END}")
        except ValueError:
            print(f"{Colors.FAIL}Entrada no válida. Por favor, ingrese un número.{Colors.END}")
    
    results = []
    if option == 1:
        subject_to_search = input("Ingrese la materia a buscar: ")
        results = [exam for exam in reminders if subject_to_search.lower() in exam['subject'].lower()]
    elif option == 2:
        test_type_to_search = input("Ingrese el tipo de examen a buscar: ")
        results = [exam for exam in reminders if test_type_to_search.lower() in exam['test_type'].lower()]
    elif option == 3:
        date_to_search_str = input("Ingrese la fecha a buscar (AAAA-MM-DD): ")
        try:
            date_to_search = datetime.datetime.strptime(date_to_search_str, "%Y-%m-%d").date()
            results = [exam for exam in reminders if datetime.datetime.strptime(exam['date'], "%Y-%m-%d").date() == date_to_search]
        except ValueError:
            print(f"{Colors.FAIL}Formato de fecha incorrecto. Usa AAAA-MM-DD.{Colors.END}")
            return
    elif option == 4:
        print(f"{Colors.WARNING}Búsqueda cancelada.{Colors.END}")
        return
    
    if not results:
        print(f"{Colors.WARNING}No se encontraron recordatorios con esos criterios.{Colors.END}")
    else:
        print(f"\n{Colors.GREEN}Resultados de la búsqueda:{Colors.END}")
        for exam in results:
            print(f"{Colors.BLUE}- {exam['subject']} ({exam['test_type']}) en {exam['room']} el {exam['date']}{Colors.END}")


def add_reminder():
    print(f"\n{Colors.HEADER}Agregar un nuevo recordatorio{Colors.END}")
    subject = input("Ingrese el nombre de la materia: ")
    test_type = input("Ingrese el tipo de examen: ")
    room = input("Ingrese la sala: ")
    while True:
        date_str = input("Ingrese la fecha del examen (AAAA-MM-DD): ")
        try:
            date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            break
        except ValueError:
            print(f"{Colors.FAIL}Formato de fecha incorrecto. Usa AAAA-MM-DD{Colors.END}")
    
    priority = input("Ingrese la prioridad del recordatorio (Alta, Media, Baja): ").lower()
    if priority not in ["alta", "media", "baja"]:
        priority = "baja"

    reminder = {
        "subject": subject,
        "test_type": test_type,
        "room": room,
        "date": date.strftime("%Y-%m-%d"),
        "priority": priority,
    }

    while True:
        repeat = input("¿Quieres que el recordatorio se repita? (si/no): ").lower()
        if repeat in ["si", "no", "y", "n"]:
            break
        else:
            print(f"{Colors.FAIL}Opcion invalida{Colors.END}")

    if repeat == "si" or repeat == "y":
        while True:
            try:
                frequency = int(input("¿Cada cuántos días quieres que se repita? "))
                reminder["frequency"] = frequency
                break
            except ValueError:
                print(f"{Colors.FAIL}Valor invalido, ingrese un numero valido.{Colors.END}")
    reminders.append(reminder)
    print(f"{Colors.GREEN}Recordatorio agregado con éxito.{Colors.END}")

def edit_reminder():
    list_reminders()
    if not reminders:
        return
    while True:
        try:
            reminder_number = int(input("Ingrese el número del recordatorio que desea editar: ")) - 1
            if 0 <= reminder_number < len(reminders):
                break
            else:
                print(f"{Colors.FAIL}Número de recordatorio no válido. Por favor, elija un número de la lista.{Colors.END}")
        except ValueError:
            print(f"{Colors.FAIL}Por favor, ingrese un número.{Colors.END}")

    reminder = reminders[reminder_number]
    print(f"{Colors.WARNING}¿Está seguro que desea editar este recordatorio? (si/no){Colors.END}")
    confirm = input().lower()
    if confirm == 'si' or confirm == 'y':
        print(f"\n{Colors.HEADER}Editando recordatorio: {reminder['subject']} ({reminder['test_type']}){Colors.END}")
        reminder['subject'] = input(f"Nuevo nombre de la materia ({reminder['subject']}): ") or reminder['subject']
        reminder['test_type'] = input(f"Nuevo tipo de examen ({reminder['test_type']}): ") or reminder['test_type']
        reminder['room'] = input(f"Nueva sala ({reminder['room']}): ") or reminder['room']

        while True:
            date_str = input(f"Nueva fecha del examen (AAAA-MM-DD) ({reminder['date']}): ") or reminder['date']
            try:
                date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                reminder['date'] = date.strftime("%Y-%m-%d")
                break
            except ValueError:
                print(f"{Colors.FAIL}Formato de fecha incorrecto. Usa AAAA-MM-DD{Colors.END}")

        priority = input(f"Nueva prioridad del recordatorio (Alta, Media, Baja) ({reminder['priority']}): ").lower()
        if priority not in ["alta", "media", "baja"]:
            priority = "baja"
        reminder['priority'] = priority
    else:
        print(f"{Colors.WARNING}Operacion cancelada.{Colors.END}")
    print(f"{Colors.GREEN}Recordatorio editado con éxito.{Colors.END}")
            break
        except ValueError:
            print(f"{Colors.FAIL}Formato de fecha incorrecto. Usa AAAA-MM-DD{Colors.END}")

    priority = input(f"Nueva prioridad del recordatorio (Alta, Media, Baja) ({reminder['priority']}): ").lower()
    if priority not in ["alta", "media", "baja"]:
        priority = "baja"
    reminder['priority'] = priority

    print(f"{Colors.GREEN}Recordatorio editado con éxito.{Colors.END}")

# Ruta principal



# Rutas para agregar un recordatorio
@app.route('/add_reminder', methods=['GET', 'POST'])
def add_reminder():
    if request.method == 'POST':
        subject = request.form['subject']
        test_type = request.form['test_type']
        room = request.form['room']
        date_str = request.form['date']

        if not all([subject, test_type, room, date_str]):
            print(f"{Colors.FAIL}Por favor, completa todos los campos.{Colors.END}")
            # flash('Por favor, completa todos los campos.', 'error')
            return redirect(url_for('add_reminder'))

        try:
            date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            print(f"{Colors.FAIL}Formato de fecha incorrecto. Usa AAAA-MM-DD{Colors.END}")

            flash("Formato de fecha incorrecto. Usa AAAA-MM-DD", "error")
            return redirect(url_for("add_reminder"))

        new_reminder = {
            "subject": subject,
            "test_type": test_type,
            "room": room,
            "date": date}
        try:
            db.session.commit()
        except Exception as e:
        flash('Recordatorio eliminado con éxito.', 'success')
    return redirect(url_for('index'))

@app.route('/completed/<int:id>')
def list_reminders():
    for i, reminder in enumerate(reminders):
        print(f"{Colors.BLUE}{i + 1}. {reminder['subject']} ({reminder['test_type']}) en {reminder['room']} el {reminder['date']}{Colors.END}")


def complete_reminder(id):
    reminder = Reminder.query.get(id)
    if reminder:
        reminder.completed = True
        try:
            db.session.commit()
        except Exception as e:
            print(f"{Colors.FAIL}Error al completar el recordatorio: {e}{Colors.END}")
        
        flash('Recordatorio completado con éxito.', 'success')
    return redirect(url_for('index'))

@app.route('/show_completed')
def show_completed():
    completed_reminders = Reminder.query.filter_by(completed=True).all()
    filename = save_reminders_to_file()
    print(f"{Colors.GREEN}Recordatorios guardados con éxito en {filename}{Colors.END}" if filename else "")
    return redirect(url_for('index'))


@app.route('/load_reminders')
def load_reminders():
    while True:
        filename = input("Ingrese el nombre del archivo para cargar los recordatorios (ej: backup.json): ")
        if  filename.endswith('.json'):
             if os.path.exists(filename):
                print(f"{Colors.WARNING}Se van a reemplazar los recordatorios actuales. ¿Está seguro que desea continuar? (si/no){Colors.END}")
                confirm = input().lower()
                if confirm == 'si' or confirm == "y":
                    load_reminders_from_file(filename)
                    print(f"{Colors.GREEN}Recordatorios cargados con éxito desde {filename}{Colors.END}")
                    break
                else:
                    print(f"{Colors.WARNING}Operación cancelada.{Colors.END}")
             else:
                print(f"{Colors.FAIL}El archivo {filename} no existe.{Colors.END}")
        else:
            print(f"{Colors.FAIL}Error: El nombre del archivo debe terminar con '.json'{Colors.END}")            
        print(f"{Colors.FAIL}El archivo {filename} no existe.{Colors.END}")
    return redirect(url_for('index'))


@app.route('/export_calendar')
def export_calendar():
    filename = export_reminders_to_text()


    return redirect(url_for('index'))
def upcoming_exams():
    show_upcoming_exams()
    flash('Exámenes próximos mostrados en la consola.', 'success')
    return redirect(url_for('index'))


# Función para revisar los recordatorios y enviar notificaciones
def notify_reminders():
    today = datetime.date.today()
    for reminder in reminders:
        date = datetime.datetime.strptime(reminder["date"], "%Y-%m-%d").date()
        days_left = (date - today).days

        if days_left == 7:  # Notificación con 7 días de anticipación
            show_notification(f"Recordatorio: {reminder['subject']}", f"Tienes un examen tipo {reminder['test_type']} en la sala {reminder['room']} en 7 días.")
            print(f"{Colors.BLUE}Recordatorio: La prueba '{reminder['subject']}' es en 7 días.{Colors.END}")
        elif days_left == 1:  # Notificación un día antes
            show_notification(f"Recordatorio: {reminder['subject']}", f"Tienes un examen tipo {reminder['test_type']} en la sala {reminder['room']} MAÑANA.")
            print(f"{Colors.BLUE}Recordatorio: La prueba '{reminder.subject}' es MAÑANA.{Colors.END}")
        elif days_left == 0:
            show_notification(f"Recordatorio: {reminder.subject}", f"Tienes un examen tipo {reminder.test_type} en la sala {reminder.room} HOY.")
            print(f"Recordatorio: La prueba '{reminder.subject}' es HOY.")



# Programador de tareas para revisar los recordatorios
def delete_reminder():
    list_reminders()
    if not reminders:
        return
    while True:
        try:
            reminder_number = int(input("Ingrese el número del recordatorio que desea eliminar: ")) - 1
            if 0 <= reminder_number < len(reminders):
                break
            else:
                print(f"{Colors.FAIL}Número de recordatorio no válido. Por favor, elija un número de la lista.{Colors.END}")
        except ValueError:
            print(f"{Colors.FAIL}Por favor, ingrese un número.{Colors.END}")
    
    print(f"{Colors.WARNING}¿Está seguro que desea eliminar este recordatorio? (si/no){Colors.END}")
    confirm = input().lower()    
    if confirm == 'si' or confirm == "y":
        del reminders[reminder_number]
        print(f"{Colors.GREEN}Recordatorio eliminado con éxito.{Colors.END}")
    elif confirm == 'no' or confirm == "n":
        print(f"{Colors.WARNING}Operación cancelada.{Colors.END}")

def main():
    notify_reminders()
    show_tutorial()
    while True:
        print(f"\n{Colors.HEADER}Menú Principal{Colors.END}")
        print(f"{Colors.BLUE}1. Agregar un nuevo recordatorio{Colors.END}")
        print(f"{Colors.BLUE}2. Ver todos los recordatorios{Colors.END}")
        print(f"{Colors.BLUE}3. Marcar como completado{Colors.END}")
        print(f"{Colors.BLUE}4. Guardar recordatorios{Colors.END}")
        print(f"{Colors.BLUE}5. Cargar recordatorios{Colors.END}")
        print(f"{Colors.BLUE}6. Exportar recordatorios a calendario{Colors.END}")
        print(f"{Colors.BLUE}7. Ver examenes proximos{Colors.END}")
        print(f"{Colors.BLUE}8. Buscar recordatorios{Colors.END}")
        print(f"{Colors.BLUE}9. Eliminar un recordatorio{Colors.END}")
        print(f"{Colors.BLUE}10. Editar un recordatorio{Colors.END}")
        print(f"{Colors.BLUE}11. Salir{Colors.END}")
        try:
            choice = int(input("Seleccione una opción: "))
            if choice == 1:
                add_reminder()
            elif choice == 2:
                list_reminders()
            elif choice == 3:
                list_reminders()
                while True:
                    try:
                        exam_number = int(input("Ingrese el numero del examen que desea marcar como completado: "))-1
                        if 0 <= exam_number < len(reminders):
                            reminders[exam_number]["completed"] = True
                            break
                    except ValueError:
                        print(f"{Colors.FAIL}Opcion invalida, ingrese un numero valido.{Colors.END}")
            elif choice == 4:
                save_reminders_to_file()
            elif choice == 5:
                load_reminders_from_file()
            elif choice == 6:
                export_reminders_to_text()
            elif choice == 7:
                show_upcoming_exams()
            elif choice == 8:
                search_reminders()
            elif choice == 9:
                delete_reminder()
            elif choice == 10:
                edit_reminder()
            elif choice == 11:
                break
        except ValueError:
            print(f"{Colors.FAIL}Opción inválida. Por favor, ingrese un número.{Colors.END}")

if __name__ == "__main__":
    main()
