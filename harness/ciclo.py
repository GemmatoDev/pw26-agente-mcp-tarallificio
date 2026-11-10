import asyncio
import sys
import time
from datetime import datetime

from mcp import Client

from harness import log
from harness.anteprima import controlla_parametri, prepara_anteprima
from harness.client_mcp import SERVER, esegui_tool, leggi_tool
from harness.providers import crea_provider

MAX_ITERAZIONI = 8

# prima di questi tool serve la conferma dell'utente
DA_CONFERMARE = ["medio", "alto"]

SISTEMA = (
    "Sei l'assistente di back-office del CRM di GemmaTaralli, un tarallificio B2B. "
    "Usa i tool per leggere e modificare i dati, non inventarti nulla. Rispondi in italiano, breve e senza emoji."
)

# parto da una nuova richiesta
async def esegui_ciclo(richiesta, provider, client):
    tools = await leggi_tool(client)
    rischi = {}
    schemi = {}
    for tool in tools:
        rischi[tool["nome"]] = tool["rischio"]
        schemi[tool["nome"]] = tool["schema"]
    stato = {
        "sessione": datetime.now().strftime("%Y%m%d-%H%M%S-%f"),
        "messaggi": [
            {"role": "system", "content": SISTEMA},
            {"role": "user", "content": richiesta},
        ],
        "tools": tools,
        "rischi": rischi,
        "schemi": schemi,
        "in_sospeso": [],
        "iterazione": 0,
        "token_input": 0,
        "token_output": 0,
    }
    log.scrivi(stato, "richiesta", testo=richiesta, modello=provider.modello)
    return await avanza(stato, provider, client)

# riparto dopo la risposta dell'utente sulla conferma
async def riprendi(stato, confermato, provider, client):
    chiamata = stato["in_sospeso"].pop(0)
    log.scrivi(stato, "conferma", tool=chiamata["nome"], confermato=confermato)
    if confermato:
        testo, errore = await esegui_tool(client, chiamata["nome"], chiamata["argomenti"])
    else:
        testo = "Operazione annullata, l'utente non ha confermato."
        errore = False
    log.scrivi(stato, "tool", tool=chiamata["nome"], argomenti=chiamata["argomenti"], risultato=testo, errore=errore)
    stato["messaggi"].append({"role": "tool", "nome": chiamata["nome"], "content": testo})
    return await avanza(stato, provider, client)

# scrivo la fine nel log e restituisco il risultato
def fine(stato, esito, testo):
    log.scrivi(stato, "fine", esito=esito, iterazioni=stato["iterazione"],
               token_input=stato["token_input"], token_output=stato["token_output"])
    return {"esito": esito, "testo": testo, "iterazioni": stato["iterazione"], "sessione": stato["sessione"],
            "token_input": stato["token_input"], "token_output": stato["token_output"]}

# ciclo agentico
async def avanza(stato, provider, client):
    while True:
        # eseguo i tool rimasti dal giro prima
        while stato["in_sospeso"]:
            chiamata = stato["in_sospeso"][0]
            rischio = stato["rischi"].get(chiamata["nome"])

            # tool di scrittura quindi mi fermo e aspetto la conferma
            if rischio in DA_CONFERMARE:
                # parametri sbagliati quindi l'errore torna al modello
                problema = controlla_parametri(chiamata["argomenti"], stato["schemi"][chiamata["nome"]])
                if problema:
                    stato["in_sospeso"].pop(0)
                    log.scrivi(stato, "tool", tool=chiamata["nome"], argomenti=chiamata["argomenti"], risultato=problema, errore=True)
                    stato["messaggi"].append({"role": "tool", "nome": chiamata["nome"], "content": problema})
                    continue

                anteprima = await prepara_anteprima(client, chiamata)
                log.scrivi(stato, "attesa_conferma", tool=chiamata["nome"], argomenti=chiamata["argomenti"],
                           rischio=rischio, anteprima=anteprima)
                return {"esito": "attesa_conferma", "chiamata": chiamata, "rischio": rischio, "anteprima": anteprima,
                        "stato": stato, "iterazioni": stato["iterazione"],
                        "token_input": stato["token_input"], "token_output": stato["token_output"]}

            stato["in_sospeso"].pop(0)
            testo, errore = await esegui_tool(client, chiamata["nome"], chiamata["argomenti"])
            log.scrivi(stato, "tool", tool=chiamata["nome"], argomenti=chiamata["argomenti"], risultato=testo, errore=errore)
            stato["messaggi"].append({"role": "tool", "nome": chiamata["nome"], "content": testo})

        # limite di giri raggiunto
        if stato["iterazione"] >= MAX_ITERAZIONI:
            return fine(stato, "limite_iterazioni", "")

        stato["iterazione"] += 1
        inizio = time.perf_counter()
        # se il fornitore va in errore mi fermo senza far crashare tutto
        try:
            risposta = provider.chiedi(stato["messaggi"], stato["tools"])
        except Exception as errore:
            log.scrivi(stato, "errore_modello", messaggio=str(errore))
            return fine(stato, "errore_modello", str(errore))
        secondi = round(time.perf_counter() - inizio, 2)
        log.scrivi(stato, "modello", iterazione=stato["iterazione"], testo=risposta.testo, chiamate=risposta.chiamate,
                   token_input=risposta.token_input, token_output=risposta.token_output, secondi=secondi)
        stato["token_input"] += risposta.token_input
        stato["token_output"] += risposta.token_output

        # nessun tool quindi il modello ha risposto
        if not risposta.chiamate:
            return fine(stato, "risposta", risposta.testo)

        # salvo la risposta con le chiamate per il giro dopo
        stato["messaggi"].append({"role": "assistant", "content": risposta.testo, "chiamate": risposta.chiamate})
        stato["in_sospeso"] = list(risposta.chiamate)

# prova da terminale
async def main():
    modello = sys.argv[2] if len(sys.argv) > 2 else "qwen3:8b"
    provider = crea_provider(modello)
    async with Client(SERVER) as client:
        risultato = await esegui_ciclo(sys.argv[1], provider, client)

        # chiedo la conferma finché il modello vuole scrivere
        while risultato["esito"] == "attesa_conferma":
            chiamata = risultato["chiamata"]
            print("Il modello vuole usare", chiamata["nome"], "con", chiamata["argomenti"])
            print("Rischio:", risultato["rischio"])
            print("Prima:", risultato["anteprima"]["prima"])
            print("Dopo: ", risultato["anteprima"]["dopo"])
            risposta = input("Confermi? (s/n) ")
            risultato = await riprendi(risultato["stato"], risposta.strip().lower() == "s", provider, client)

    print(risultato["testo"])
    print()
    print("esito:", risultato["esito"], "| iterazioni:", risultato["iterazioni"],
          "| token:", risultato["token_input"], "in,", risultato["token_output"], "out")

if __name__ == "__main__":
    asyncio.run(main())
