import sqlite3
from typing import Literal

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations


from db import crm

# creo il server mcp del crm
server = MCPServer("gemmataralli-crm")

# apro il db chiamo la funzione del crm e trasformo gli errori in errori del tool
def esegui(funzione, *parametri):
    conn = crm.connetti()
    try:
        return funzione(conn, *parametri)
    except (ValueError, sqlite3.IntegrityError) as errore:
        raise ToolError(str(errore))
    finally:
        conn.close()

# i tool di lettura non modificano il db
LETTURA = ToolAnnotations(
    read_only_hint=True,
    open_world_hint=False,
)

# i tool che aggiungono una riga senza toccare quelle che ci sono
AGGIUNGE = ToolAnnotations(
    read_only_hint=False,
    destructive_hint=False,
    idempotent_hint=False,
    open_world_hint=False,
)

# il tool che sovrascrive un valore già presente
SOVRASCRIVE = ToolAnnotations(
    read_only_hint=False,
    destructive_hint=True,
    idempotent_hint=True,
    open_world_hint=False,
)

# cerco i clienti per nome
@server.tool(annotations=LETTURA, meta={"rischio": "basso"})
def cerca_cliente(testo: str) -> list[dict]:
    """Cerca i clienti per ragione sociale, anche con una parte del nome. Restituisce l'id da usare negli altri tool."""
    return esegui(crm.cerca_cliente, testo)

# scheda del cliente con contatti ticket e opportunità
@server.tool(annotations=LETTURA, meta={"rischio": "basso"})
def dettaglio_cliente(cliente_id: int) -> dict:
    """Scheda del cliente con contatti, ticket e opportunità."""
    return esegui(crm.dettaglio_cliente, cliente_id)

# ticket del cliente anche filtrati per stato
@server.tool(annotations=LETTURA, meta={"rischio": "basso"})
def elenco_ticket(cliente_id: int,
                  stato: Literal["aperto", "in_lavorazione", "chiuso"] | None = None) -> list[dict]:
    """Ticket di un cliente, anche filtrati per stato."""
    return esegui(crm.elenco_ticket, cliente_id, stato)

# clienti che hanno ricevuto un lotto
@server.tool(annotations=LETTURA, meta={"rischio": "basso"})
def tracciabilita_lotto(codice_lotto: str) -> dict:
    """Clienti che hanno ricevuto un lotto e con quale spedizione. Il codice è del tipo L-26101."""
    return esegui(crm.tracciabilita_lotto, codice_lotto)

# scheda di un'opportunità
@server.tool(annotations=LETTURA, meta={"rischio": "basso"})
def dettaglio_opportunita(opportunita_id: int) -> dict:
    """Scheda di un'opportunità con titolo, valore, stato e cliente."""
    return esegui(crm.dettaglio_opportunita, opportunita_id)

# apro un nuovo ticket
@server.tool(annotations=AGGIUNGE, meta={"rischio": "medio"})
def crea_ticket(cliente_id: int,
                tipo: Literal["reclamo", "campionatura", "richiesta_documenti"],
                priorita: Literal["alta", "media", "bassa"],
                descrizione: str,
                categoria: Literal["frantumato", "ritardo", "confezione", "etichetta", "corpo_estraneo"] | None = None,
                lotto_codice: str | None = None,
                spedizione_id: int | None = None) -> dict:
    """Apre un ticket. La categoria va messa solo per i reclami. Lotto e spedizione devono essere del cliente."""
    return esegui(crm.crea_ticket, cliente_id, tipo, priorita, descrizione,
                  categoria, lotto_codice, spedizione_id)

# registro un'attività fatta con il cliente
@server.tool(annotations=AGGIUNGE, meta={"rischio": "medio"})
def registra_attivita(cliente_id: int,
                      tipo: Literal["telefonata", "email", "visita", "invio_campioni"],
                      operatore: str,
                      nota: str | None = None,
                      opportunita_id: int | None = None,
                      ticket_id: int | None = None) -> dict:
    """Registra un'attività fatta con il cliente."""
    return esegui(crm.registra_attivita, cliente_id, tipo, operatore, nota,
                  opportunita_id, ticket_id)

# cambio lo stato di un'opportunità
@server.tool(annotations=SOVRASCRIVE, meta={"rischio": "alto"})
def aggiorna_opportunita(opportunita_id: int,
                         stato: Literal["aperta", "in_trattativa", "vinta", "persa"]) -> dict:
    """Cambia lo stato di un'opportunità e restituisce quello vecchio."""
    return esegui(crm.aggiorna_opportunita, opportunita_id, stato)

# avvio il server
if __name__ == "__main__":
    server.run()    