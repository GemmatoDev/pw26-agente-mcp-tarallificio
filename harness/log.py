import json
from datetime import datetime
from pathlib import Path

# cartella logs nella radice del repo
CARTELLA = Path(__file__).resolve().parent.parent / "logs"

# scrivo un passo del ciclo come una riga json
def scrivi(stato, tipo, **dati):
    CARTELLA.mkdir(exist_ok=True)
    riga = {"ora": datetime.now().isoformat(timespec="seconds"), "sessione": stato["sessione"], "tipo": tipo}
    riga.update(dati)
    with open(CARTELLA / "ciclo.jsonl", "a", encoding="utf-8") as file:
        file.write(json.dumps(riga, ensure_ascii=False) + "\n")