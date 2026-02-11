import json
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session

DATA_PATH = Path("data/questions.json")

app = Flask(__name__)
app.secret_key = "CHANGE_ME_IN_HEROKU"  # luego lo ponemos por variable de entorno


def load_questions():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    questions = data["questions"]
    # nos quedamos solo con las que tienen type 1..9
    questions = [q for q in questions if q.get("type") in range(1, 10)]
    return questions


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/quiz")
def quiz_get():
    questions = load_questions()
    page = int(request.args.get("page", 1))
    per_page = 30
    total_pages = (len(questions) + per_page - 1) // per_page

    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    end = start + per_page
    chunk = questions[start:end]

    answers = session.get("answers", {})  # { "id": true/false }

    return render_template(
        "quiz.html",
        questions=chunk,
        page=page,
        total_pages=total_pages,
        answers=answers,
    )


@app.post("/quiz")
def quiz_post():
    # guardamos checks de la página actual
    questions = load_questions()
    page = int(request.args.get("page", 1))
    per_page = 30
    total_pages = (len(questions) + per_page - 1) // per_page
    page = max(1, min(page, total_pages))

    start = (page - 1) * per_page
    end = start + per_page
    chunk = questions[start:end]

    answers = session.get("answers", {})
    # setear true/false por cada id en la página
    for q in chunk:
        qid = str(q["id"])
        answers[qid] = (request.form.get(f"q_{qid}") == "1")

    session["answers"] = answers

    if page >= total_pages:
        return redirect(url_for("result"))

    return redirect(url_for("quiz_get", page=page + 1))


@app.get("/reset")
def reset():
    session.pop("answers", None)
    return redirect(url_for("index"))


@app.get("/result")
def result():
    questions = load_questions()
    answers = session.get("answers", {})

    scores = {t: 0 for t in range(1, 10)}
    for q in questions:
        qid = str(q["id"])
        if answers.get(qid):
            scores[q["type"]] += 1

    max_score = max(scores.values()) if scores else 0
    top_types = [t for t, s in scores.items() if s == max_score and max_score > 0]

    # orden por puntaje desc
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    return render_template(
        "result.html",
        sorted_scores=sorted_scores,
        top_types=top_types,
        max_score=max_score,
    )
