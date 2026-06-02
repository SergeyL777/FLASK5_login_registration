from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///Notes.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Notes(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Исправлено: primary_key → primary_key
    title = db.Column(db.String(200), nullable=False)
    subtitle = db.Column(db.String(300))
    text = db.Column(db.Text, nullable=False)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/programmer-diary", methods=['GET', 'POST'])
def programmer_diary():
    if request.method == 'POST':
        title = request.form.get('title')
        subtitle = request.form.get('subtitle')
        content = request.form.get('content')
        if title and content:
            try:
                note = Notes(title=title, subtitle=subtitle, text=content)
                db.session.add(note)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Ошибка при сохранении в БД: {e}")
        return redirect(url_for('programmer_diary'))
    notes = Notes.query.all()
    return render_template("notes.html", notes=notes)

# Инициализация БД и добавление тестовой записи
with app.app_context():
    db.create_all()
    # Проверяем, есть ли уже записи, чтобы не дублировать
    if Notes.query.count() == 0:
        test_note = Notes(
            title="Четвёртая тема: Работа с миграциями",
            subtitle="Основы Flask-Migrate",
            text="Сегодня изучил, как выполнять миграции базы данных в Flask. Понял, что миграции позволяют безопасно изменять структуру БД без потери данных."
        )
        db.session.add(test_note)
        db.session.commit()


if __name__ == "__main__":
    app.run(debug=True)
