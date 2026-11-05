import asyncio
import sys

from mcp import Client

from harness.client_mcp import SERVER, esegui_tool, leggi_tool
from harness.providers import OllamaProvider

MAX_ITERAZIONI = 8

SISTEMA = (
    "Sei l'assistente di back-office del CRM di GemmaTaralli, un tarallificio B2B. "
    "Usa i tool per leggere e modificare i dati, non inventarti nulla. Rispondi in italiano, breve e senza emoji."
)

# ciclo agentico
async def esegui_ciclo(richiesta, provider, client):
    tools = await leggi_tool(client)
    messaggi = [
        {"role": "system", "content": SISTEMA},
        {"role": "user", "content": richiesta},
    ]
    token_input = 0
    token_output = 0

    for iterazione in range(1, MAX_ITERAZIONI + 1):
        risposta = provider.chiedi(messaggi, tools)
        token_input += risposta.token_input
        token_output += risposta.token_output

        # nessun tool quindi il modello ha risposto
        if not risposta.chiamate:
            return {"esito": "risposta", "testo": risposta.testo, "iterazioni": iterazione,
                    "token_input": token_input, "token_output": token_output}

        # salvo la risposta con le chiamate per il giro dopo
        messaggi.append({"role": "assistant", "content": risposta.testo, "chiamate": risposta.chiamate})

        # eseguo i tool e passo i risultati
        for chiamata in risposta.chiamate:
            testo, errore = await esegui_tool(client, chiamata["nome"], chiamata["argomenti"])
            messaggi.append({"role": "tool", "nome": chiamata["nome"], "content": testo})

    # limite di giri raggiunto
    return {"esito": "limite_iterazioni", "testo": "", "iterazioni": MAX_ITERAZIONI,
            "token_input": token_input, "token_output": token_output}

# prova da terminale
async def main():
    provider = OllamaProvider("qwen3:8b")
    async with Client(SERVER) as client:
        risultato = await esegui_ciclo(sys.argv[1], provider, client)
    print(risultato["testo"])
    print()
    print("esito:", risultato["esito"], "| iterazioni:", risultato["iterazioni"],
          "| token:", risultato["token_input"], "in,", risultato["token_output"], "out")

if __name__ == "__main__":
    asyncio.run(main())
