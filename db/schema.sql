-- abilito le foreign keys
PRAGMA foreign_keys = ON;

-- telefonate, mail, visite, lo storico dei clienti
CREATE TABLE attivita (
    id INTEGER PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES cliente(id),
    opportunita_id INTEGER REFERENCES opportunita(id),
    ticket_id INTEGER REFERENCES ticket(id),
    tipo TEXT NOT NULL CHECK (tipo IN ('telefonata', 'email', 'invio_campioni', 'visita')),
    data TEXT NOT NULL,
    operatore TEXT NOT NULL,
    nota TEXT
);

-- seguite dal commerciale
CREATE TABLE opportunita (
    id INTEGER PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES cliente(id),
    titolo TEXT NOT NULL,
    valore_stimato REAL NOT NULL CHECK (valore_stimato >= 0),
    stato TEXT NOT NULL CHECK (stato IN ('aperta', 'in_trattativa', 'persa', 'vinta')),
    chiusura_prevista TEXT
);

-- UNIQUE, per evitare OMONIMI con i clienti
CREATE TABLE cliente (
    id INTEGER PRIMARY KEY,
    ragione_sociale TEXT NOT NULL UNIQUE,
    canale TEXT NOT NULL CHECK (canale IN ('GDO', 'grossista', 'horeca', 'export')),
    paese TEXT NOT NULL,
    citta TEXT
);

--  chi lavora per il cliente e i loro rispettivi ruoli
CREATE TABLE contatto (
    id INTEGER PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES cliente(id),
    nome TEXT NOT NULL,
    cognome TEXT NOT NULL,
    ruolo TEXT NOT NULL CHECK (ruolo IN ('acquisti', 'amministrazione', 'logistica', 'qualita')),
    email TEXT,
    telefono TEXT
);

-- i vari reclami,richieste dai clienti, lotto e spedizioni facoltativi perché un ticket può riguardare anche ritardi, richiesta di documenti senza per forza un lotto preciso
CREATE TABLE ticket (
    id INTEGER PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES 	cliente(id),
    lotto_codice TEXT REFERENCES lotto(codice),
    spedizione_id INTEGER REFERENCES spedizione(id),
    tipo TEXT NOT NULL CHECK (tipo IN ('reclamo', 'campionatura', 'richiesta_documenti')),
    categoria TEXT CHECK (categoria IN ('frantumato', 'ritardo', 'confezione', 'etichetta', 'corpo_estraneo')),
    priorita TEXT NOT NULL CHECK (priorita IN ('alta', 'media', 'bassa')),
    stato TEXT NOT NULL CHECK (stato IN ('aperto', 'in_lavorazione', 'chiuso')),
    descrizione TEXT NOT NULL,
    aperto_il TEXT NOT NULL,
    chiuso_il TEXT
);

--la consegna al cliente, numero ddt unico per identificarla correttamente
CREATE TABLE spedizione (
    id INTEGER PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES cliente(id),
    data_spedizione TEXT NOT NULL,
    numero_ddt TEXT NOT NULL UNIQUE
);

-- relazione N:M tra spedizione e lotto, indica quali lotti sono partiti, quanti cartoni con ogni spedizione
CREATE TABLE contiene (
    spedizione_id INTEGER NOT NULL REFERENCES spedizione(id),
    lotto_codice TEXT NOT NULL REFERENCES lotto(codice),
    quantita_cartoni INTEGER NOT NULL CHECK (quantita_cartoni > 0),
    PRIMARY KEY (spedizione_id, lotto_codice)
);
-- partite di taralli prodotti, con i vari dati di produzione. ovviamente la data di scadenza deve essere dopo quella di produzione ergo il motivo del check
CREATE TABLE lotto (
    codice TEXT PRIMARY KEY,
    prodotto_codice TEXT NOT NULL REFERENCES prodotto(codice),
    data_produzione TEXT NOT NULL,
    data_scadenza TEXT NOT NULL,
    quantita_prodotta INTEGER NOT NULL CHECK (quantita_prodotta > 0),
    stato TEXT NOT NULL CHECK (stato IN ('regolare', 'bloccato')),
    CHECK (data_scadenza > data_produzione)
);

-- cosa vende il tarallificio
CREATE TABLE prodotto (
    codice TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    formato_g INTEGER NOT NULL CHECK (formato_g > 0),
    shelf_life_mesi INTEGER NOT NULL CHECK (shelf_life_mesi > 0)
);