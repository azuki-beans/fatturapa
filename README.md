# fatturapa

[![PyPI](https://img.shields.io/pypi/v/fatturapa?color=8A2230)](https://pypi.org/project/fatturapa/)
[![Python](https://img.shields.io/pypi/pyversions/fatturapa)](https://pypi.org/project/fatturapa/)
[![Licenza MIT](https://img.shields.io/badge/licenza-MIT-informational)](LICENSE)

Parser della **Fattura Elettronica** italiana — tracciato FatturaPA v1.2, formati
`FPR12` e `FPA12`. **Zero dipendenze**: solo standard library.

> *Parser for the Italian electronic invoice format (FatturaPA v1.2). Turns the
> XML into plain dataclasses. No dependencies.*

Trasforma l'XML in dataclass già leggibili — codici decodificati, importi e date
all'italiana — pronte da impaginare come preferisci. La libreria **non** genera
PDF e non impone un motore di template: la resa grafica resta tua.

```bash
pip install fatturapa
```

```python
from fatturapa import parse

for documento in parse(xml_bytes):
    print(documento.tipo_documento, documento.numero, documento.data)
    print(documento.cessionario.denominazione)
    for linea in documento.linee:
        print(" ", linea.descrizione, linea.quantita, linea.prezzo_totale)
    print("Totale:", documento.importo_totale, documento.divisa)
```

```
Fattura 123 18/12/2014
DITTA BETA
  DESCRIZIONE DELLA FORNITURA 5 5,00
Totale: 6,10 EUR
```

## Cosa fa (e cosa no)

Legge il tracciato e te lo restituisce in una forma comoda da stampare:

- **decodifica i codici** — `TD01` → *Fattura*, `RF19` → *Forfettario*, `MP05` →
  *Bonifico*, e così per Natura, CondizioniPagamento, EsigibilitaIVA;
- **formatta all'italiana** — `1234.56` → `1.234,56`, `2026-01-20` → `20/01/2026`;
- **calcola i totali** dai riepiloghi, e ricava il totale documento (imponibile +
  imposta + bollo) quando `ImportoTotaleDocumento` manca, visto che è opzionale.

Non valida contro l'XSD, non verifica firme digitali, non estrae allegati. Se ti
serve quello, guarda
[fattura-elettronica-reader](https://pypi.org/project/fattura-elettronica-reader/).

## Scelte di fondo

- **Namespace-agnostico.** L'XML del SdI mescola il namespace del tracciato,
  figli con `xmlns=""` e una firma XAdES innestata; la navigazione avviene per
  *nome locale* del tag, quindi funziona con o senza prefisso.
- **Nessuna eccezione sui campi opzionali.** I tag mancanti diventano stringhe o
  liste vuote: **mai `None`**. Il codice che stampa non deve difendersi.
- **Le fatture in lotto sono la norma.** Una `FatturaElettronica` può contenere
  più `FatturaElettronicaBody`: `parse()` restituisce sempre una `list[Documento]`.

`parse()` solleva `ValueError` solo se la radice non è `<FatturaElettronica>`, se
l'XML è malformato o se non c'è alcun corpo documento. Per un controllo
preventivo che non solleva mai c'è `is_fattura(raw)`:

```python
from fatturapa import is_fattura

if is_fattura(contenuto):
    documenti = parse(contenuto)
```

## Il modello

`parse()` restituisce una lista di `Documento`:

| campo | contenuto |
|---|---|
| `tipo_documento` / `tipo_documento_codice` | *Fattura* / `TD01` |
| `numero`, `data`, `divisa`, `causali` | dati generali |
| `importo_totale`, `totale_imponibile`, `totale_imposta`, `bollo` | totali |
| `cedente`, `cessionario` | `Soggetto` (denominazione, `partita_iva`, sede, `indirizzo_completo`) |
| `linee` | `list[Linea]` (descrizione, quantità, prezzi, aliquota, `codice_articolo`) |
| `riepiloghi` | `list[Riepilogo]` (aliquota, natura, imponibile, imposta, riferimento normativo) |
| `pagamenti`, `condizioni_pagamento` | `list[Pagamento]` (modalità, scadenza, IBAN, istituto) |
| `trasporto` | `Trasporto` (causale, colli, peso, `indirizzo_resa`) |
| `ordini` | `list[DatiOrdine]` (`DatiOrdineAcquisto`) |

Tutti i valori sono stringhe **già formattate** per essere stampate. Se ti
servono come numeri, riconvertili tu: la libreria non fa scelte al posto tuo su
arrotondamenti e valuta.

## Un `.p7m` firmato?

Le fatture arrivano spesso firmate (`.xml.p7m`). Estrai prima il contenuto, poi
passalo a `parse()`:

```bash
openssl smime -verify -in fattura.xml.p7m -inform DER -noverify -out fattura.xml
```

Per farlo da interfaccia web c'è [p7m-apri](https://github.com/azuki-beans/p7m-apri),
che usa questa stessa libreria per visualizzare le fatture.

## Sviluppo

```bash
poetry install
poetry run pytest
poetry run ruff check .
```

I test girano sui **tracciati di esempio pubblicati dall'Agenzia delle Entrate**
(in `tests/tracciati/`), più casi mirati costruiti a mano per trasporto, bollo,
natura e formattazione.

Licenza MIT.
