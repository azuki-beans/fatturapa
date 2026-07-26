"""Parser della Fattura Elettronica italiana (FatturaPA v1.2).

Libreria autonoma, solo standard library: trasforma l'XML del tracciato in
dataclass già leggibili (codici decodificati, importi e date all'italiana),
pronte per essere impaginate come si preferisce.

    from fatturapa import parse

    for documento in parse(xml_bytes):
        print(documento.numero, documento.importo_totale)

Il pacchetto non impone né un motore di template né un generatore di PDF: la
resa grafica resta a carico di chi lo usa.
"""
from .parser import (  # noqa: F401
    CONDIZIONI_PAGAMENTO,
    ESIGIBILITA_IVA,
    MODALITA_PAGAMENTO,
    NATURA,
    REGIME_FISCALE,
    TIPO_DOCUMENTO,
    DatiOrdine,
    Documento,
    Linea,
    Pagamento,
    Riepilogo,
    Soggetto,
    Trasporto,
    is_fattura,
    parse,
)

__all__ = [
    "CONDIZIONI_PAGAMENTO",
    "ESIGIBILITA_IVA",
    "MODALITA_PAGAMENTO",
    "NATURA",
    "REGIME_FISCALE",
    "TIPO_DOCUMENTO",
    "DatiOrdine",
    "Documento",
    "Linea",
    "Pagamento",
    "Riepilogo",
    "Soggetto",
    "Trasporto",
    "is_fattura",
    "parse",
]

__version__ = "0.1.0"
