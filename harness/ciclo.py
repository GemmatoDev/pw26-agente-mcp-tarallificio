import asyncio
import sys

from mcp import Client

from harness.client_mcp import SERVER, esegui_tool, leggi_tool
from harness.providers import OllamaProvider

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
    for tool in tools:
        rischi[tool["nome"]] = tool["rischio"]
    stato = {
        "messaggi": [
            {"role": "system", "content": SISTEMA},
            {"role": "user", "content": richiesta},
        ],
        "tools": tools,
        "rischi": rischi,
        "in_sospeso": [],
        "iterazione": 0,
        "token_input": 0,
        "token_output": 0,
    }
    return await avanza(stato, provider, client)

# riparto dopo la risposta dell'utente sulla conferma
async def riprendi(stato, confermato, provider, client):
    chiamata = stato["in_sospeso"].pop(0)
    if confermato:
        testo, errore = await esegui_tool(client, chiamata["nome"], chiamata["argomenti"])
    else:
        testo = "Operazione annullata, l'utente non ha confermato."
    stato["messaggi"].append({"role": "tool", "nome": chiamata["nome"], "content": testo})
    return await avanza(stato, provider, client)

# ciclo agentico
async def avanza(stato, provider, client):
    while True:
        # eseguo i tool rimasti dal giro prima
        while stato["in_sospeso"]:
            chiamata = stato["in_sospeso"][0]
            rischio = stato["rischi"].get(chiamata["nome"])

            # tool di scrittura quindi mi fermo e aspetto la conferma
            if rischio in DA_CONFERMARE:
                return {"esito": "attesa_conferma", "chiamata": chiamata, "rischio": rischio,
                        "stato": stato, "iterazioni": stato["iterazione"],
                        "token_input": stato["token_input"], "token_output": stato["token_output"]}

            stato["in_sospeso"].pop(0)
            testo, errore = await esegui_tool(client, chiamata["nome"], chiamata["argomenti"])
            stato["messaggi"].append({"role": "tool", "nome": chiamata["nome"], "content": testo})

        # limite di giri raggiunto
        if stato["iterazione"] >= MAX_ITERAZIONI:
            return {"esito": "limite_iterazioni", "testo": "", "iterazioni": stato["iterazione"],
                    "token_input": stato["token_input"], "token_output": stato["token_output"]}

        stato["iterazione"] += 1
        risposta = provider.chiedi(stato["messaggi"], stato["tools"])
        stato["token_input"] += risposta.token_input
        stato["token_output"] += risposta.token_output

        # nessun tool quindi il modello ha risposto
        if not risposta.chiamate:
            return {"esito": "risposta", "testo": risposta.testo, "iterazioni": stato["iterazione"],
                    "token_input": stato["token_input"], "token_output": stato["token_output"]}

        # salvo la risposta con le chiamate per il giro dopo
        stato["messaggi"].append({"role": "assistant", "content": risposta.testo, "chiamate": risposta.chiamate})
        stato["in_sospeso"] = list(risposta.chiamate)

# prova da terminale
async def main():
    provider = OllamaProvider("qwen3:8b")
    async with Client(SERVER) as client:
        risultato = await esegui_ciclo(sys.argv[1], provider, client)

        # chiedo la conferma finché il modello vuole scrivere
        while risultato["esito"] == "attesa_conferma":
            chiamata = risultato["chiamata"]
            print("Il modello vuole usare", chiamata["nome"], "con", chiamata["argomenti"])
            print("Rischio:", risultato["rischio"])
            risposta = input("Confermi? (s/n) ")
            risultato = await riprendi(risultato["stato"], risposta.strip().lower() == "s", provider, client)

    print(risultato["testo"])
    print()
    print("esito:", risultato["esito"], "| iterazioni:", risultato["iterazioni"],
          "| token:", risultato["token_input"], "in,", risultato["token_output"], "out")

if __name__ == "__main__":
    asyncio.run(main())