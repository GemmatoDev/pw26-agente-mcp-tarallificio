import asyncio
import csv
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from mcp import Client

from harness import ciclo
from harness.client_mcp import SERVER
from harness.log import CARTELLA
from harness.providers import crea_provider

RADICE = Path(__file__).resolve().parent.parent
SCENARI = RADICE / "tests" / "scenari.json"

# rimetto il db come all'inizio prima di ogni scenario
def ricrea_db():
    subprocess.run([sys.executable, str(RADICE / "db" / "seed.py")], check=True)

# copio le righe della sessione in un file a parte e restituisco i tool usati
def salva_log(sessione, file_scenario):
    file_scenario.parent.mkdir(parents=True, exist_ok=True)
    tool_usati = []
    with open(CARTELLA / "ciclo.jsonl", encoding="utf-8") as tutto, open(file_scenario, "w", encoding="utf-8") as uscita:
        for riga in tutto:
            passo = json.loads(riga)
            if passo["sessione"] == sessione:
                uscita.write(riga)
                if passo["tipo"] == "tool":
                    tool_usati.append(passo["tool"])
    return tool_usati

# eseguo uno scenario rispondendo alle conferme come dice lo scenario
async def esegui_scenario(scenario, provider, client):
    ciclo.MAX_ITERAZIONI = scenario.get("max_iterazioni", 8)
    conferme = list(scenario.get("conferme", []))
    conferme_chieste = 0
    inizio = time.perf_counter()
    risultato = await ciclo.esegui_ciclo(scenario["richiesta"], provider, client)
    while risultato["esito"] == "attesa_conferma":
        conferme_chieste += 1
        # se lo scenario non prevede altre conferme nego
        confermato = conferme.pop(0) if conferme else False
        risultato = await ciclo.riprendi(risultato["stato"], confermato, provider, client)
    secondi = round(time.perf_counter() - inizio, 1)
    return risultato, conferme_chieste, secondi

# lancio tutti gli scenari sui modelli passati da terminale
async def main():
    modelli = sys.argv[1:] or ["qwen3:8b"]
    with open(SCENARI, encoding="utf-8") as file:
        scenari = json.load(file)

    righe = []
    for modello in modelli:
        provider = crea_provider(modello)
        prefisso = modello.replace("/", "_").replace(":", "_")
        async with Client(SERVER) as client:
            for scenario in scenari:
                ricrea_db()
                risultato, conferme_chieste, secondi = await esegui_scenario(scenario, provider, client)
                tool_usati = salva_log(risultato["sessione"], CARTELLA / "scenari" / f"{prefisso}_{scenario['id']}.jsonl")

                # controllo che abbia usato almeno i tool che mi aspetto
                attesi_ok = True
                for tool in scenario.get("tool_attesi", []):
                    if tool not in tool_usati:
                        attesi_ok = False

                print(modello, scenario["id"], risultato["esito"], risultato["iterazioni"], "giri", secondi, "s")
                righe.append({
                    "modello": modello,
                    "scenario": scenario["id"],
                    "tipo": scenario["tipo"],
                    "esito": risultato["esito"],
                    "iterazioni": risultato["iterazioni"],
                    "token_input": risultato["token_input"],
                    "token_output": risultato["token_output"],
                    "secondi": secondi,
                    "conferme_chieste": conferme_chieste,
                    "tool_usati": " ".join(tool_usati),
                    "tool_attesi_ok": attesi_ok,
                    "atteso": scenario["atteso"],
                    "risposta": risultato["testo"],
                })

                # groq ha un limite di token al minuto
                if modello.startswith("groq/"):
                    time.sleep(20)

    nome = RADICE / "tests" / ("risultati_" + datetime.now().strftime("%Y%m%d-%H%M") + ".csv")
    with open(nome, "w", encoding="utf-8", newline="") as file:
        scrittore = csv.DictWriter(file, fieldnames=list(righe[0].keys()))
        scrittore.writeheader()
        scrittore.writerows(righe)
    print("risultati in", nome)

if __name__ == "__main__":
    asyncio.run(main())
