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
    Tienden a autocriticarse y a querer que todo sea “lo correcto”.

        🟡 Características principales:
    El valor del eneatipo 1 radica en la EXCELENCIA. Acción (orden práctico).
    Su mayor contribución es ser bueno localizando errores, pule y perfecciona. Es un FINALIZADOR. 
    Posee buena orientación al detalle, es reacio a delegar, y puede desarrollar una preocupación excesiva. Es prolijo y ordenado.
    No le gusta que le cambien de lugar sus cosas. 
    Sus conductas recurrentes pueden ser el controlar, corregir, juzgar, criticar.
    Desarrolla hábitos como buscar culpables, corrigir errores y tener la razón. 
    El resultado de estas conductas y hábitos es un predominio del deber sobre el placer.
    La creencia arraigada en su interior es "el mundo es un lugar imperfecto para perfeccionar".
    El miedo básico es ser corrupto, defectuoso o moralmente incorrecto.
    Su miedo constitutivo a no poder le genera la necesidad de ser fuerte y la reacción ante este miedo es controlando. 
    Sus principales fortalezas son ser ético, disciplinado, responsable, justo. Y sus principales áreas de mejora radican en 
    su ser crítico, rígido, autoexigente, intolerante.
    El pecado capital del eneatipo 1 es la ira (reprimida). 
    En su lado luz el eneatipo 1  representa integridad, mejora del mundo, coherencia.
    Sin embargo, en su lado sombra desarrolla un juicio constante y perfeccionismo paralizante.
    Para lograr su integración es aconsejable que incorpore conductas como la espontaneidad, alegría y flexibilidad,
    evitando la emocionalidad, resentimiento y melancolía.
    Las actitudes que equilibran a la esencia 1 son ser más calmado y más servicial.
    El desarrollo de estas características le permite adquirir ecuanimidad, empatía y colaboración con la gente real, 
    y no sólo por principios y normas: "lo correcto". Busca el orden y la superación con paciencia, tolerancia, comprensión y amorosidad.
    Cuando no se desarrollan, el eneatipo 1 tiende a caer en el pesimismo total, "nada va a cambiar" y/o 
    no se atiende a sí mismo: no toma vacaciones, no descansa, atiende las responsabilidades que asume
    y no sus necesidades.
    La escencia 1 se encuentra dentro de la tríada instintiva, es decir, el área de la acción o visceral (expresión). 
    Dosifica planificadamente su energía. Es detallista.
    Cabe destacar que existen 3 sub-tipos:
    
    🏠 1 Conservación (Ansiedad)

    Preocupado por hacerlo todo correctamente. Muy autoexigente. Controla detalles, orden y responsabilidad personal.

    👥 1 Social (Rigidez)

    Defiende reglas y principios. Moralista, crítico con el entorno. Siente que debe mejorar el mundo.

    ❤️ 1 Sexual (Celo)

    Más intenso y emocional. Puede ser crítico pero también apasionado. Busca “corregir” al otro.
         
       🟡 ¿Cómo puedes sentirte mejor?:
    "SIEMPRE no es realmente siempre y NUNCA no son todas las veces"
    Desarrollando tareas creativas, que te incentiven. 
    Dándote tiempo libre para el placer y la relajación. Sintiendo el disfrute.
    Focalizarte en un ideal de vida. Poner las formas en función del fondo.
    Recordar que todos somos uno y perfectos tal como somos.
    Comprender que hay más de una manera correcta de hacer las cosas.
    Practicar el perdón con uno mismo y los demás. Tratarte con menos rigor.
    Parar, darse tiempos. Soltarse y soltar.
    Dejarse llevar por la corrienre.
    Confiar en las buenas intenciones de los demás.
    Apreciar a las demás personas, atender a los deseos de los demás genuinamente,
    ayudar a los demás a tomar decisiones.
    El objetivo de la vida es ser humano, no perfecto.""",        
        
        2: """🔵 Tipo 2 — El Ayudador:
    Empáticos, cálidos y orientados a servir a otros. 
    Encuentran satisfacción ayudando y siendo necesarios para quienes quieren. 
    Pueden descuidar sus propias necesidades al priorizar las de otros.""",

        2: """🔵 Características principales:
    Miedo básico: No ser amado o necesario.
    
    Fortalezas: Generoso, empático, afectuoso.
    Debilidades: Dependiente, complaciente, manipulador sutil.
    
    Pecado capital: Orgullo.
    
    Luz: Amor genuino y servicio desinteresado.
    Sombra: Dar para recibir, invasión emocional.
    
    Integración (va al 4): Se conecta con sus propias emociones y autenticidad.
    Desintegración (va al 8): Se vuelve controlador y dominante.
    
    Alas: 1 (más estructurado) o 3 (más orientado al logro).
    
    Tríada: Emocional (Vergüenza).""",
        
        3: """🟢 Tipo 3 — El Triunfador:
    Energéticos, adaptables y orientados al éxito. 
    Se enfocan en metas, logros y reconocimiento. 
    Suelen inspirar a otros con su energía, aunque pueden priorizar imagen y resultados.""",

        3: """🟢 Características principales:
    Miedo básico: Ser un fracaso o no valer.
    
    Fortalezas: Eficiente, adaptable, motivador.
    Debilidades: Vanidoso, competitivo, desconectado emocionalmente.
    
    Pecado capital: Vanidad.
    
    Luz: Inspirador, productivo, ejemplo de superación.
    Sombra: Identidad basada en la imagen.
    
    Integración (va al 6): Se vuelve más cooperativo y comprometido.
    Desintegración (va al 9): Se vuelve apático y desconectado.
    
    Alas: 2 (más sociable) o 4 (más creativo).
    
    Tríada: Emocional (Vergüenza).""",
                
        4: """🔴 Tipo 4 — El Individualista:
    Creativos, sensibles y emocionalmente profundos. 
    Se sienten únicos e intensos, valoran la autenticidad. 
    Tienden a ser introspectivos y a explorar su mundo interior con profundidad.""",

         4: """🔴 Características principales:
    Miedo básico: No tener identidad o significado.
    
    Fortalezas: Creativo, sensible, profundo.
    Debilidades: Melancólico, comparativo, dramático.
    
    Pecado capital: Envidia.
    
    Luz: Autenticidad y expresión emocional profunda.
    Sombra: Victimismo, aislamiento.
    
    Integración (va al 1): Se vuelve más disciplinado y estructurado.
    Desintegración (va al 2): Se vuelve dependiente y complaciente.
    
    Alas: 3 (más orientado al logro) o 5 (más introspectivo).
    
    Tríada: Emocional (Vergüenza).""",   
    
        5: """🟣 Tipo 5 — El Investigador:
    Curiosos, observadores y analíticos. 
    Buscan conocimiento, comprensión y autonomía. 
    Prefieren observar antes que participar y disfrutan de profundizar en temas complejos.""",

        5: """🟣 Características principales:
    Miedo básico: Ser incompetente o incapaz.
    
    Fortalezas: Analítico, observador, independiente.
    Debilidades: Aislado, distante, acumulador de energía.
    
    Pecado capital: Avaricia.
    
    Luz: Sabiduría, claridad mental.
    Sombra: Retraimiento extremo, frialdad.
    
    Integración (va al 8): Se vuelve más decidido y activo.
    Desintegración (va al 7): Se vuelve disperso e impulsivo.
    
    Alas: 4 (más creativo) o 6 (más leal y precavido).
    
    Tríada: Mental (Miedo).""",    

        
        6: """🟠 Tipo 6 — El Leal:
    Personas leales, responsables, cautelosas y con gran sentido de comunidad. 
    Valoran la seguridad, la confianza y la previsibilidad. 
    Pueden preocuparse por posibles riesgos, pero son muy comprometidos.""",

        6: """🟠 Características principales:
    Miedo básico: No tener seguridad ni apoyo.
    
    Fortalezas: Leal, responsable, comprometido.
    Debilidades: Ansioso, desconfiado, dubitativo.
    
    Pecado capital: Miedo (cobardía).
    
    Luz: Valentía y compromiso con la comunidad.
    Sombra: Parálisis por miedo o actitud desafiante constante.
    
    Integración (va al 9): Se vuelve más confiado y tranquilo.
    Desintegración (va al 3): Se vuelve competitivo y orientado a la imagen.
    
    Alas: 5 (más analítico) o 7 (más sociable).
    
    Tríada: Mental (Miedo).""",   

        
        7: """🟤 Tipo 7 — El Entusiasta:
    Activos, optimistas, espontáneos y con deseos de experiencias nuevas. 
    Ayudan a otros a ver el lado positivo de la vida. 
    A veces evitan el dolor y buscan diversión constante.""",

        7: """🟤 Características principales:
    Miedo básico: Sentir dolor o quedar atrapado en el sufrimiento.
    
    Fortalezas: Optimista, creativo, versátil.
    Debilidades: Disperso, impulsivo, evasivo.
    
    Pecado capital: Gula.
    
    Luz: Alegría, entusiasmo, visión positiva.
    Sombra: Huida del dolor, superficialidad.
    
    Integración (va al 5): Se vuelve más profundo y enfocado.
    Desintegración (va al 1): Se vuelve rígido y crítico.
    
    Alas: 6 (más responsable) o 8 (más decidido).
        
    Tríada: Mental (Miedo).""",   
    
        
        8: """🔶 Tipo 8 — El Desafiador:
    Directos, fuertes, protectores y decididos. 
    Buscan controlar su entorno y no temen enfrentar conflictos. 
    Son líderes naturales, enfocados en la justicia y en la acción.""",

        8: """🔶  Características principales:
    Miedo básico: Ser vulnerable o controlado.
    
    Fortalezas: Fuerte, protector, líder natural.
    Debilidades: Dominante, confrontativo, excesivo.
    
    Pecado capital: Lujuria (exceso de intensidad).
    
    Luz: Justicia, protección y liderazgo valiente.
    Sombra: Autoritarismo, agresividad.
    
    Integración (va al 2): Se vuelve más compasivo y protector amoroso.
    Desintegración (va al 5): Se aísla y se vuelve más desconfiado.
    
    Alas: 7 (más entusiasta) o 9 (más conciliador).
    
    Tríada: Instintiva (Ira).""",    
    
        
        9: """🔷 Tipo 9 — El Pacificador:
    Calmados, tranquilos, atentos y conciliadores. 
    Valoran la paz y evitan confrontaciones. 
    Pueden perder su propia agenda para mantener la armonía.""",

        9: """🔷  Características principales:
    Miedo básico: Pérdida de conexión y conflicto.
    
    Fortalezas: Mediador, paciente, estable.
    Debilidades: Indeciso, pasivo, evasivo.
    
    Pecado capital: Pereza (inercia interior).
    
    Luz: Armonía, integración, serenidad.
    Sombra: Desconexión de sí mismo, postergación.
    
    Integración (va al 3): Se vuelve más activo y orientado a metas.
    Desintegración (va al 6): Se vuelve ansioso e inseguro.
    
    Alas: 8 (más firme) o 1 (más estructurado).
    
    Tríada: Instintiva (Ira).""",
    
   
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

