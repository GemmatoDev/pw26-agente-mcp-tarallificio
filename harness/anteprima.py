import json

from jsonschema import ValidationError, validate

from harness.client_mcp import esegui_tool

# controllo i parametri con lo schema
def controlla_parametri(argomenti, schema):
    try:
        validate(argomenti, schema)
        return None
    except ValidationError as errore:
        return "Parametri non validi: " + errore.message

# prima e dopo della modifica
async def prepara_anteprima(client, chiamata):
    argomenti = chiamata["argomenti"]

    # stato attuale dell'opportunità
    if chiamata["nome"] == "aggiorna_opportunita":
        testo, errore = await esegui_tool(client, "dettaglio_opportunita", {"opportunita_id": argomenti["opportunita_id"]})
        if errore:
            return {"prima": testo, "dopo": argomenti}
        opportunita = json.loads(testo)
        prima = {"titolo": opportunita["titolo"], "cliente": opportunita["ragione_sociale"], "stato": opportunita["stato"]}
        dopo = {"titolo": opportunita["titolo"], "cliente": opportunita["ragione_sociale"], "stato": argomenti["stato"]}
        return {"prima": prima, "dopo": dopo}

    # ticket e attività sono righe nuove
    return {"prima": None, "dopo": argomenti}
