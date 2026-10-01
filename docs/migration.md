# Trennung am 2026-10-01

Editorcode wurde selektiv aus `notariat8/ontology`, Branch `codex/editor-workbench`, Commit `0c01d0cf737db71675540b17dbbc71707ed0a65b` übernommen. Keine private Git-Historie, Fallmodelle, Kataloge oder Secrets wurden exportiert. Bestehende Lizenztexte und Attribution bleiben erhalten.

Neu: expliziter lokaler Datenroot, getrennte Assetpfade, remote gelesener Katalog am festen Commit, dynamische Fallanzahl, synthetische Tests sowie eine Software-CI. Der bisherige 20-Fall-Regressionssatz liegt unter `tests/integration` und benötigt einen separaten Datencheckout.

Die Quellzweige bleiben erhalten. Der Editorzweig enthält außerdem eine Änderung an `ontology/core.ttl`; sie wird nicht als Software veröffentlicht und bleibt als fachlicher Entwurf im Datenprojekt erhalten. Der bestehende SOP-Fachzweig wird nicht verändert. Software-PRs im Datenprojekt werden durch die Migration abgelöst.

Das bestehende Azure-Deployment läuft zunächst weiter mit seinem bisherigen Image und GitHub-App-Zugang. Diese Migration startet kein Deployment und ändert keine App-Rechte. Die alten Hostingnachweise in den übernommenen Dokumenten sind historische Nachweise; ein neues Image aus editor8 und der produktive Schreib-/PR-Pilot stehen separat aus.
