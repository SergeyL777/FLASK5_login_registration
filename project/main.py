from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Хранилище записей (в реальном приложении лучше использовать БД)
notes = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/programmer-diary", methods=['GET', 'POST'])
def programmer_diary():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        if title and content:
            notes[title] = content
        return redirect(url_for('programmer_diary'))
    return render_template("notes.html", notes=notes)

if __name__ == "__main__":
    app.run(debug=True)
