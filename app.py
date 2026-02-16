import json
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session

DATA_PATH = Path("data/questions.json")

app = Flask(__name__)
app.secret_key = "CHANGE_ME_IN_HEROKU"  # luego lo ponemos por variable de entorno

ALAS = {
    1: (9, 2),
    2: (1, 3),
    3: (2, 4),
    4: (3, 5),
    5: (4, 6),
    6: (5, 7),
    7: (6, 8),
    8: (7, 9),
    9: (8, 1),
}

DESCRIPCION_ALAS = {
    "1w9": "Más tranquilo, idealista, moral, reservado.",
    "1w2": "Más servicial, orientado a ayudar, más expresivo.",
    "2w1": "Más responsable, ético, estructurado.",
    "2w3": "Más sociable, carismático, orientado al éxito.",
    "3w2": "Encantador, enfocado en la imagen y relaciones.",
    "3w4": "Más introspectivo, creativo, busca autenticidad.",
    "4w3": "Más expresivo, artístico, orientado a destacar.",
    "4w5": "Más introspectivo, profundo, reservado.",
    "5w4": "Creativo, sensible, más emocional.",
    "5w6": "Analítico, estratégico, más racional y cauteloso.",
    "6w5": "Más intelectual, prudente, observador.",
    "6w7": "Más sociable, inquieto, busca seguridad en grupos.",
    "7w6": "Más responsable y colaborador.",
    "7w8": "Más fuerte, independiente y dominante.",
    "8w7": "Más enérgico, impulsivo, expansivo.",
    "8w9": "Más calmado, protector, firme pero estable.",
    "9w8": "Más firme, protector, práctico.",
    "9w1": "Más idealista, organizado y correcto.",
}

VIRTUDES_POR_TIPO = {
    1: "Organizar",
    2: "Escuchar",
    3: "Arriesgar",
    4: "Emocionar",
    5: "Razonar",
    6: "Asegurar",
    7: "Hablar",
    8: "Ejecutar",
    9: "Presente en el aquí y ahora",
}

EJES_SIMETRIA = {
    "SER": {"tipos": [4, 5], "antidoto": "Participar"},
    "TENER": {"tipos": [3, 6], "antidoto": "Relajación"},
    "COMUNICAR": {"tipos": [2, 7], "antidoto": "Diálogo"},
    "HACER": {"tipos": [1, 8], "antidoto": "Consenso"},
    "ESTAR": {"tipos": [9], "antidoto": "Compromiso"},
}

ORDEN_EJES = ["HACER", "COMUNICAR", "TENER", "SER", "ESTAR"]
MEDIA_TEO = 11.1
TOL = 0.1  # permite 11.0–11.2 como “equilibrado/desarrollado”

def es_desarrollado(valor: float) -> bool:
    return valor >= (MEDIA_TEO - TOL)

def es_bajo(valor: float) -> bool:
    return valor < (MEDIA_TEO - TOL)

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

def clasificar_eje(valor_redondeado_1d: float) -> str:
    """
    Regla: equilibrado SOLO si da 11.1 (con redondeo a 1 decimal).
    """
    v = valor_redondeado_1d
    if v < 8:
        return "no_desarrollado"
    if 8 <= v <= 10.9:
        return "bajo_leve"
    if abs(v - 11.1) <= 0.1:
        return "equilibrado"
    if 11.2 <= v <= 14:
        return "alto_leve"
    if 14 < v <= 20:
        return "elevado"
    return "excesivo"


def juntar_lista_humana(items):
    items = [x for x in items if x]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} y {items[1]}"
    return ", ".join(items[:-1]) + f" y {items[-1]}"


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

    # Transformar a porcentajes (sobre total_marked)
    porcentaje_scores = {}
    for tipo, score in scores.items():
        porcentaje = (score / total_marked * 100) if total_marked > 0 else 0
        porcentaje_scores[tipo] = round(porcentaje, 1)
       
    # ✅ NUEVO: labels/values para el radar (en orden 1..9)
    labels = [str(i) for i in range(1, 10)]
    values = [porcentaje_scores[i] for i in range(1, 10)]

        # -----------------------------
    # Ejes de equilibrio (promedio)
    # -----------------------------
    ejes = []
    for eje in ORDEN_EJES:
        cfg = EJES_SIMETRIA[eje]
        tipos = cfg["tipos"]
        antidoto = cfg["antidoto"]

        # promedio de porcentajes (regla tuya)
        prom = sum(porcentaje_scores[t] for t in tipos) / len(tipos)
        prom = round(prom, 1)

        estado = clasificar_eje(prom)

        virtudes = [VIRTUDES_POR_TIPO[t] for t in tipos]
        ejes.append({
            "eje": eje,
            "valor": prom,
            "estado": estado,
            "antidoto": antidoto,
            "virtudes": virtudes,
            "tipos": tipos,
        })

    # -----------------------------
    # Texto: Análisis de Ejes
    # -----------------------------
    analisis_ejes_parrafos = []
    for item in ejes:
        eje = item["eje"]
        v = item["valor"]
        est = item["estado"]
        antidoto = item["antidoto"]

    if eje == "HACER":
        if es_bajo(v):
            base = (
                "El eje del HACER aparece por debajo de la media, lo que indica que "
                "hay algo urgente que necesita ponerse en acción. En esta etapa, el desafío es "
                "dejar de evaluar o postergar y hacer lo que debas hacer para avanzar."
                f" Antídoto: {antidoto}."
            )
        else:
            base = (
                "El eje del HACER se encuentra por encima de la media, indicando una marcada orientación "
                "a la acción, ejecución y control. En su luz, esto implica claridad sobre tu ideal de vida "
                "y capacidad de concretar; en su sombra, puede traducirse en controlarte y controlar el entorno "
                "de forma permanente."
            )
            if est in ("elevado", "excesivo"):
                base += f" Si esta energía se intensifica, conviene moderarla. Antídoto: {antidoto}."
        analisis_ejes_parrafos.append(base)
        continue

    if eje == "COMUNICAR":
        if es_bajo(v):
            base = (
              "El eje del COMUNICAR aparece por debajo de la media, lo que indica que "
              "hay algo importante que no estás diciendo o expresando. Esto se vincula con tu mundo interno: "
              "aunque tema las consecuencias, comunicar lo esencial es parte de tu sanación."
              f" Antídoto: {antidoto}."
            )
        else:
            base = (
              "El eje del COMUNICAR se encuentra por encima de la media. En su luz, "
              "indica una buena capacidad de comunicación: saber escuchar, llegar al otro y conectar con empatía; "
              "en su sombra, puede aparecer hablar mucho sin decir lo esencial."
            )
            # si está muy alto, sugerimos moderar
            if item["estado"] in ("elevado", "excesivo"):
                base += f" Antídoto: {antidoto}."
        analisis_ejes_parrafos.append(base)
        continue


    if eje == "TENER":
        if es_bajo(v):
            base = (
                "El eje del TENER aparece por debajo de la media, lo que sugiere una carencia en la forma "
                "de sostener recursos, seguridad y valoración interna. Esto puede expresarse como dificultad "
                "para reconocer tu propio valor, ordenar prioridades, poner precio/cobrar, administrar o pedir lo "
                "que necesitás sin culpa."
                f" Antídoto: {antidoto}."
            )
        else:
            base = (
                "El eje del TENER se encuentra por encima de la media. En su luz, indica capacidad para trabajar, "
                "lograr y alcanzar lo que querés, con decisión y empuje; en su sombra, puede llevar a desatender lo "
                "afectivo, lo físico o lo espiritual por una preocupación excesiva por el tener."
            )
            if est in ("elevado", "excesivo"):
                base += f" Si se intensifica, practicá moderación. Antídoto: {antidoto}."
        analisis_ejes_parrafos.append(base)
        continue


    if eje == "SER":
        if es_bajo(v):
            base = (
                "El eje del SER aparece por debajo de la media, indicando que hay un llamado a profundizar: "
                "mirarte a vos misma y a tu realidad con más honestidad y reflexión. No se trata de aislarse, "
                "sino de hacer un trabajo de introspección que te devuelva claridad y sentido."
                f" Antídoto: {antidoto}."
            )
        else:
            base = (
                "El eje del SER se encuentra por encima de la media. En su luz, indica profundidad y reflexión, "
                "una buena mirada de la vida y de vos misma; en su sombra, puede traducirse en encerrarte, "
                "aislarte o esconderte, evitando mirar una parte de tu realidad que no te gusta."
            )
            if est in ("elevado", "excesivo"):
                base += f" Si se intensifica, cuidá no aislarte. Antídoto: {antidoto}."
        analisis_ejes_parrafos.append(base)
        continue

    if eje == "ESTAR":
        if es_bajo(v):
            base = (
                "El eje del ESTAR aparece por debajo de la media, indicando dificultad para habitar el presente: "
                "podés estar pendiente del pasado o del futuro, o viviendo con tensión. El desafío evolutivo es "
                "aprender a estar aquí y ahora, sosteniendo tu centro."
                f" Antídoto: {antidoto}."
            )
        else:
            base = (
                "El eje del ESTAR se encuentra por encima de la media. En su luz, indica presencia y capacidad de "
                "vivir el presente con intensidad; en su sombra, puede aparecer una forma de 'estar sin estar': "
                "se evita el conflicto o se busca que no haya problemas, pero internamente no hay presencia real."
            )
            if est in ("elevado", "excesivo"):
                base += f" Si se intensifica, buscá presencia genuina. Antídoto: {antidoto}."
        analisis_ejes_parrafos.append(base)
        continue


    # -----------------------------
    # Texto: Síntesis Evolutiva
    # -----------------------------
    ejes_bajos = [x for x in ejes if x["valor"] < MEDIA_TEO]
    ejes_virtud = [x for x in ejes if x["valor"] >= MEDIA_TEO and x["estado"] in ("equilibrado", "alto_leve")]
    ejes_moderar = [x for x in ejes if x["estado"] in ("elevado", "excesivo")]

    # virtudes de desafío (sin repetir, manteniendo orden)
    # ejes bajos (por promedio del eje)
    ejes_bajos = [x for x in ejes if es_bajo(x["valor"])]
    
    virtudes_desafio = []
    antidotos_desafio = []
    ejes_desafio_nombres = []
    
    for x in ejes_bajos:
        ejes_desafio_nombres.append(x["eje"])
        antidotos_desafio.append(x["antidoto"])
    
        # ✅ SOLO virtudes de los TIPOS que están por debajo de la media
        for t in x["tipos"]:
            if es_bajo(porcentaje_scores[t]):
                v = VIRTUDES_POR_TIPO[t]
                if v not in virtudes_desafio:
                    virtudes_desafio.append(v)


    virtudes_principales = []
    ejes_principales_nombres = []
    
    for x in ejes:
        # desarrollados = >= media (incluye equilibrado)
        if es_desarrollado(x["valor"]) and x["estado"] in ("equilibrado", "alto_leve"):
            ejes_principales_nombres.append(x["eje"])
    
        # ✅ virtudes por TIPO desarrollado (no por eje)
        for t in x["tipos"]:
            if es_desarrollado(porcentaje_scores[t]):
                v = VIRTUDES_POR_TIPO[t]
                if v not in virtudes_principales:
                    virtudes_principales.append(v)


    # moderación
    antidotos_moderar = []
    ejes_moderar_nombres = []
    for x in ejes_moderar:
        ejes_moderar_nombres.append(x["eje"])
        antidotos_moderar.append(x["antidoto"])

    sintesis_parrafos = []

    if ejes_desafio_nombres:
        p1 = (
            f"Aquí se encuentra tu principal desafío evolutivo en los ejes del "
            f"{juntar_lista_humana(ejes_desafio_nombres)}. "
            f"Las virtudes a desarrollar son {juntar_lista_humana(virtudes_desafio)}, "
            f"integrando profundidad interior con expresión auténtica."
        )
        # Antídotos oficiales del modelo
        p1 += f" Antídotos: {juntar_lista_humana(list(dict.fromkeys(antidotos_desafio)))}."
        sintesis_parrafos.append(p1)

    if ejes_principales_nombres:
        p2 = (
            f"Tus principales virtudes se manifiestan en los ejes del "
            f"{juntar_lista_humana(ejes_principales_nombres)}, "
            f"donde destacan tu capacidad de {juntar_lista_humana(virtudes_principales)}."
        )
        sintesis_parrafos.append(p2)

    if ejes_moderar_nombres:
        p3 = (
            f"Estas cualidades constituyen pilares de tu estructura personal, "
            f"aunque será importante moderarlas cuando se intensifiquen en exceso. "
            f"Antídotos: {juntar_lista_humana(list(dict.fromkeys(antidotos_moderar)))}."
        )
        sintesis_parrafos.append(p3)




    
    # Eneatipo principal
    max_score = max(scores.values()) if scores else 0
    top_types = [t for t, s in scores.items() if s == max_score and max_score > 0]
    
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    sorted_porcentajes = [(t, porcentaje_scores[t]) for (t, _) in sorted_scores]

    # -----------------------------
    # Ala (Wing) del tipo principal
    # -----------------------------
    ala_textos = []
    
    if top_types:
        principal = top_types[0]
    
        izq, der = ALAS[principal]
        pct_izq = porcentaje_scores.get(izq, 0)
        pct_der = porcentaje_scores.get(der, 0)
    
        if pct_izq > pct_der:
            clave = f"{principal}w{izq}"
            txt = DESCRIPCION_ALAS.get(clave)
            if txt:
                ala_textos = [txt]
        elif pct_der > pct_izq:
            clave = f"{principal}w{der}"
            txt = DESCRIPCION_ALAS.get(clave)
            if txt:
                ala_textos = [txt]
        else:
            # empate -> mostrar ambas descripciones (una por línea)
            clave1 = f"{principal}w{izq}"
            clave2 = f"{principal}w{der}"
            txt1 = DESCRIPCION_ALAS.get(clave1)
            txt2 = DESCRIPCION_ALAS.get(clave2)
            ala_textos = [t for t in (txt1, txt2) if t]



    
    eneatipo_textos = {
    1: {
        "titulo": "🟡 Tipo 1 — El Reformador",
        "descripcion": """Personas éticas, con fuerte sentido del bien y del mal, buscan mejorar el mundo y la perfección. 
         Son responsables, disciplinadas, y muy exigentes consigo mismas y con los demás. 
         Tienden a autocriticarse y a querer que todo sea “lo correcto”.""",
    "caracteristicas": """El valor del eneatipo 1 radica en la EXCELENCIA. Acción (orden práctico).
    
    Su mayor contribución es localizar errores, pulir y perfeccionar. Es un FINALIZADOR. Posee buena orientación al detalle, es reacio a delegar, y puede desarrollar una preocupación excesiva. Es prolijo y ordenado; no le gusta que le cambien de lugar sus cosas.
    
    Sus conductas recurrentes pueden ser: controlar, corregir, juzgar, criticar. Desarrolla hábitos como buscar culpables, corregir errores y tener la razón. El resultado de estas conductas y hábitos es un predominio del deber sobre el placer.
    
    La creencia arraigada en su interior es: "el mundo es un lugar imperfecto para perfeccionar". El miedo básico es ser corrupto, defectuoso o moralmente incorrecto. Su miedo constitutivo a no poder le genera la necesidad de ser fuerte, y la reacción ante este miedo es controlar.
    
    Sus principales fortalezas son ser ético, disciplinado, responsable y justo. Sus principales áreas de mejora radican en ser crítico, rígido, autoexigente e intolerante. El pecado capital del eneatipo 1 es la ira (reprimida).
    
    En su lado luz representa integridad, mejora del mundo y coherencia. En su lado sombra desarrolla un juicio constante y un perfeccionismo paralizante.
    
    Para lograr su evolución es aconsejable incorporar espontaneidad, alegría y flexibilidad, evitando emocionalidad, resentimiento y melancolía. Las actitudes que equilibran a la esencia 1 son ser más calmado y más servicial.
    
    El desarrollo de estas características le permite adquirir ecuanimidad, empatía y colaboración con la gente real (y no sólo por principios y normas: "lo correcto"). Busca el orden y la superación con paciencia, tolerancia, comprensión y amorosidad.
    
    Cuando no se desarrollan, el eneatipo 1 tiende a caer en el pesimismo total ("nada va a cambiar") y/o no se atiende a sí mismo: no toma vacaciones, no descansa, atiende las responsabilidades que asume y no sus necesidades.
    
    Otra de las áreas de expansión es su punto ciego: tomar riesgos, mostrarse, exponerse. La esencia 1 se encuentra dentro de la tríada instintiva (área de la acción o visceral, expresión). Dosifica planificadamente su energía. Es detallista, vive en el presente y tiene necesidad de autonomía.
    
    Cabe destacar que existen 3 subtipos:
    🏠 1 Conservación: busca seguridad, recursos y estabilidad. Puede desarrollar ansiedad: preocupado por hacerlo todo correctamente. Muy autoexigente. Controla detalles, orden y responsabilidad personal.
    👥 1 Social: busca grupo, pertenencia e imagen social. Puede desarrollar rigidez: defiende reglas y principios. Moralista, crítico con el entorno. Siente que debe mejorar el mundo.
    ❤️ 1 Sexual: busca intensidad y conexión profunda. Sus relaciones son uno a uno, es selectivo. Puede desarrollar celo: más intenso y emocional. Puede ser crítico pero también apasionado. Busca “corregir” al otro.""",

    "orientacion":"""    
    🎯 Vocación base
    
    Derecho / justicia
    
    Ingeniería de procesos / calidad
    
    Docencia
    
    Gestión institucional
    
    Medio ambiente
    
    Auditoría
    
    Trabajos donde puedan mejorar sistemas.
    
    🔁 Según subtipo
    
    🟢 Conservación (perfeccionista silencioso)
    – Contabilidad
    – Ingeniería industrial
    – Normativas / compliance
    – Medicina clínica
    
    🔵 Social (idealista moral)
    – Política pública
    – ONG
    – Educación
    – Dirección institucional
    
    🔴 Sexual (intenso reformador)
    – Activismo
    – Liderazgo de cambios
    – Coaching transformacional
    
    🌱 Clave evolutiva
    
    Aprender trabajos donde haya margen de error y creatividad.""",        
    "mejorar": """Tener presente que "SIEMPRE no es realmente siempre y NUNCA no son todas las veces".

    • Desarrollar tareas creativas que te incentiven.
    • Darte tiempo libre para el placer y la relajación, sintiendo el disfrute.
    • Focalizarte en un ideal de vida: poner las formas en función del fondo.
    • Recordar que todos somos uno y perfectos tal como somos.
    • Comprender que hay más de una manera correcta de hacer las cosas.
    • Practicar el perdón con uno mismo y con los demás. Tratarte con menos rigor.
    • Parar y darte tiempos. Soltarte y soltar.
    • Dejarte llevar por la corriente.
    • Confiar en las buenas intenciones de los demás.
    • Apreciar a las demás personas y atender sus deseos genuinamente.
    • Ayudar a los demás a tomar decisiones.
    
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
    creencias_limitantes = {
        1: "Miedo a PERDER LA LIBERTAD por quedar atrapado en estructuras o situaciones que me asfixian (trabajo, pareja, etc).",
        2: "Miedo a ABRIRME AFECTIVAMENTE, por que puedo sufrir.",
        3: "Miedo a FRACASAR, por lo que no estoy haciendo lo que tengo que hacer para lograr el desarrollo personal.",
        4: "Miedo a MIRARME A MI MISMO, porque hay algo de mí que no me gusta ver, o que no puedo cambiar (culpa del pasado, baja autoestima, etc).",
        5: "Miedo a SUFRIR POR ALGO QUE NO QUIERO O NO PUEDO VER O ACEPTAR, algo de mi realidad que me duele, no está superado, o no sé qué es, pero me molesta.",
        6: "Miedo a PERDER LA LIBERTAD por quedar atrapado en obligaciones o compromisos que se ha creado uno mismo.",
        7: "Miedo a DISFRUTAR, por no poder soltar cosas o situaciones por exceso de responsabilidades y por temor a perder el control (mal concepto de la alegría).",
        8: "Miedo a TOMAR UNA DECISIÓN, por las consecuencias que va atraer o traerme y no saber decir que basta o que no. Hay algo a lo cual no le estoy diciendo que no.",
        9: "Miedo a PARAR, porque si paro, ¿quién se hace cargo de todo lo que me hago cargo yo?, es una manera de seguir adicto a la actividad.",
    }

    # Ranking de los 3 tipos con menor porcentaje
    # (si total_marked == 0, todos dan 0; en ese caso igual mostramos 1..9 ordenados)
    low3 = sorted(porcentaje_scores.items(), key=lambda x: (x[1], x[0]))[:3]

    # Lista lista para el template: [(tipo, porcentaje, texto), ...]
    camino_evolucion = [
        (tipo, pct, creencias_limitantes[tipo]) for tipo, pct in low3
    ]

    return render_template(
        "result.html",
        sorted_scores=sorted_scores,
        sorted_porcentajes=sorted_porcentajes,
        top_types=top_types,
        max_score=max_score,
        total_marked=total_marked,
        eneatipo_textos=eneatipo_textos,
        labels=labels,
        values=values,
        camino_evolucion=camino_evolucion,
        analisis_ejes_parrafos=analisis_ejes_parrafos,
        sintesis_parrafos=sintesis_parrafos,

    )
