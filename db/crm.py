import sqlite3
from datetime import date

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
    # unisco i dati del lotto con le spedizioni trovate
    risultato = dict(lotto)
    risultato["spedizioni"] = [dict(sped) for sped in spedizioni_trovate]
    return risultato

# apro un nuovo ticket dopo aver controllato che i dati siano coerenti
def crea_ticket(conn, cliente_id, tipo, priorita, descrizione,
                categoria=None, lotto_codice=None, spedizione_id=None):
    query = "SELECT * FROM cliente WHERE id = ?"
    cliente = conn.execute(query, (cliente_id,)).fetchone()
    if cliente is None:
        raise ValueError("cliente non esistente")

    # la spedizione deve essere di questo cliente
    if spedizione_id is not None:
        query = "SELECT * FROM spedizione WHERE id = ? AND cliente_id = ?"
        spedizione = conn.execute(query, (spedizione_id, cliente_id)).fetchone()
        if spedizione is None:
            raise ValueError("spedizione non trovata per questo cliente")

    # il lotto deve essere arrivato a questo cliente
    if lotto_codice is not None:
        if spedizione_id is not None:
            # se c'è la spedizione il lotto deve stare proprio in quella
            query = "SELECT * FROM contiene WHERE spedizione_id = ? AND lotto_codice = ?"
            trovato = conn.execute(query, (spedizione_id, lotto_codice)).fetchone()
        else:
            # altrimenti basta che stia in una qualsiasi spedizione del cliente
            query = """
                SELECT * FROM contiene
                JOIN spedizione ON spedizione.id = contiene.spedizione_id
                WHERE spedizione.cliente_id = ? AND contiene.lotto_codice = ?
            """
            trovato = conn.execute(query, (cliente_id, lotto_codice)).fetchone()
        if trovato is None:
            raise ValueError("il lotto non risulta spedito a questo cliente")

    # il ticket nasce sempre aperto con la data di oggi
    query = """
        INSERT INTO ticket (cliente_id, lotto_codice, spedizione_id, tipo, categoria,
                            priorita, stato, descrizione, aperto_il)
        VALUES (?, ?, ?, ?, ?, ?, 'aperto', ?, ?)
    """
    cur = conn.execute(query, (cliente_id, lotto_codice, spedizione_id, tipo, categoria,
                               priorita, descrizione, str(date.today())))
    conn.commit()

    # rileggo il ticket appena creato e lo restituisco
    query = "SELECT * FROM ticket WHERE id = ?"
    ticket_creato = conn.execute(query, (cur.lastrowid,)).fetchone()
    return dict(ticket_creato)

# registro una telefonata email visita o invio campioni
def registra_attivita(conn, cliente_id, tipo, operatore, nota=None,
                      opportunita_id=None, ticket_id=None):
    query = "SELECT * FROM cliente WHERE id = ?"
    cliente = conn.execute(query, (cliente_id,)).fetchone()
    if cliente is None:
        raise ValueError("cliente non esistente")

    # se collego un ticket deve essere dello stesso cliente
    if ticket_id is not None:
        query = "SELECT * FROM ticket WHERE id = ? AND cliente_id = ?"
        ticket = conn.execute(query, (ticket_id, cliente_id)).fetchone()
        if ticket is None:
            raise ValueError("ticket non trovato per questo cliente")

    # stessa cosa per l'opportunità
    if opportunita_id is not None:
        query = "SELECT * FROM opportunita WHERE id = ? AND cliente_id = ?"
        opportunita = conn.execute(query, (opportunita_id, cliente_id)).fetchone()
        if opportunita is None:
            raise ValueError("opportunità non trovata per questo cliente")

    query = """
        INSERT INTO attivita (cliente_id, opportunita_id, ticket_id, tipo, data, operatore, nota)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    cur = conn.execute(query, (cliente_id, opportunita_id, ticket_id, tipo,
                               str(date.today()), operatore, nota))
    conn.commit()
    # rileggo l'attività appena creata e la restituisco
    query = "SELECT * FROM attivita WHERE id = ?"
    attivita_creata = conn.execute(query, (cur.lastrowid,)).fetchone()
    return dict(attivita_creata)

# cambio lo stato di un'opportunità e tengo anche quello vecchio
def aggiorna_opportunita(conn, opportunita_id, stato):
    query = "SELECT * FROM opportunita WHERE id = ?"
    opportunita = conn.execute(query, (opportunita_id,)).fetchone()
    if opportunita is None:
        raise ValueError("opportunità non esistente")
    # cambio lo stato nel db e salvo
    query = "UPDATE opportunita SET stato = ? WHERE id = ?"
    conn.execute(query, (stato, opportunita_id))
    conn.commit()
    
    # restituisco l'opportunità con lo stato nuovo e quello vecchio
    risultato = dict(opportunita)
    risultato["stato_precedente"] = risultato["stato"]
    risultato["stato"] = stato
    return risultato