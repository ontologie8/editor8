# Trennung am 2026-10-01

Editorcode wurde selektiv aus `notariat8/ontology`, Branch `codex/editor-workbench`, Commit `0c01d0cf737db71675540b17dbbc71707ed0a65b` übernommen. Keine private Git-Historie, Fallmodelle, Kataloge oder Secrets wurden exportiert. Bestehende Lizenztexte und Attribution bleiben erhalten.

Neu: expliziter lokaler Datenroot, getrennte Assetpfade, remote gelesener Katalog am festen Commit, dynamische Fallanzahl, synthetische Tests sowie eine Software-CI. Der bisherige 20-Fall-Regressionssatz liegt unter `tests/integration` und benötigt einen separaten Datencheckout.

Die Quellzweige bleiben erhalten. Der Editorzweig enthält außerdem eine Änderung an `ontology/core.ttl`; sie wird nicht als Software veröffentlicht und bleibt als fachlicher Entwurf im Datenprojekt erhalten. Der bestehende SOP-Fachzweig wird nicht verändert. Software-PRs im Datenprojekt werden durch die Migration abgelöst.

Beim ersten Export lief das bestehende Azure-Deployment zunächst mit seinem bisherigen Image weiter. Inzwischen wurde die Software aus editor8 bereitgestellt und mit PR #1 die automatische Bereitstellung nach erfolgreichen Software- und Containerprüfungen eingerichtet. Am 01.10.2026 waren das bereitgestellte Softwareimage und der erfolgreiche Deploy-Job gegen den editor8-Commit geprüft. Die Deployment-Zugänge liegen in editor8, das GitHub-App-Secret wird aus Azure Key Vault eingebunden. Es wird kein Secret aus dem ontology-Checkout geladen. [Eigenständigkeit und Betriebszugänge](editor-autonomy.md) hält die aktuelle Prüfung fest. Der produktive Schreib-/PR-Pilot und die notarielle Fachprüfung bleiben separat offen.

Der bereits bestehende SOP-Entwurf enthält die `quellabschnitt`-Definition aus dem Softwarequellzweig. Sie bleibt daher in ontology PR #4; kein doppelter Fachentwurf wird angelegt. Seine Anwendungscodeänderungen werden entfernt. Das dortige zusätzliche Leseseitenformat ist über `editor_document_version: 2` getrennt von den Fachmodellen angebunden und im Editor erhalten.
