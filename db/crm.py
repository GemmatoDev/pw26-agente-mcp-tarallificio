import sqlite3

# linko db
DB = "db/gemmataralli.db"

# connessione al DB
def connetti():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON") 
    # così leggo le colonne con il loro nome
    conn.row_factory = sqlite3.Row
    return conn

# cerco i clienti che hanno il testo nel nome
def cerca_cliente(conn, testo):
    query = "SELECT id, ragione_sociale, canale, paese, citta FROM cliente WHERE ragione_sociale LIKE ?"
    clienti_trovati =  conn.execute(query, (f"%{testo}%",)).fetchall()
    return [dict(cliente) for cliente in clienti_trovati ]

# scheda completa del cliente con contatti ticket e opportunità
def dettaglio_cliente(conn, cliente_id):
    query = "SELECT * FROM cliente WHERE id = ?"
    cliente = conn.execute(query, (cliente_id,)).fetchone()
    # se il cliente non c'è mi fermo con un errore e lo segnalo
    if cliente is None: 
        raise ValueError("cliente non esistente") 
    scheda = dict(cliente)

    # aggiungo i contatti
    query = "SELECT * FROM contatto WHERE cliente_id = ?"
    contatti = conn.execute(query, (cliente_id,)).fetchall()
    scheda["contatti"] = [dict(contatto) for contatto in contatti]

    # aggiungo i ticket
    query = "SELECT * FROM ticket WHERE cliente_id = ?"
    ticket_trovati = conn.execute(query, (cliente_id,)).fetchall()
    scheda["ticket"] = [dict(ticket) for ticket in ticket_trovati]

    # aggiungo le opportunità
    query = "SELECT * FROM opportunita WHERE cliente_id = ?"
    opportunita_trovate = conn.execute(query, (cliente_id,)).fetchall()
    scheda["opportunita"] = [dict(opp) for opp in opportunita_trovate]

    return scheda

# elenco ticket del cliente anche filtrati per stato
def elenco_ticket(conn, cliente_id, stato=None):
    if stato is None:
        query = "SELECT * FROM ticket WHERE cliente_id = ?"
        ticket_trovati = conn.execute(query, (cliente_id,)).fetchall()
    else:
        query = "SELECT * FROM ticket WHERE cliente_id = ? AND stato = ?"
        ticket_trovati = conn.execute(query, (cliente_id, stato)).fetchall()
    return [dict(ticket) for ticket in ticket_trovati]

# trovo tutti i clienti che hanno ricevuto un lotto
def tracciabilita_lotto(conn, codice_lotto):
    query = "SELECT * FROM lotto WHERE codice = ?"
    lotto = conn.execute(query, (codice_lotto,)).fetchone()
    # se il lotto non c'è mi fermo con un errore e lo segnalo
    if lotto is None:
        raise ValueError("lotto non esistente")

    # parto dal lotto e arrivo al cliente passando per contiene e spedizione
    query = """
        SELECT cliente.id AS cliente_id, cliente.ragione_sociale,
        spedizione.numero_ddt, spedizione.data_spedizione,
        contiene.quantita_cartoni
        FROM contiene
        JOIN spedizione ON spedizione.id = contiene.spedizione_id
        JOIN cliente ON cliente.id = spedizione.cliente_id
        WHERE contiene.lotto_codice = ?
        ORDER BY spedizione.data_spedizione
    """
    spedizioni_trovate = conn.execute(query, (codice_lotto,)).fetchall()

    risultato = dict(lotto)
    risultato["spedizioni"] = [dict(sped) for sped in spedizioni_trovate]
    return risultato