import sys

from mcp import Client, StdioServerParameters
from mcp.types import TextContent

# avvio il server con il python del venv
SERVER = StdioServerParameters(command=sys.executable, args=["-m", "mcp_server.server"])

# tool del server per il provider
async def leggi_tool(client):
    risultato = await client.list_tools()
    tools = []
    for tool in risultato.tools:
        meta = tool.meta or {}
        tools.append({
            "nome": tool.name,
            "descrizione": tool.description,
            "schema": tool.input_schema,
            # rischio alto se manca
            "rischio": meta.get("rischio", "alto"),
        })
    return tools

# eseguo il tool
async def esegui_tool(client, nome, argomenti):
    risultato = await client.call_tool(nome, argomenti)
    blocchi = []
    for blocco in risultato.content:
        if isinstance(blocco, TextContent):
            blocchi.append(blocco.text)
    return "\n".join(blocchi), risultato.is_error