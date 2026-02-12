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
    questions_all = load_questions()
    page = int(request.args.get("page") or 1)

    per_page = 30
    total_pages = (len(questions_all) + per_page - 1) // per_page

    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    end = start + per_page
    chunk = questions_all[start:end]

    answers = session.get("answers", {})

    return render_template(
        "quiz.html",
        questions=chunk,
        page=page,
        total_pages=total_pages,
        answers=answers,
    )


@app.post("/quiz")
def quiz_post():

    questions_all = load_questions()
    page = int(request.args.get("page") or 1)

    per_page = 30
    total_pages = (len(questions_all) + per_page - 1) // per_page

    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    end = start + per_page
    chunk = questions_all[start:end]

    # guardar respuestas de esta página
    answers = session.get("answers", {})

    for q in chunk:
        qid = str(q["id"])
        answers[qid] = (request.form.get(f"q_{qid}") == "1")

    session["answers"] = answers

    # si no es última página → siguiente page
    if page < total_pages:
        return redirect(url_for("quiz_get", page=page + 1))

    # si es última → resultado
    return redirect(url_for("result"))


@app.get("/reset")
def reset():
    session.pop("answers", None)
    return redirect(url_for("index"))


@app.get("/result")
def result():
    questions = load_questions()
    answers = session.get("answers", {})

    # Contar cuántas respuestas marcaste en total
    total_marked = sum(1 for qid, val in answers.items() if val)

    # Calcular scores por tipo
    scores = {t: 0 for t in range(1, 10)}
    for q in questions:
        qid = str(q["id"])
        if answers.get(qid):
            scores[q["type"]] += 1

    # Transformar a porcentajes
    porcentaje_scores = {}
    for tipo, score in scores.items():
        porcentaje = (score / total_marked * 100) if total_marked > 0 else 0
        porcentaje_scores[tipo] = round(porcentaje, 1)

    # Eneatipo principal
    max_score = max(scores.values()) if scores else 0
    top_types = [t for t, s in scores.items() if s == max_score and max_score > 0]

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    sorted_porcentajes = [(t, porcentaje_scores[t]) for (t, _) in sorted_scores]

    eneatipo_textos = {
        1: """🟡 Tipo 1 — El Reformador:
    Personas éticas, con fuerte sentido del bien y del mal, 
    buscan mejorar el mundo y la perfección. 
    Son responsables, disciplinadas, y muy exigentes consigo mismas y con los demás. 
    Tienden a autocriticarse y a querer que todo sea “lo correcto”.""",
    
        2: """🔵 Tipo 2 — El Ayudador:
    Empáticos, cálidos y orientados a servir a otros. 
    Encuentran satisfacción ayudando y siendo necesarios para quienes quieren. 
    Pueden descuidar sus propias necesidades al priorizar las de otros.""",
    
        3: """🟢 Tipo 3 — El Triunfador:
    Energéticos, adaptables y orientados al éxito. 
    Se enfocan en metas, logros y reconocimiento. 
    Suelen inspirar a otros con su energía, aunque pueden priorizar imagen y resultados.""",
    
        4: """🔴 Tipo 4 — El Individualista:
    Creativos, sensibles y emocionalmente profundos. 
    Se sienten únicos e intensos, valoran la autenticidad. 
    Tienden a ser introspectivos y a explorar su mundo interior con profundidad.""",
    
        5: """🟣 Tipo 5 — El Investigador:
    Curiosos, observadores y analíticos. 
    Buscan conocimiento, comprensión y autonomía. 
    Prefieren observar antes que participar y disfrutan de profundizar en temas complejos.""",
    
        6: """🟠 Tipo 6 — El Leal:
    Personas leales, responsables, cautelosas y con gran sentido de comunidad. 
    Valoran la seguridad, la confianza y la previsibilidad. 
    Pueden preocuparse por posibles riesgos, pero son muy comprometidos.""",
    
        7: """🟤 Tipo 7 — El Entusiasta:
    Activos, optimistas, espontáneos y con deseos de experiencias nuevas. 
    Ayudan a otros a ver el lado positivo de la vida. 
    A veces evitan el dolor y buscan diversión constante.""",
    
        8: """🔶 Tipo 8 — El Desafiador:
    Directos, fuertes, protectores y decididos. 
    Buscan controlar su entorno y no temen enfrentar conflictos. 
    Son líderes naturales, enfocados en la justicia y en la acción.""",
    
        9: """🔷 Tipo 9 — El Pacificador:
    Calmados, tranquilos, atentos y conciliadores. 
    Valoran la paz y evitan confrontaciones. 
    Pueden perder su propia agenda para mantener la armonía.""",
    }


    return render_template(
        "result.html",
        sorted_scores=sorted_scores,
        sorted_porcentajes=sorted_porcentajes,
        top_types=top_types,
        max_score=max_score,
        total_marked=total_marked,
        eneatipo_textos=eneatipo_textos,
    )

