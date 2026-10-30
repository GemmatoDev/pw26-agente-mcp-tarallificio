# Dizionario dei dati

## ATTIVITÀ

| Attributo | Tipo | Obbligatorio | Valori ammessi |
|---|---|---|---|
| id | intero | sì | - |
| tipo | testo | sì | telefonata, email, invio_campioni, visita |
| data | data | sì |AAAA-MM-GG |
| operatore | testo | sì | - |
| nota | testo | no | - |

## OPPORTUNITÀ

| Attributo | Tipo | Obbligatorio | Valori ammessi |
|---|---|---|---|
| id | intero | sì | - |
| titolo | testo | sì | - |
| valore stimato | decimale | sì |>=0|
| stato | testo | sì | aperta, in_trattativa, persa, vinta |
| chiusura prevista | data | sì | AAAA-MM-GG |

## CLIENTE

| Attributo | Tipo | Obbligatorio | Valori ammessi |
|---|---|---|---|
| id | intero | sì | - |
| ragione sociale | testo | sì | univoco |
| canale | testo | sì | GDO, grossista, horeca, export |
| paese | testo | sì | - |
| città | testo | no | - |

## CONTATTO

| Attributo | Tipo | Obbligatorio | Valori ammessi |
|---|---|---|---|
| id | intero | sì | - |
| nome | testo | sì | - |
| cognome | testo | sì |- |
| ruolo | testo | sì | acquisti, amministrazione, logistica, qualita |
| email | testo | no | - |
| telefono | testo | no | - |

## TICKET

| Attributo | Tipo | Obbligatorio | Valori ammessi |
|---|---|---|---|
| id | intero | sì | - |
| tipo | testo | sì | reclamo, campionatura, richiesta_documenti |
| categoria | testo | si però solo se tipo = reclamo | frantumato, ritardo, confezione, etichetta, corpo_estraneo |
| priorità | testo | sì |alta, media, bassa|
| stato | testo | sì | aperto, chiuso, in_lavorazione |
| descrizione | testo | sì | - |
| aperto il | data | sì | AAAA-MM-GG |
| chiuso il | data | no | AAAA-MM-GG |

Vincoli tra attributi:
- chiuso il se presente non deve essere precedente ad aperto il
- stato = chiuso se e solo se chiuso il è valorizzato
- categoria valorizzata se e solo se tipo = reclamo

## SPEDIZIONE

| Attributo | Tipo | Obbligatorio | Valori ammessi |
|---|---|---|---|
| id | intero | sì | - |
| data spedizione | data | sì | AAAA-MM-GG |
| numero DDT | testo | sì | AAAA/NNNN, univoco |

## CONTIENE

| Attributo | Tipo | Obbligatorio | Valori ammessi |
|---|---|---|---|
| quantità cartoni | intero | sì | >0 |

## LOTTO

| Attributo | Tipo | Obbligatorio | Valori ammessi |
|---|---|---|---|
| codice | testo | sì | formato L-AANNN (es. L-26118), univoco |
| data produzione | data | sì | AAAA-MM-GG |
| data scadenza | data | sì | AAAA-MM-GG, obbligatoriamente dopo data produzione |
| quantità prodotta | intero | sì | >0 |
| stato | testo | sì | regolare, bloccato |

## PRODOTTO

| Attributo | Tipo | Obbligatorio | Valori ammessi |
|---|---|---|---|
| codice | testo | sì | formato GT-XXNNN (es. GT-CL300), univoco |
| nome | testo | sì | - |
| formato | intero | sì | grammi, >0 |
| shelf life | intero | sì | mesi, >0 |
