import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from mcp import Client

from harness import ciclo
from harness.client_mcp import SERVER
from harness.log import CARTELLA
from harness.providers import crea_provider

MODELLI = ["qwen3:8b", "gemma4:e4b", "groq/openai/gpt-oss-120b"]

templates = Jinja2Templates(directory=Path(__file__).resolve().parent / "templates")

# richieste ferme in attesa della conferma divise per sessione
in_attesa = {}

# apro il server mcp una volta sola quando parte la web
@asynccontextmanager
async def avvio(app):
    async with Client(SERVER) as client:
        app.state.client = client
        yield

app = FastAPI(lifespan=avvio)

# logo e immagini della pagina
app.mount("/static", StaticFiles(directory=Path(__file__).resolve().parent / "static"), name="static")

# passi della sessione presi dal log
def leggi_passi(sessione):
    passi = []
    with open(CARTELLA / "ciclo.jsonl", encoding="utf-8") as file:
        for riga in file:
            passo = json.loads(riga)
            if passo["sessione"] != sessione or passo["tipo"] in ["richiesta", "fine"]:
                continue
            dettaglio = passo.get("tool", "")
            if passo["tipo"] == "modello":
                dettaglio = f"{passo['secondi']} s, {passo['token_input']} in, {passo['token_output']} out"
            if passo["tipo"] == "tool" and passo["errore"]:
                dettaglio += " (errore)"
            if passo["tipo"] == "conferma":
                dettaglio += " sì" if passo["confermato"] else " no"
            passi.append((passo["ora"][11:], passo["tipo"], dettaglio))
    return passi

# preparo la pagina con il risultato del ciclo
def mostra(request, risultato, richiesta, modello, provider):
    if risultato["esito"] == "attesa_conferma":
        sessione = risultato["stato"]["sessione"]
        in_attesa[sessione] = (risultato["stato"], provider, richiesta, modello)
    else:
        sessione = risultato["sessione"]
    return templates.TemplateResponse(request, "index.html", {
        "modelli": MODELLI,
        "modello": modello,
        "richiesta": richiesta,
        "risultato": risultato,
        "sessione": sessione,
        "passi": leggi_passi(sessione),
    })

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {"modelli": MODELLI, "modello": MODELLI[0]})

@app.post("/chiedi")
async def chiedi(request: Request, richiesta: str = Form(...), modello: str = Form(...)):
    provider = crea_provider(modello)
    risultato = await ciclo.esegui_ciclo(richiesta, provider, request.app.state.client)
    return mostra(request, risultato, richiesta, modello, provider)

@app.post("/conferma")
async def conferma(request: Request, sessione: str = Form(...), scelta: str = Form(...)):
    stato, provider, richiesta, modello = in_attesa.pop(sessione)
    risultato = await ciclo.riprendi(stato, scelta == "si", provider, request.app.state.client)
    return mostra(request, risultato, richiesta, modello, provider)
