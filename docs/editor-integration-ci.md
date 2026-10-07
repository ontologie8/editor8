# Datenintegration in CI

Stand: 07.10.2026. Software und Daten bleiben getrennt. Die öffentliche editor8-CI prüft synthetische Daten, Python, JavaScript, Browser und Container. Die Integration mit den Notar-Fachmodellen läuft im [separaten Datenrepository](https://github.com/notariat8/ontology/actions/workflows/editor-integration.yml), das auf Nutzerauftrag seit 07.10.2026 öffentlich ist. App-Zulassung und Schreibrechte bleiben davon unabhängig.

Der Workflow wurde mit [Daten-PR #10](https://github.com/notariat8/ontology/pull/10) übernommen. Der [erste erfolgreiche PR-Lauf](https://github.com/notariat8/ontology/actions/runs/37016881500) bestätigt Python- und Browserintegration. Neue Editorstände erhalten einen eigenen Lauf mit ihrem vollständigen Commit.

## Regelmäßiger Lauf

`notariat8/ontology/.github/workflows/editor-integration.yml` startet bei Push und Pull Request, täglich um 04:17 UTC sowie manuell. Er checkt Daten und den öffentlichen Editor in getrennte Verzeichnisse aus. `EDITOR8_DATA_ROOT` zeigt ausdrücklich auf den Datencheckout. Beide Checkouts speichern keine Credentials. Der vorhandene Actions-Token liest nur das Datenrepository; für den öffentlichen Editor ist kein zusätzlicher Zugang nötig. App-Secrets und personenbezogene OAuth-Tokens werden nicht benötigt.

Standardmäßig wird der Datencommit des Ereignisses mit editor8 `main` geprüft. Sobald der Editor ausgecheckt ist, bleibt sein Commit für den ganzen Lauf fest. Die Actions-Zusammenfassung nennt beide vollständigen SHAs und den Ausgang. Ein späteres `main` verändert diesen bereits ausgecheckten Stand nicht.

Der Job führt die Python-Integration unter `tests/integration` und `npm run test:integration:browser` des Editors aus. Beim Ausgangsstand sind das 48 Python- und fünf Browserprüfungen mit den 20 gepflegten Fällen. Schreib-/PR-Wege verwenden einen lokalen GitHub-Ersatz; weder Fachmodelle noch echte GitHub-PRs werden durch Tests verändert. Testausgaben liegen im Datenrepository und sind nach dessen Veröffentlichung öffentlich.

## Einen Stand gezielt wiederholen

In der Actions-Seite **Validate editor integration → Run workflow** wählen. Optional vollständige 40-stellige SHAs in `editor_commit` und `data_commit` eintragen. Leere Felder prüfen editor8 `main` und den Datencommit des gewählten Workflow-Ereignisses. Für eine exakte Wiederholung beide Kennungen aus der früheren Zusammenfassung angeben. Der Workflow selbst wird von der ausgewählten Workflow-Revision ausgeführt.

Ein Editor-Arbeitsbranch kann nach seinem Push über seinen vollständigen Commit bereits vor dem Merge geprüft werden. Neue Softwarestände benötigen vor fachlich relevanter Auslieferung eine erfolgreiche Integration mit dokumentiertem Datenstand.

## Grenzen und Zuständigkeit

Der private Integrationslauf ist ein eigenständiger Nachweis, kein automatisch erzwungener Statuscheck des öffentlichen Editor-PRs. Ohne zusätzliche repositoryübergreifende Schreibberechtigung wird kein Status in editor8 zurückgeschrieben. Vor einer entsprechenden Übernahme wird der private Prüfausgang deshalb ausdrücklich geprüft. Der tägliche Lauf erkennt auch neue Editor-main-Stände ohne Änderung am Datenrepository.

Die Azure-Auslieferung bleibt Aufgabe von editor8. Ein erfolgreicher Integrationslauf bestätigt weder einen produktiven OAuth-Schreibweg noch eine notarielle Freigabe. Diese Abnahmen stehen gesondert in [Roadmap](editor-roadmap.md) und [Produktstand](editor-produktstand.md).
