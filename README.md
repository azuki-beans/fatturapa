# fatturapa

[![PyPI](https://img.shields.io/pypi/v/fatturapa?color=8A2230)](https://pypi.org/project/fatturapa/)
[![Python](https://img.shields.io/pypi/pyversions/fatturapa)](https://pypi.org/project/fatturapa/)
[![MIT License](https://img.shields.io/badge/license-MIT-informational)](LICENSE)

Parser for the Italian **electronic invoice** (*Fattura Elettronica*): FatturaPA v1.2 schema,
`FPR12` and `FPA12` formats. **Zero dependencies**: standard library only.

It turns the XML into ready-to-read dataclasses (decoded codes, amounts and dates in Italian
format) that you can lay out however you like. The library does **not** generate PDFs and does not
impose a template engine: rendering is up to you.

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

The public API mirrors the Italian names of the FatturaPA schema (`documento`, `cessionario`,
`linee`, …), so fields map one-to-one to the official specification.

## What it does (and what it doesn't)

It reads the XML and gives it back in a shape that is easy to print:

- **decodes codes**: `TD01` → *Fattura*, `RF19` → *Forfettario*, `MP05` → *Bonifico*, and the same
  for Natura, CondizioniPagamento, EsigibilitaIVA;
- **formats the Italian way**: `1234.56` → `1.234,56`, `2026-01-20` → `20/01/2026`;
- **computes totals** from the VAT summaries, and derives the document total (taxable amount + tax +
  stamp duty) when `ImportoTotaleDocumento` is missing, since it is optional.

It does not validate against the XSD, does not verify digital signatures and does not extract
attachments. If you need that, have a look at
[fattura-elettronica-reader](https://pypi.org/project/fattura-elettronica-reader/).

## Design choices

- **Namespace-agnostic.** XML coming from the SdI (the Italian exchange system) mixes the schema
  namespace, children with `xmlns=""` and an embedded XAdES signature; navigation uses the tag's
  *local name*, so it works with or without prefixes.
- **No exceptions on optional fields.** Missing tags become empty strings or empty lists:
  **never `None`**. Printing code does not need to be defensive.
- **Batch invoices are the norm.** A `FatturaElettronica` can contain several
  `FatturaElettronicaBody`: `parse()` always returns a `list[Documento]`.

`parse()` raises `ValueError` only if the root is not `<FatturaElettronica>`, if the XML is
malformed or if there is no document body. For an upfront check that never raises there is
`is_fattura(raw)`:

```python
from fatturapa import is_fattura

if is_fattura(contenuto):
    documenti = parse(contenuto)
```

## The model

`parse()` returns a list of `Documento`:

| field | content |
|---|---|
| `tipo_documento` / `tipo_documento_codice` | *Fattura* / `TD01` |
| `numero`, `data`, `divisa`, `causali` | general data (number, date, currency, descriptions) |
| `importo_totale`, `totale_imponibile`, `totale_imposta`, `bollo` | totals |
| `cedente`, `cessionario` | `Soggetto` (seller / buyer: name, `partita_iva`, address, `indirizzo_completo`) |
| `linee` | `list[Linea]` (description, quantity, prices, VAT rate, `codice_articolo`) |
| `riepiloghi` | `list[Riepilogo]` (VAT rate, nature, taxable amount, tax, legal reference) |
| `pagamenti`, `condizioni_pagamento` | `list[Pagamento]` (method, due date, IBAN, bank) |
| `trasporto` | `Trasporto` (reason, packages, weight, `indirizzo_resa`) |
| `ordini` | `list[DatiOrdine]` (`DatiOrdineAcquisto`) |

All values are strings **already formatted** for printing. If you need numbers, convert them
yourself: the library does not make rounding or currency choices on your behalf.

## A signed `.p7m`?

Invoices often arrive digitally signed (`.xml.p7m`). Extract the content first, then pass it to
`parse()`:

```bash
openssl smime -verify -in fattura.xml.p7m -inform DER -noverify -out fattura.xml
```

For a web interface there is [p7m-apri](https://github.com/azuki-beans/p7m-apri), which uses this
same library to display invoices.

## Development

```bash
poetry install
poetry run pytest
poetry run ruff check .
```

Tests run on the **sample files published by the Italian Revenue Agency** (*Agenzia delle
Entrate*, in `tests/tracciati/`), plus hand-made cases for transport, stamp duty, VAT nature and
formatting.

MIT License.
