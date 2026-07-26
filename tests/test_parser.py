"""Comportamento del parser sui casi che i tracciati ufficiali non coprono.

Ogni test costruisce la fattura più piccola che serve a mettere alla prova un
solo aspetto: così quando fallisce si sa già dove guardare.
"""
import pytest

from fatturapa import is_fattura, parse
from supporto import fattura_minima


# ---------------------------------------------------------------------------
# Ingresso: cosa è una fattura e cosa no
# ---------------------------------------------------------------------------
def test_is_fattura_riconosce_una_fattura():
    assert is_fattura(fattura_minima()) is True


@pytest.mark.parametrize(
    "contenuto",
    [
        b"<AltroDocumento></AltroDocumento>",
        b"non sono xml",
        b"",
        b"%PDF-1.4 ...",
    ],
)
def test_is_fattura_non_solleva_mai(contenuto):
    assert is_fattura(contenuto) is False


def test_parse_rifiuta_una_radice_diversa():
    with pytest.raises(ValueError, match="non è una Fattura Elettronica"):
        parse(fattura_minima(radice="Documento"))


def test_parse_rifiuta_xml_malformato():
    with pytest.raises(ValueError, match="XML non valido"):
        parse(b"<FatturaElettronica><aperto>")


def test_parse_rifiuta_una_fattura_senza_corpo():
    senza_corpo = b"""<?xml version="1.0"?>
    <FatturaElettronica versione="FPR12">
      <FatturaElettronicaHeader/>
    </FatturaElettronica>"""
    with pytest.raises(ValueError, match="alcun corpo"):
        parse(senza_corpo)


def test_namespace_ignorato_del_tutto():
    """Con o senza namespace il risultato non cambia."""
    con = parse(fattura_minima())[0]
    senza = parse(fattura_minima(namespace=""))[0]
    assert con.numero == senza.numero == "1"
    assert con.cedente.denominazione == senza.cedente.denominazione


def test_firma_xades_ignorata():
    """La firma innestata non deve confondere la navigazione."""
    xml = fattura_minima().replace(
        b"</FatturaElettronica>",
        b'<ds:Signature xmlns:ds="http://www.w3.org/2000/09/xmldsig#">'
        b"<ds:SignedInfo><ds:Numero>999</ds:Numero></ds:SignedInfo>"
        b"</ds:Signature></FatturaElettronica>",
    )
    assert parse(xml)[0].numero == "1"


# ---------------------------------------------------------------------------
# Formattazione
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("grezzo", "atteso"),
    [
        ("100.00", "100,00"),
        ("1234.56", "1.234,56"),
        ("1234567.89", "1.234.567,89"),
        ("0.00", "0,00"),
        ("-50.5", "-50,50"),
    ],
)
def test_importi_all_italiana(grezzo, atteso):
    linea = f"""
        <DettaglioLinee><NumeroLinea>1</NumeroLinea>
          <Descrizione>X</Descrizione>
          <PrezzoUnitario>{grezzo}</PrezzoUnitario>
          <PrezzoTotale>{grezzo}</PrezzoTotale>
        </DettaglioLinee>"""
    assert parse(fattura_minima(linee=linea))[0].linee[0].prezzo_totale == atteso


def test_date_all_italiana():
    generali = """
        <TipoDocumento>TD01</TipoDocumento><Data>2026-03-07</Data>
        <Numero>1</Numero><ImportoTotaleDocumento>1.00</ImportoTotaleDocumento>"""
    assert parse(fattura_minima(generali=generali))[0].data == "07/03/2026"


def test_quantita_senza_decimali_inutili():
    """Le quantità intere si stampano senza la coda di zeri del tracciato."""
    linea = """
        <DettaglioLinee><NumeroLinea>1</NumeroLinea><Descrizione>X</Descrizione>
          <Quantita>30.00000000</Quantita>
          <PrezzoUnitario>1.00</PrezzoUnitario><PrezzoTotale>30.00</PrezzoTotale>
        </DettaglioLinee>"""
    assert parse(fattura_minima(linee=linea))[0].linee[0].quantita == "30"


def test_valore_non_numerico_resta_com_e():
    """Un importo illeggibile non fa saltare la lettura: si mostra tale e quale."""
    linea = """
        <DettaglioLinee><NumeroLinea>1</NumeroLinea><Descrizione>X</Descrizione>
          <PrezzoTotale>abc</PrezzoTotale>
        </DettaglioLinee>"""
    assert parse(fattura_minima(linee=linea))[0].linee[0].prezzo_totale == "abc"


# ---------------------------------------------------------------------------
# Decodifica dei codici
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("codice", "atteso"),
    [("TD01", "Fattura"), ("TD04", "Nota di credito"), ("TD24", "Fattura differita")],
)
def test_tipo_documento_decodificato(codice, atteso):
    generali = f"""
        <TipoDocumento>{codice}</TipoDocumento><Data>2026-01-20</Data>
        <Numero>1</Numero><ImportoTotaleDocumento>1.00</ImportoTotaleDocumento>"""
    documento = parse(fattura_minima(generali=generali))[0]
    assert documento.tipo_documento == atteso
    assert documento.tipo_documento_codice == codice


def test_codice_sconosciuto_resta_tale_e_quale():
    """Il tracciato cambia: un codice non previsto si mostra, non si perde."""
    generali = """
        <TipoDocumento>TD99</TipoDocumento><Data>2026-01-20</Data>
        <Numero>1</Numero><ImportoTotaleDocumento>1.00</ImportoTotaleDocumento>"""
    assert parse(fattura_minima(generali=generali))[0].tipo_documento == "TD99"


def test_natura_e_riferimento_normativo():
    riepilogo = """
        <DatiRiepilogo>
          <AliquotaIVA>0.00</AliquotaIVA>
          <Natura>N5</Natura>
          <ImponibileImporto>100.00</ImponibileImporto>
          <Imposta>0.00</Imposta>
          <RiferimentoNormativo>art. 74 DPR 633/72</RiferimentoNormativo>
        </DatiRiepilogo>"""
    (riepilogo_letto,) = parse(fattura_minima(riepiloghi=riepilogo))[0].riepiloghi
    assert riepilogo_letto.natura.startswith("Regime del margine")
    assert riepilogo_letto.riferimento_normativo == "art. 74 DPR 633/72"


def test_modalita_pagamento_decodificata():
    pagamento = """
      <DatiPagamento>
        <CondizioniPagamento>TP02</CondizioniPagamento>
        <DettaglioPagamento>
          <ModalitaPagamento>MP05</ModalitaPagamento>
          <DataScadenzaPagamento>2026-03-20</DataScadenzaPagamento>
          <ImportoPagamento>122.00</ImportoPagamento>
          <IBAN>IT66T0830401845000045353525</IBAN>
          <IstitutoFinanziario>BANCA X</IstitutoFinanziario>
        </DettaglioPagamento>
      </DatiPagamento>"""
    documento = parse(fattura_minima(pagamento=pagamento))[0]
    (letto,) = documento.pagamenti
    assert letto.modalita == "Bonifico"
    assert letto.scadenza == "20/03/2026"
    assert letto.iban == "IT66T0830401845000045353525"
    assert letto.istituto == "BANCA X"
    assert documento.condizioni_pagamento == "Pagamento completo"


# ---------------------------------------------------------------------------
# Soggetti
# ---------------------------------------------------------------------------
def test_partita_iva_include_il_paese():
    assert parse(fattura_minima())[0].cedente.partita_iva == "IT01234567890"


def test_partita_iva_senza_paese():
    cedente = """
        <DatiAnagrafici>
          <IdFiscaleIVA><IdCodice>01234567890</IdCodice></IdFiscaleIVA>
          <Anagrafica><Denominazione>ALPHA</Denominazione></Anagrafica>
        </DatiAnagrafici>"""
    letto = parse(fattura_minima(cedente=cedente))[0].cedente
    assert letto.partita_iva == "01234567890"


def test_persona_fisica_nome_e_cognome():
    """Senza Denominazione il nome si compone da Nome + Cognome."""
    cessionario = """
        <DatiAnagrafici>
          <CodiceFiscale>RSSMRA80A01H501U</CodiceFiscale>
          <Anagrafica><Nome>MARIO</Nome><Cognome>ROSSI</Cognome></Anagrafica>
        </DatiAnagrafici>"""
    letto = parse(fattura_minima(cessionario=cessionario))[0].cessionario
    assert letto.denominazione == "MARIO ROSSI"


def test_indirizzo_completo_e_civico():
    cedente = parse(fattura_minima())[0].cedente
    assert cedente.indirizzo == "VIA ROMA, 1"
    assert cedente.indirizzo_completo == "VIA ROMA, 1 – 38122 TRENTO (TN)"


def test_soggetto_assente_da_un_soggetto_vuoto():
    """Un blocco anagrafico privo di dati non solleva: restituisce campi vuoti."""
    letto = parse(fattura_minima(cessionario="<!-- niente -->"))[0].cessionario
    assert letto.denominazione == ""
    assert letto.codice_fiscale == ""
    assert letto.partita_iva == ""
    assert letto.indirizzo_completo == ""


# ---------------------------------------------------------------------------
# Totali
# ---------------------------------------------------------------------------
def test_totali_sommano_piu_riepiloghi():
    riepiloghi = """
        <DatiRiepilogo><AliquotaIVA>22.00</AliquotaIVA>
          <ImponibileImporto>100.00</ImponibileImporto><Imposta>22.00</Imposta>
        </DatiRiepilogo>
        <DatiRiepilogo><AliquotaIVA>10.00</AliquotaIVA>
          <ImponibileImporto>50.00</ImponibileImporto><Imposta>5.00</Imposta>
        </DatiRiepilogo>"""
    documento = parse(fattura_minima(riepiloghi=riepiloghi))[0]
    assert documento.totale_imponibile == "150,00"
    assert documento.totale_imposta == "27,00"
    assert len(documento.riepiloghi) == 2


def test_totale_documento_calcolato_se_assente():
    """`ImportoTotaleDocumento` è opzionale: si ricava da imponibile + imposta."""
    generali = """
        <TipoDocumento>TD01</TipoDocumento><Data>2026-01-20</Data><Numero>1</Numero>"""
    assert parse(fattura_minima(generali=generali))[0].importo_totale == "122,00"


def test_totale_calcolato_comprende_il_bollo():
    generali = """
        <TipoDocumento>TD01</TipoDocumento><Data>2026-01-20</Data><Numero>1</Numero>
        <DatiBollo><BolloVirtuale>SI</BolloVirtuale>
          <ImportoBollo>2.00</ImportoBollo></DatiBollo>"""
    documento = parse(fattura_minima(generali=generali))[0]
    assert documento.bollo == "2,00"
    assert documento.importo_totale == "124,00"


# ---------------------------------------------------------------------------
# Campi utili all'impaginazione su modulo cartaceo
# ---------------------------------------------------------------------------
def test_dati_trasporto_e_indirizzo_di_resa():
    trasporto = """
      <DatiTrasporto>
        <CausaleTrasporto>VENDITA</CausaleTrasporto>
        <NumeroColli>3</NumeroColli>
        <Descrizione>SCATOLE</Descrizione>
        <IndirizzoResa>
          <Indirizzo>VIA VERDI</Indirizzo><NumeroCivico>10</NumeroCivico>
          <CAP>38100</CAP><Comune>TRENTO</Comune><Provincia>TN</Provincia>
        </IndirizzoResa>
      </DatiTrasporto>"""
    letto = parse(fattura_minima(generali_extra=trasporto))[0].trasporto
    assert letto.causale == "VENDITA"
    assert letto.colli == "3"
    assert letto.aspetto_beni == "SCATOLE"
    assert letto.indirizzo == "VIA VERDI, 10"
    assert letto.indirizzo_resa == "VIA VERDI, 10 – 38100 TRENTO (TN)"


def test_trasporto_assente_da_un_oggetto_vuoto():
    letto = parse(fattura_minima())[0].trasporto
    assert letto.causale == ""
    assert letto.indirizzo_resa == ""


def test_ordini_di_acquisto_multipli():
    ordini = """
      <DatiOrdineAcquisto><IdDocumento>66685</IdDocumento>
        <Data>2026-01-02</Data><RiferimentoNumeroLinea>1</RiferimentoNumeroLinea>
      </DatiOrdineAcquisto>
      <DatiOrdineAcquisto><IdDocumento>66686</IdDocumento></DatiOrdineAcquisto>"""
    letti = parse(fattura_minima(generali_extra=ordini))[0].ordini
    assert [o.id_documento for o in letti] == ["66685", "66686"]
    assert letti[0].data == "02/01/2026"
    assert letti[1].data == ""


def test_codice_articolo_e_unita_di_misura():
    linea = """
        <DettaglioLinee><NumeroLinea>1</NumeroLinea>
          <CodiceArticolo><CodiceTipo>EAN</CodiceTipo>
            <CodiceValore>9791255060468</CodiceValore></CodiceArticolo>
          <Descrizione>LIBRO</Descrizione>
          <Quantita>2.00</Quantita><UnitaMisura>PZ</UnitaMisura>
          <PrezzoUnitario>10.00</PrezzoUnitario><PrezzoTotale>20.00</PrezzoTotale>
        </DettaglioLinee>"""
    (letta,) = parse(fattura_minima(linee=linea))[0].linee
    assert letta.codice_articolo == "9791255060468"
    assert letta.tipo_codice == "EAN"
    assert letta.unita_misura == "PZ"


def test_causali_multiple_conservate_in_ordine():
    generali = """
        <TipoDocumento>TD01</TipoDocumento><Data>2026-01-20</Data><Numero>1</Numero>
        <ImportoTotaleDocumento>1.00</ImportoTotaleDocumento>
        <Causale>PRIMA</Causale><Causale>SECONDA</Causale>"""
    assert parse(fattura_minima(generali=generali))[0].causali == ["PRIMA", "SECONDA"]
