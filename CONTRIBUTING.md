# Zu editor8 beitragen

Änderungen über Branch und Pull Request liefern. Ein Beitrag beschreibt Zweck, Auswirkung und Prüfnachweis. Für einen größeren Auftrag ein Issue mit Scope und Akzeptanzkriterien anlegen. Sicherheitslücken folgen [SECURITY.md](SECURITY.md).

Dieses Repository pflegt Software und Produktdokumentation. Fachmodelle gehören ins ausdrücklich konfigurierte Datenrepository. Keine realen Aktenwerte, privaten Fachmodelle oder Secrets eintragen. [AGENTS.md](AGENTS.md), [DESIGN.md](DESIGN.md) und der [Datenvertrag](docs/data-contract.md) beschreiben die Arbeitsgrenzen.

## Validierung und Lieferung

1. Python: `python -m unittest discover -s tests -q`.
2. Dokumentationsgleichstand: `python scripts/build_learning.py --check`.
3. JavaScript: `node --check editor/app.js` und `node --check editor/learning/app.js`.
4. Synthetische Browserwege: `npm ci` und `npm run test:browser` nach Installation des Playwright-Browsers.
5. Datenintegration zusätzlich mit einem ausdrücklich angegebenen separaten Checkout prüfen; Anleitung in [README](README.md).
6. UI-Änderungen im Desktoplayout sichtbar prüfen. Veränderte Befehle, Felder, Rollen und Abläufe im Handbuch und Training aktualisieren.

Ein Softwarebuild ist erst mit gesundem aktivem Azure-Image und passender live ausgelieferter Release-Kennung abgeschlossen. Eine technische Softwarelieferung erteilt keine notarielle Fachfreigabe.

Beiträge übernehmen die Lizenz ihrer Kategorie: Code AGPL-3.0-or-later; Dokumentation CC-BY-4.0. Attribution und Markenregeln aus [NOTICE](NOTICE), [AUTHORS.md](AUTHORS.md) und [TRADEMARK.md](TRADEMARK.md) erhalten. Die NaC-Beitragsregeln wurden auf die tatsächlichen editor8-Prüfungen angepasst; NaC-Prozessvalidatoren sind hier keine Softwaretests.
