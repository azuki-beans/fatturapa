"""Materiale condiviso dai test.

`tests/tracciati/` contiene i file di esempio pubblicati dall'Agenzia delle
Entrate insieme al tracciato v1.2: sono la prova che il parser regge l'XML
"vero", compreso il prefisso di namespace (`p:FatturaElettronica`) che i file
ufficiali usano e le fatture in lotto.

Per i casi che i file ufficiali non coprono (trasporto, bollo, natura, unità di
misura…) si usa `fattura_minima()`, che costruisce l'XML più piccolo possibile e
lascia iniettare solo i pezzi in esame.
"""
from pathlib import Path

TRACCIATI = Path(__file__).parent / "tracciati"


def leggi(nome: str) -> bytes:
    return (TRACCIATI / nome).read_bytes()


def fattura_minima(
    *,
    generali: str = "",
    generali_extra: str = "",
    linee: str = "",
    riepiloghi: str = "",
    pagamento: str = "",
    cedente: str = "",
    cessionario: str = "",
    trasmissione: str = "",
    radice: str = "FatturaElettronica",
    namespace: str = 'xmlns="http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2"',
) -> bytes:
    """Una fattura valida ridotta all'osso, con i pezzi passati innestati dentro.

    I default riproducono il minimo che il parser deve saper leggere; ogni
    argomento sostituisce il blocco corrispondente. `generali_extra` si aggiunge
    dentro `<DatiGenerali>` (è lì che stanno trasporto e ordini d'acquisto).
    """
    generali = generali or """
        <TipoDocumento>TD01</TipoDocumento>
        <Divisa>EUR</Divisa>
        <Data>2026-01-20</Data>
        <Numero>1</Numero>
        <ImportoTotaleDocumento>122.00</ImportoTotaleDocumento>"""
    linee = linee or """
        <DettaglioLinee>
          <NumeroLinea>1</NumeroLinea>
          <Descrizione>CONSULENZA</Descrizione>
          <Quantita>1.00</Quantita>
          <PrezzoUnitario>100.00</PrezzoUnitario>
          <PrezzoTotale>100.00</PrezzoTotale>
          <AliquotaIVA>22.00</AliquotaIVA>
        </DettaglioLinee>"""
    riepiloghi = riepiloghi or """
        <DatiRiepilogo>
          <AliquotaIVA>22.00</AliquotaIVA>
          <ImponibileImporto>100.00</ImponibileImporto>
          <Imposta>22.00</Imposta>
        </DatiRiepilogo>"""
    cedente = cedente or """
        <DatiAnagrafici>
          <IdFiscaleIVA><IdPaese>IT</IdPaese><IdCodice>01234567890</IdCodice></IdFiscaleIVA>
          <Anagrafica><Denominazione>ALPHA SRL</Denominazione></Anagrafica>
          <RegimeFiscale>RF01</RegimeFiscale>
        </DatiAnagrafici>
        <Sede>
          <Indirizzo>VIA ROMA</Indirizzo>
          <NumeroCivico>1</NumeroCivico>
          <CAP>38122</CAP><Comune>TRENTO</Comune><Provincia>TN</Provincia>
        </Sede>"""
    cessionario = cessionario or """
        <DatiAnagrafici>
          <CodiceFiscale>RSSMRA80A01H501U</CodiceFiscale>
          <Anagrafica><Denominazione>BETA SNC</Denominazione></Anagrafica>
        </DatiAnagrafici>
        <Sede><Indirizzo>VIA MILANO 2</Indirizzo><CAP>20100</CAP>
          <Comune>MILANO</Comune><Provincia>MI</Provincia></Sede>"""
    trasmissione = trasmissione or """
        <CodiceDestinatario>0000000</CodiceDestinatario>"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<{radice} {namespace} versione="FPR12">
  <FatturaElettronicaHeader>
    <DatiTrasmissione>{trasmissione}</DatiTrasmissione>
    <CedentePrestatore>{cedente}</CedentePrestatore>
    <CessionarioCommittente>{cessionario}</CessionarioCommittente>
  </FatturaElettronicaHeader>
  <FatturaElettronicaBody>
    <DatiGenerali>
      <DatiGeneraliDocumento>{generali}</DatiGeneraliDocumento>
      {generali_extra}
    </DatiGenerali>
    <DatiBeniServizi>{linee}{riepiloghi}</DatiBeniServizi>
    {pagamento}
  </FatturaElettronicaBody>
</{radice}>""".encode()
