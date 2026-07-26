# Changelog

Le modifiche degne di nota. Il progetto segue il [versionamento
semantico](https://semver.org/lang/it/).

## [0.2.0] — 2026-07-26

### Corretto

- `Linea.prezzo_unitario` non viene più arrotondato a due decimali. Il tracciato
  ne ammette fino a otto e i listini a decimale lungo li usano davvero: un
  prezzo di `0.41670000` veniva restituito come `0,42`, perdendo il valore
  originale. Ora gli zeri di riempimento si tolgono ma i decimali significativi
  si conservano (`0,4167`), sempre con un minimo di due (`5` → `5,00`).
  Gli importi (`prezzo_totale`, imponibili, imposte) restano a due decimali.

## [0.1.0] — 2026-07-26

Prima versione. Il parser nasce dentro
[p7m-apri](https://github.com/azuki-beans/p7m-apri), dove serviva a impaginare
le fatture elettroniche in PDF, ed è stato estratto in libreria autonoma perché
riusabile da solo.

### Aggiunto

- `parse(raw)` — dall'XML del tracciato FatturaPA v1.2 (`FPR12`/`FPA12`) a una
  `list[Documento]`, una per ogni `FatturaElettronicaBody` (fatture in lotto).
- `is_fattura(raw)` — controllo preventivo che non solleva mai eccezioni.
- Dataclass `Documento`, `Soggetto`, `Linea`, `Riepilogo`, `Pagamento`,
  `Trasporto`, `DatiOrdine`.
- Decodifica di TipoDocumento, RegimeFiscale, Natura, ModalitaPagamento,
  CondizioniPagamento ed EsigibilitaIVA; i codici non previsti restano visibili
  così come sono, invece di sparire.
- Importi e date formattati all'italiana; totali sommati dai riepiloghi e totale
  documento ricavato quando `ImportoTotaleDocumento` è assente.
- Annotazioni di tipo complete (`py.typed`).
