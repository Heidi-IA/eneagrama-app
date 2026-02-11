import json
from pathlib import Path

import pandas as pd

INPUT_XLSX = Path("data/source.xlsx")
OUTPUT_JSON = Path("data/questions.json")


def is_int_like(x) -> bool:
    try:
        if pd.isna(x):
            return False
        int(float(x))
        return True
    except Exception:
        return False


def to_int(x) -> int:
    return int(float(x))


def build_type_map_from_eneagrama(xlsx_path: Path) -> dict[int, int]:
    """
    ENEAGRAMA: tiene bloques repetidos con columnas:
      Respuesta | Tipología | (1..9) ...
    Usamos Respuesta (id) + Tipología (eneatipo).
    """
    raw = pd.read_excel(xlsx_path, sheet_name="ENEAGRAMA", header=None)

    # Header real: en tu preview, fila 0 tiene "Respuesta" y "Tipología"
    header = raw.iloc[0].astype(str).str.strip().str.lower().tolist()

    pairs = []
    for i, val in enumerate(header):
        if val == "respuesta":
            if i + 1 < len(header) and header[i + 1].startswith("tipolog"):
                pairs.append((i, i + 1))

    if not pairs:
        raise RuntimeError("No encontré columnas 'Respuesta' y 'Tipología' en ENEAGRAMA.")

    type_map: dict[int, int] = {}

    # Datos empiezan después de la fila donde aparecen 1..9 (en tu preview es fila 1).
    for r in range(2, len(raw)):
        for resp_col, tipo_col in pairs:
            resp = raw.iat[r, resp_col]
            tipo = raw.iat[r, tipo_col]

            if is_int_like(resp) and is_int_like(tipo):
                rid = to_int(resp)
                t = to_int(tipo)
                if 1 <= rid <= 500 and 1 <= t <= 9:
                    type_map[rid] = t

    return type_map


def build_questions_from_afirmaciones(xlsx_path: Path) -> list[dict]:
    """
    AFIRMACIONES: afirmaciones en filas 30..299 (Excel 1-based).
      - col 0: id
      - col 2: texto
    """
    raw = pd.read_excel(xlsx_path, sheet_name="AFIRMACIONES", header=None)

    # Excel 30..299 -> pandas 29..298
    sub = raw.iloc[29:299].copy()

    questions = []
    for _, row in sub.iterrows():
        qid = row.get(0)
        text = row.get(2)

        if not is_int_like(qid):
            continue
        qid = to_int(qid)

        if not isinstance(text, str):
            continue
        text = text.strip()
        if len(text) < 5:
            continue

        questions.append({"id": qid, "text": text})

    # dedup por id
    dedup = {q["id"]: q for q in questions}
    return [dedup[k] for k in sorted(dedup.keys())]


def main():
    if not INPUT_XLSX.exists():
        raise FileNotFoundError(f"No encuentro {INPUT_XLSX}. Copiá tu Excel ahí.")

    type_map = build_type_map_from_eneagrama(INPUT_XLSX)
    questions = build_questions_from_afirmaciones(INPUT_XLSX)

    joined = []
    missing_type = 0
    for q in questions:
        t = type_map.get(q["id"])
        if t is None:
            missing_type += 1
            continue
        joined.append({"id": q["id"], "text": q["text"], "type": t})

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(
        json.dumps(
            {
                "questions": joined,
                "stats": {
                    "questions_in_afirmaciones": len(questions),
                    "types_in_eneagrama": len(type_map),
                    "joined": len(joined),
                    "missing_type_skipped": missing_type,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        f"OK: generé {OUTPUT_JSON} | AFIRMACIONES={len(questions)} | ENEAGRAMA tipos={len(type_map)} | JOIN={len(joined)} | sin tipo={missing_type}"
    )


if __name__ == "__main__":
    main()
