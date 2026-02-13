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

@app.post("/start")
def start_quiz():
    fecha = request.form.get("fecha_nacimiento")
    hora = request.form.get("hora_nacimiento")
    desconozco_hora = request.form.get("hora_desconocida") == "1"

    session["usuario"] = {
        "nombre": request.form.get("nombre"),
        "email": request.form.get("email"),
        "sexo": request.form.get("sexo"),
        "fecha_nacimiento": fecha,
        "hora_nacimiento": None if desconozco_hora else hora,
        "hora_desconocida": desconozco_hora,
    }

    # Inicializar respuestas vacías
    session["answers"] = {}

    return redirect(url_for("quiz_get", page=1))

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
    1: {
        "titulo": "🟡 Tipo 1 — El Reformador",
        "descripcion": """Personas éticas, con fuerte sentido del bien y del mal, buscan mejorar el mundo y la perfección. 
         Son responsables, disciplinadas, y muy exigentes consigo mismas y con los demás. 
         Tienden a autocriticarse y a querer que todo sea “lo correcto”.""",
        "caracteristicas": """El valor del eneatipo 1 radica en la EXCELENCIA. Acción (orden práctico).
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
    Para lograr su evolución es aconsejable que incorpore conductas como la espontaneidad, alegría y flexibilidad,
    evitando la emocionalidad, resentimiento y melancolía.
    Las actitudes que equilibran a la esencia 1 son ser más calmado y más servicial.
    El desarrollo de estas características le permite adquirir ecuanimidad, empatía y colaboración con la gente real, 
    y no sólo por principios y normas: "lo correcto". Busca el orden y la superación con paciencia, tolerancia, comprensión y amorosidad.
    Cuando no se desarrollan, el eneatipo 1 tiende a caer en el pesimismo total, "nada va a cambiar" y/o 
    no se atiende a sí mismo: no toma vacaciones, no descansa, atiende las responsabilidades que asume
    y no sus necesidades.
    Otra de las áreas de expansión es su punto ciego, que es tomar riesgos, mostrarse, exponerse. 
    La esencia 1 se encuentra dentro de la tríada instintiva, es decir, el área de la acción o visceral (expresión). 
    Dosifica planificadamente su energía. Es detallista. Vive en el presente y tiene la necesidad de autonomía.
    Cabe destacar que existen 3 sub-tipos:
    🏠 1 Conservación (Ansiedad): preocupado por hacerlo todo correctamente. Muy autoexigente. Controla detalles, orden y responsabilidad personal.
    👥 1 Social (Rigidez): defiende reglas y principios. Moralista, crítico con el entorno. Siente que debe mejorar el mundo.
    ❤️ 1 Sexual (Celo): más intenso y emocional. Puede ser crítico pero también apasionado. Busca “corregir” al otro.""",         
    "mejorar": """Tener presente que "SIEMPRE no es realmente siempre y NUNCA no son todas las veces".
    Desarrollando tareas creativas, que te incentiven. 
    Dándote tiempo libre para el placer y la relajación. Sintiendo el disfrute.
    Focalizarte en un ideal de vida. Poner las formas en función del fondo.
    Recordar que todos somos uno y perfectos tal como somos.
    Comprender que hay más de una manera correcta de hacer las cosas.
    Practicar el perdón con uno mismo y los demás. Tratarte con menos rigor.
    Parar, darse tiempos. Soltarse y soltar.
    Dejarse llevar por la corriente.
    Confiar en las buenas intenciones de los demás.
    Apreciar a las demás personas, atender a los deseos de los demás genuinamente,
    ayudar a los demás a tomar decisiones.
    El objetivo de la vida es ser humano, no perfecto.""",        
},       
2: {
    "titulo": "🔵 Tipo 2 — El Ayudador",
    "descripcion": """Empáticos, cálidos y orientados a servir a otros. 
    Encuentran satisfacción ayudando y siendo necesarios para quienes quieren. 
    Pueden descuidar sus propias necesidades al priorizar las de otros.""",
    "caracteristicas": """El valor del eneatipo 2 radica en la CONEXIÓN EMOCIONAL. Dar.
    Su mayor contribución es identificar el talento, delegar eficazmente, y entregar feedback. Es un COORDINADOR. 
    Puede crear una atmósfera negativa, manipular y estar orientado a los conflictos. 
    Sus conductas recurrentes pueden ser agradar, ayudar, adular y buscar. 
    Desarrolla hábitos como descuido de las propias necesidades y dificultad para poner límites. 
    El resultado de estas conductas y hábitos es sentirse usado, vacío y frustrado. 
    La creencia arraigada en su interior es "el mundo es un lugar donde es necesario dar para recibir".
    El miedo básico es no ser amado o necesario.
    Sus principales fortalezas son generoso, empático, afectuoso. Y sus áreas de mejora radican en 
    dependiencia, complacencia y la manipulación sutil.
    El pecado capital del eneatipo 2 es la soberbia u orgullo. 
    En su lado luz representa amor genuino y servicio desinteresado.
    En su lado sombra desarrolla un dar para recibir e invasión emocional.
    Cabe destacar que existen 3 sub-tipos:
    🏠 2 Conservación (Privilegio): Busca ser indispensable. Ayuda para asegurarse amor y protección.
    👥 2 Social (Ambición): Quiere ser querido y reconocido socialmente. Seductor social.
    ❤️ 2 Sexual (Conquista): Más intenso y posesivo. Seduce para asegurar vínculo exclusivo.""",
    "mejorar": """Aprender a decir que NO con asertividad. 
    Comprendiendo que todos somos amados por lo que somos, no por lo que damos y
    que en último término las personas siempre satisfacen sus necesidades. 
    Comprendiendo que ser amado no depende de cambiar para complacer a los demás. 
    Mantener claro quién eres realmente. 
    Prestar atención a tus deseos y necesidades y atenderlos. 
    Reconocer que no eres indispensable y que eso está bien.
    No ayudar cuando la persona no lo pide.
    Permitir que te ayuden.
    Aprender que existe un orden del cual eres parte.
    Conseguir grandes cosas atendiendo proyectos propios. 
    Dejar de estar excesivamente pendiente de las necesidades ajenas.""",
},
  
3: {
    "titulo": "🟢 Tipo 3 — El Triunfador",
    "descripcion": """Energéticos, adaptables y orientados al éxito. 
    Se enfocan en metas, logros y reconocimiento. 
    Suelen inspirar a otros con su energía, aunque pueden priorizar imagen y resultados.""",
    "caracteristicas": """Miedo básico: Ser un fracaso o no valer.
    Fortalezas: Eficiente, adaptable, motivador.
    Debilidades: Vanidoso, competitivo, desconectado emocionalmente.
    Pecado capital: Vanidad.
    En su lado luz es inspirador, productivo y ejemplo de superación.
    En su lado sombra puede basar su identidad en la imagen.
    Cabe destacar las alas:
    🟢 3 con ala 2: Más sociable y enfocado en relaciones.
    🟢 3 con ala 4: Más creativo y expresivo.""",
    "mejorar": """¿Cómo puedes sentirte mejor?:
    Centrando tu atención en tus valores internos en lugar de la imagen.
    Practicando la autenticidad sobre la apariencia.
    Valorando tus logros sin depender de la aprobación externa.
    Fomentando la empatía y la conexión genuina.
    Permitirte descansar sin sentir culpa.
    Equilibrar productividad con presencia y gratitud.""",
},
        
4: {
    "titulo": "🔴 Tipo 4 — El Individualista",
    "descripcion": """Creativos, sensibles y emocionalmente profundos. 
    Se sienten únicos e intensos, valoran la autenticidad. 
    Tienden a ser introspectivos y a explorar su mundo interior con profundidad.""",
    "caracteristicas": """Miedo básico: No tener identidad o significado.
    Fortalezas: Creativo, sensible, profundo.
    Debilidades: Melancólico, comparativo, dramático.
    Pecado capital: Envidia.
    En su lado luz se expresa con autenticidad emocional profunda.
    En su sombra puede caer en victimismo o aislamiento.
    Alcanzan equilibrio entre estructura y expresión personal.
    Alas:
    🔴 4 con ala 3: Más orientado al logro.
    🔴 4 con ala 5: Más introspectivo y cerebral.""",
    "mejorar": """¿Cómo puedes sentirte mejor?:
    Cultivando la disciplina personal y la estructura.
    Aprendiendo a aceptar tus emociones sin quedarte atrapado en ellas.
    Fomentando la creatividad con propósito.
    Practicando gratitud y conexión con otros.
    Explorando logros tangibles además del mundo interior.""",
},

5: {
    "titulo": "🟣 Tipo 5 — El Investigador",
    "descripcion": """Curiosos, observadores y analíticos. Buscan conocimiento, comprensión y autonomía. 
    Prefieren observar antes que participar y disfrutan de profundizar en temas complejos.""",
    "caracteristicas": """Miedo básico: Ser incompetente o incapaz.
    Fortalezas: Analítico, observador, independiente.
    Debilidades: Aislado, distante, retraído.
    Pecado capital: Avaricia.
    En su lado luz se expresa con sabiduría y claridad mental.
    En su sombra puede caer en retraimiento extremo o frialdad.
    Cabe destacar alas:
    🟣 5 con ala 4: Más creativo.
    🟣 5 con ala 6: Más precavido y leal.""",
    "mejorar": """¿Cómo puedes sentirte mejor?:
    Integrando acción deliberada y participación social.
    Cultivando conexiones con otros sin perder tu independencia.
    Practicando compartir tu conocimiento con humildad.
    Balanceando reflexión con experiencia directa.""",
},
        
6: {
    "titulo": "🟠 Tipo 6 — El Leal",
    "descripcion": """Personas leales, responsables, cautelosas y con gran sentido de comunidad. 
    Valoran la seguridad, la confianza y la previsibilidad. 
    Pueden preocuparse por posibles riesgos, pero son muy comprometidos.""",
    "caracteristicas": """Miedo básico: No tener seguridad ni apoyo.
    Fortalezas: Leal, responsable, comprometido.
    Debilidades: Ansioso, desconfiado, dubitativo.
    Pecado capital: Miedo.
    En su lado luz se expresa con valentía y compromiso con la comunidad.
    En su sombra puede caer en parálisis por miedo.
    Cabe destacar alas:
    🟠 6 con ala 5: Más analítico e introspectivo.
    🟠 6 con ala 7: Más social y adaptable.""",
    "mejorar": """¿Cómo puedes sentirte mejor?:
    Practicando confianza en ti mismo.
    Cultivando cooperación y apertura.
    Aprendiendo a discernir riesgos reales de miedos imaginarios.
    Practicando calma antes que reacción.
    Construyendo seguridad desde el interior.""",
},
        
 7: {
    "titulo": "🟤 Tipo 7 — El Entusiasta",
    "descripcion": """Activos, optimistas, espontáneos y con deseos de experiencias nuevas. 
    Ayudan a otros ver el lado positivo de la vida. A veces evitan el dolor y buscan diversión constante.""",
    "caracteristicas": """Miedo básico: Sentir dolor o quedar atrapado en el sufrimiento.
    Fortalezas: Optimista, creativo, versátil.
    Debilidades: Disperso, impulsivo, evasivo.
    Pecado capital: Gula (deseo de experiencias).
    En su lado luz se expresa con alegría y entusiasmo.
    En su sombra puede evadir el dolor y superficializar experiencias.
    Alas:
    🟤 7 con ala 6: Más responsable y comunitario.
    🟤 7 con ala 8: Más decidido y firme.""",
    "mejorar": """¿Cómo puedes sentirte mejor?:
    Cultivando enfoque y presencia emocional.
    Aceptando el dolor como parte de la vida.
    Desarrollando rutinas que equilibren diversión y responsabilidad.
    Profundizando experiencias en lugar de dispersarlas.""",
},
        
8: {
    "titulo": "🔶 Tipo 8 — El Desafiador",
    "descripcion": """Directos, fuertes, protectores y decididos. 
    Buscan controlar su entorno y no temen enfrentar conflictos. 
    Son líderes naturales, enfocados en la justicia y la acción.""",
    "caracteristicas": """Miedo básico: Ser vulnerable o controlado.
    Fortalezas: Fuerte, protector, líder natural.
    Debilidades: Dominante, confrontativo, excesivo.
    Pecado capital: Lujuria (intensidad).
    En su lado luz se expresa con justicia y liderazgo valiente.
    En su sombra puede volverse autoritario o agresivo.
    Alas:
    🔶 8 con ala 7: Más entusiasta.
    🔶 8 con ala 9: Más conciliador.""",
    "mejorar": """¿Cómo puedes sentirte mejor?:
    Practicando empatía sin perder firmeza.
    Abrazando vulnerabilidad como fuerza interna.
    Equilibrando poder con compasión.
    Construyendo confianza sin confrontación innecesaria.""",
},
        
9: {
    "titulo": "🔷 Tipo 9 — El Pacificador",
    "descripcion": """Calmados, tranquilos, atentos y conciliadores. 
    Valoran la paz y evitan confrontaciones. 
    Pueden perder su propia agenda personal para mantener la armonía.""",
    "caracteristicas": """Miedo básico: Pérdida de conexión y conflicto.
    Fortalezas: Mediador, paciente, estable.
    Debilidades: Indeciso, pasivo, evasivo.
    Pecado capital: Pereza (inercia interior).
    En su lado luz se expresa con armonía y serenidad.
    En su sombra puede desconectarse de sí mismo.
    Alas:
    🔷 9 con ala 8: Más firme.
    🔷 9 con ala 1: Más estructurado.""",
    "mejorar": """¿Cómo puedes sentirte mejor?:
    Practicando afirmación personal sin necesidad de evitar confrontaciones.
    Cultivando claridad y enfoque.
    Ejercitando toma de decisiones conscientes.
    Integrando presencia activa con serenidad interior.""",
}
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

