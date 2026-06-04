from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import secrets
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///Notes.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Модель для заметок
class Notes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subtitle = db.Column(db.String(300))
    text = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Связь с пользователем

    # Обратная связь — позволяет получать заметки пользователя через user.notes
    user = db.relationship('Users', back_populates='notes')

# Модель для пользователей
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    token = db.Column(db.String(32), unique=True, nullable=True)
    token_expiry = db.Column(db.DateTime, nullable=True)

    # Связь с заметками пользователя
    notes = db.relationship('Notes', back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_token(self):
        self.token = secrets.token_urlsafe(32)
        self.token_expiry = datetime.utcnow() + timedelta(hours=24)
        return self.token

# Функция получения текущего пользователя
def get_current_user():
    token = request.cookies.get('auth_token')
    if not token:
        return None

    user = Users.query.filter_by(token=token).first()
    if not user or user.token_expiry < datetime.utcnow():
        return None
    return user

# Функция проверки авторизации
def check_auth_token():
    return get_current_user() is not None

# Маршруты

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Проверка существования пользователя с таким же именем
        if Users.query.filter_by(username=username).first():
            return render_template("register.html", error="Пользователь с таким именем уже существует")
        # Проверка существования пользователя с таким же email
        if Users.query.filter_by(email=email).first():
            return render_template("register.html", error="Пользователь с таким email уже существует")

        # Создание нового пользователя
        user = Users(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('login'))
    return render_template("register.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = Users.query.filter_by(username=username).first()
        if user and user.check_password(password):
            token = user.generate_token()
            db.session.commit()
            response = redirect(url_for('programmer_diary'))
            response.set_cookie('auth_token', token)
            return response
        else:
            return render_template("login.html", error="Неверные учётные данные")
    return render_template("login.html")

@app.route("/programmer-diary", methods=['GET', 'POST'])
def programmer_diary():
    # Проверка авторизации через токен
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form.get('title')
        subtitle = request.form.get('subtitle')
        content = request.form.get('content')
        if title and content:
            try:
                # Создаём заметку с указанием пользователя
                note = Notes(
                    title=title,
                    subtitle=subtitle,
                    text=content,
                    user_id=current_user.id  # Привязываем заметку к пользователю
                )
                db.session.add(note)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Ошибка при сохранении в БД: {e}")
                return render_template("notes.html", notes=notes, error="Не удалось сохранить заметку")
        return redirect(url_for('programmer_diary'))

    # Получаем только заметки текущего пользователя
    notes = Notes.query.filter_by(user_id=current_user.id).all()
    return render_template("notes.html", notes=notes)

# Инициализация БД и добавление тестовой записи
with app.app_context():
    db.create_all()

    # Создаём тестового пользователя, если его ещё нет
    if Users.query.filter_by(username='test_user').first() is None:
        test_user = Users(username='test_user', email='test@example.com')
        test_user.set_password('test_password')
        db.session.add(test_user)
        db.session.commit()

        # Создаём тестовую заметку для этого пользователя, если заметок ещё нет
        if Notes.query.count() == 0:
            test_note = Notes(
                title='Тестовая заметка',
                subtitle='Это тестовая заметка для проверки',
                text='Содержание тестовой заметки',
                user_id=test_user.id
            )
            db.session.add(test_note)
            db.session.commit()

if __name__ == "__main__":
    app.run(debug=True)
