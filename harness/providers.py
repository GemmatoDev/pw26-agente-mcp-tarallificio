from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import json

import ollama
from groq import Groq


# risposta del modello, uguale per ogni fornitore
@dataclass
class Risposta:
    testo: str
    chiamate: list[dict] = field(default_factory=list)
    token_input: int = 0
    token_output: int = 0


# ogni fornitore implementa chiedi
class LLMProvider(ABC):

    @abstractmethod
    def chiedi(self, messaggi: list[dict], tools: list[dict]) -> Risposta:
        pass


# fornitore locale ollama
class OllamaProvider(LLMProvider):

    def __init__(self, modello: str):
        self.modello = modello

    def chiedi(self, messaggi, tools):
        # converto i tool mcp nel formato di ollama
        tools_ollama = []
        for tool in tools:
            tools_ollama.append({
                "type": "function",
                "function": {
                    "name": tool["nome"],
                    "description": tool["descrizione"],
                    "parameters": tool["schema"],
                },
            })

        # traduco i messaggi nel formato di ollama
        messaggi_ollama = []
        for messaggio in messaggi:
            if messaggio["role"] == "assistant":
                tool_calls = []
                for c in messaggio.get("chiamate", []):
                    tool_calls.append({"function": {"name": c["nome"], "arguments": c["argomenti"]}})
                messaggi_ollama.append({"role": "assistant", "content": messaggio["content"], "tool_calls": tool_calls})
            elif messaggio["role"] == "tool":
                messaggi_ollama.append({"role": "tool", "tool_name": messaggio["nome"], "content": messaggio["content"]})
            else:
                messaggi_ollama.append(messaggio)

        risposta = ollama.chat(model=self.modello, messages=messaggi_ollama, tools=tools_ollama)

        # prendo le chiamate ai tool
        chiamate = []
        for chiamata in risposta.message.tool_calls or []:
            chiamate.append({
                "nome": chiamata.function.name,
                "argomenti": chiamata.function.arguments,
            })

        return Risposta(
            testo=risposta.message.content or "",
            chiamate=chiamate,
            token_input=risposta.prompt_eval_count or 0,
            token_output=risposta.eval_count or 0,
        )


# fornitore cloud groq con piano gratuito
class GroqProvider(LLMProvider):

    def __init__(self, modello: str):
        self.modello = modello
        # la chiave la prende da GROQ_API_KEY
        self.client = Groq()

    def chiedi(self, messaggi, tools):
        # converto i tool mcp nel formato di groq
        tools_groq = []
        for tool in tools:
            tools_groq.append({
                "type": "function",
                "function": {
                    "name": tool["nome"],
                    "description": tool["descrizione"],
                    "parameters": tool["schema"],
                },
            })

        # traduco i messaggi nel formato di groq
        # groq collega ogni risultato alla sua chiamata con un id che assegno in ordine
        messaggi_groq = []
        id_da_usare = []
        for messaggio in messaggi:
            if messaggio["role"] == "assistant":
                tool_calls = []
                for c in messaggio.get("chiamate", []):
                    id_chiamata = "chiamata_" + str(len(messaggi_groq)) + "_" + str(len(tool_calls))
                    id_da_usare.append(id_chiamata)
                    tool_calls.append({"id": id_chiamata, "type": "function",
                                       "function": {"name": c["nome"], "arguments": json.dumps(c["argomenti"])}})
                nuovo = {"role": "assistant", "content": messaggio["content"]}
                if tool_calls:
                    nuovo["tool_calls"] = tool_calls
                messaggi_groq.append(nuovo)
            elif messaggio["role"] == "tool":
                messaggi_groq.append({"role": "tool", "tool_call_id": id_da_usare.pop(0),
                                      "name": messaggio["nome"], "content": messaggio["content"]})
            else:
                messaggi_groq.append(messaggio)

        risposta = self.client.chat.completions.create(model=self.modello, messages=messaggi_groq, tools=tools_groq)
        messaggio = risposta.choices[0].message

        # prendo le chiamate ai tool e leggo gli argomenti dal testo json
        chiamate = []
        for chiamata in messaggio.tool_calls or []:
            try:
                argomenti = json.loads(chiamata.function.arguments)
            except json.JSONDecodeError:
                argomenti = {}
            chiamate.append({"nome": chiamata.function.name, "argomenti": argomenti})

        return Risposta(
            testo=messaggio.content or "",
            chiamate=chiamate,
            token_input=risposta.usage.prompt_tokens,
            token_output=risposta.usage.completion_tokens,
        )


# scelgo il fornitore dal nome del modello che per groq inizia con groq/
def crea_provider(nome):
    if nome.startswith("groq/"):
        return GroqProvider(nome[5:])
    return OllamaProvider(nome)
