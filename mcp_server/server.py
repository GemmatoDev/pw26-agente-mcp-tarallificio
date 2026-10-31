import sqlite3

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

# cerco i clienti per nome
@server.tool(annotations=ToolAnnotations(read_only_hint=True), meta={"rischio": "basso"})
def cerca_cliente(testo: str) -> list[dict]:
    """Cerca i clienti la cui ragione sociale contiene il testo indicato."""
    return esegui(crm.cerca_cliente, testo)

# avvio il server
if __name__ == "__main__":
    server.run()