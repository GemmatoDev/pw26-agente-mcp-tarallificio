\# Agente LLM per il backoffice di un tarallificio fittizio "GemmaTaralli"



Un assistente per un ufficio commerciale di un'impresa alimentare B2B.

L'operatore di backoffice scrive le richieste all'agente in linguaggio naturale.

Le richieste variano da apertura reclami su lotti a tracciabilità dei lotti.

L'agente quindi consulta il db del mini-CRM tramite i tool di un server MCP e chiede conferma all’operatore prima di modificare i dati.



\## Specifiche tecniche



L'intero sistema è composto da un server MCP e un harness agentico, entrambi scritti in Python.

L'interfaccia web mostra la chat con l'agente, i vari passi eseguiti (chiamate tool, parametri, risultati), l'anteprima delle modifiche da confermare e i token consumati per ogni richiesta dell'operatore.

I modelli possono essere locali (Ollama) o di un provider con piano gratuito, intercambiabili da configurazione.



\## Contesto



Project work del corso di laurea L-31 UniPegaso, traccia 26.

GemmaTaralli è un'impresa di fantasia e i dati sono simulati.



\## Stato



In sviluppo.



\## Licenza



MIT

