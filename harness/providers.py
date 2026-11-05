from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import ollama


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