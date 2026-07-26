"""Il parser sui file di esempio pubblicati dall'Agenzia delle Entrate.

Sono la verifica più importante: XML reali, con il prefisso di namespace, le
fatture in lotto e i campi opzionali disposti come li scrive davvero il SdI.
"""
import pytest

from fatturapa import Documento, parse

from supporto import leggi

UFFICIALI = [
    "IT01234567890_FPA01.xml",
    "IT01234567890_FPA02.xml",
    "IT01234567890_FPA03.xml",
    "IT01234567890_FPR01.xml",
    "IT01234567890_FPR02.xml",
    "IT01234567890_FPR03.xml",
]


@pytest.mark.parametrize("nome", UFFICIALI)
def test_ogni_tracciato_ufficiale_produce_documenti(nome):
    documenti = parse(leggi(nome))
    assert documenti
    assert all(isinstance(d, Documento) for d in documenti)
    assert all(d.numero and d.data for d in documenti)


@pytest.mark.parametrize("nome", UFFICIALI)
def test_nessun_campo_e_none(nome):
    """La promessa del parser: campi assenti = stringhe/liste vuote, mai None."""
    for documento in parse(leggi(nome)):
        for valore in vars(documento).values():
            assert valore is not None
        for soggetto in (documento.cedente, documento.cessionario):
            assert all(v is not None for v in vars(soggetto).values())
        for linea in documento.linee:
            assert all(v is not None for v in vars(linea).values())


@pytest.mark.parametrize(
    ("nome", "numeri"),
    [
        ("IT01234567890_FPA03.xml", ["12", "456"]),
        ("IT01234567890_FPR03.xml", ["123", "456"]),
    ],
)
def test_lotto_restituisce_un_documento_per_body(nome, numeri):
    documenti = parse(leggi(nome))
    assert [d.numero for d in documenti] == numeri
    # l'header è unico e vale per tutti i documenti del lotto
    assert len({d.cedente.denominazione for d in documenti}) == 1


def test_namespace_con_prefisso():
    """I file FPA ufficiali usano <p:FatturaElettronica>: va letto lo stesso."""
    documenti = parse(leggi("IT01234567890_FPA01.xml"))
    assert documenti[0].cedente.denominazione == "ALPHA SRL"


def test_campi_di_un_documento_completo():
    documento = parse(leggi("IT01234567890_FPR01.xml"))[0]

    assert documento.tipo_documento == "Fattura"
    assert documento.tipo_documento_codice == "TD01"
    assert documento.numero == "123"
    assert documento.data == "18/12/2014"
    assert documento.divisa == "EUR"
    assert documento.importo_totale == "6,10"
    assert documento.codice_destinatario == "ABC1234"

    assert documento.cedente.denominazione == "SOCIETA' ALPHA SRL"
    assert documento.cedente.partita_iva == "IT01234567890"
    assert documento.cedente.regime_fiscale == "Forfettario"
    assert documento.cessionario.denominazione == "DITTA BETA"

    (linea,) = documento.linee
    assert linea.descrizione.startswith("DESCRIZIONE DELLA FORNITURA")
    assert (linea.quantita, linea.prezzo_unitario, linea.prezzo_totale) == (
        "5", "1,00", "5,00",
    )
    assert linea.aliquota_iva == "22,00"

    (riepilogo,) = documento.riepiloghi
    assert (riepilogo.imponibile, riepilogo.imposta) == ("5,00", "1,10")
    assert riepilogo.esigibilita == "IVA a esigibilità immediata"

    (pagamento,) = documento.pagamenti
    assert pagamento.modalita == "Contanti"
    assert pagamento.scadenza == "30/01/2015"
    assert documento.condizioni_pagamento == "Pagamento a rate"

    assert [o.id_documento for o in documento.ordini] == ["66685"]


def test_totali_sommati_dai_riepiloghi():
    documento = parse(leggi("IT01234567890_FPR02.xml"))[0]
    assert documento.totale_imponibile == "27,00"
    assert documento.totale_imposta == "5,95"


def test_importi_oltre_il_migliaio_usano_il_punto():
    """Formato italiano: separatore migliaia "." e decimali ","."""
    secondo = parse(leggi("IT01234567890_FPR03.xml"))[1]
    assert secondo.importo_totale == "2.440,00"
    assert secondo.totale_imponibile == "2.000,00"
