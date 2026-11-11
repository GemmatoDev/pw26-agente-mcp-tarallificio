![GemmaTaralli](docs/banner.png)

# Agente LLM per il backoffice di un tarallificio fittizio "GemmaTaralli"

Un assistente per un ufficio commerciale di un'impresa alimentare B2B.

L'operatore di backoffice scrive le richieste all'agente in linguaggio naturale, come aprire un reclamo su un lotto o sapere quali clienti hanno ricevuto quel lotto.

L'agente quindi consulta il db del mini-CRM tramite i tool di un server MCP e chiede conferma all'operatore prima di modificare i dati.

## Specifiche tecniche

L'intero sistema è composto da un server MCP e un harness agentico, entrambi scritti in Python.

L'interfaccia web mostra la chat con l'agente, i vari passi eseguiti (chiamate al modello e ai tool, con tempi e token), l'anteprima delle modifiche da confermare e i token consumati per ogni richiesta dell'operatore.

I modelli possono essere locali (Ollama) o di un provider con piano gratuito (Groq) e si scelgono dalla pagina web o direttamente da CLI.

## Struttura

| Cartella | Contenuti |
|---|---|
| `db/` | schema, dati di prova e funzioni sul database |
| `mcp_server/` | il server MCP con gli 8 tool |
| `harness/` | ciclo agentico, provider, client MCP, anteprima e log |
| `harness/runner.py` | lancia gli scenari di test sui modelli |
| `web/` | l'interfaccia web |
| `tests/` | scenari e risultati dei test |
| `logs/scenari/` | log del giro ufficiale |
| `docs/` | decisioni, registro ore, fonti, scheda impresa, diagrammi e screenshot |

## Tool del server MCP

| Tool | Cosa fa | Rischio |
|---|---|---|
| `cerca_cliente` | cerca un cliente per nome | basso |
| `dettaglio_cliente` | contatti, ticket e opportunità di un cliente | basso |
| `elenco_ticket` | ticket di un cliente, anche per stato | basso |
| `tracciabilita_lotto` | a chi è arrivato un lotto | basso |
| `dettaglio_opportunita` | scheda di un'opportunità | basso |
| `crea_ticket` | apre un reclamo, una richiesta di campioni o di documenti | medio |
| `registra_attivita` | segna una telefonata, una email, una visita o un invio di campioni | medio |
| `aggiorna_opportunita` | cambia lo stato di un'opportunità | alto |

I tool che scrivono nel database, cioè quelli a rischio medio e alto, partono solo se l'operatore conferma.

## Installazione

L'ho provato su Windows 11 con Python 3.14.

1. Si installa [Ollama](https://ollama.com) e si scaricano i due modelli locali:

   ```
   ollama pull qwen3:8b
   ollama pull gemma4:e4b
   ```

2. Si clona il repo, si crea l'ambiente virtuale e si installano le dipendenze:

   ```
   git clone https://github.com/GemmatoDev/pw26-agente-mcp-tarallificio.git
   cd pw26-agente-mcp-tarallificio
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Si crea il database con i dati di prova:

   ```
   python db/seed.py
   ```

   Ogni volta che si lancia riparte da zero, quindi serve anche per tornare ai dati iniziali.

4. Groq è facoltativo. Per usarlo serve una chiave gratuita di [console.groq.com](https://console.groq.com), da salvare così prima di riaprire il terminale:

   ```
   setx GROQ_API_KEY <chiave>
   ```

## Esecuzione

I comandi vanno lanciati dalla cartella del repo con l'ambiente virtuale attivo.

Interfaccia web, poi si apre http://127.0.0.1:8000:

```
python -m uvicorn web.app:app
```

Da terminale, il secondo parametro è il modello (per Groq `groq/openai/gpt-oss-120b`):

```
python -m harness.ciclo "chi ha ricevuto il lotto L-26101?" qwen3:8b
```

Test sui tre modelli:

```
python -m harness.runner qwen3:8b gemma4:e4b groq/openai/gpt-oss-120b
```

Il runner rifà il database prima di ogni scenario, salva i log in `logs/scenari/` e i risultati in un CSV dentro `tests/`.

## Contesto

Project work del corso di laurea L-31 UniPegaso, traccia 26.

GemmaTaralli è un'impresa di fantasia e i dati sono simulati.

## Stato

Sviluppo concluso a novembre 2026.

## Licenza

MIT