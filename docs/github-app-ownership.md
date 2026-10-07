# Editorbetreiber und Dateninstallation trennen

Stand: 07.10.2026. Software und Azure-Auslieferung stammen aus `ontologie8/editor8`. Die Eigentumsübertragung der bestehenden GitHub-App von `notariat8` nach `ontologie8` ist durch die GitHub-API bestätigt. App-ID und Client-ID sind unverändert. Name **Ontologie8 Editor**, Kennung `ontologie8-editor` und Homepage `https://www.ontologie8.de` sind ebenfalls geprüft. Die Dateninstallation unter `notariat8` besteht getrennt davon weiter. Eine neue tatsächliche Anmeldung nach der Übertragung bleibt zu prüfen.

## Ziel und überprüfter Ausgangsstand

| Bestandteil | Ausgangsstand | Ziel |
| --- | --- | --- |
| Software und Release | `ontologie8/editor8` | `ontologie8/editor8` |
| GitHub-App-Eigentümer | `notariat8` | `ontologie8`, der Editorbetreiber |
| Bestehende App-ID | `5119378` | Dieselbe Registrierung weiterführen |
| App-Name | NaC Ontology Editor notariat8 | Ontologie8 Editor, vom Betreiber geändert und geprüft |
| App-Homepage | bisheriger Azure-Hostname | `https://www.ontologie8.de` |
| GitHub-Dateninstallation | `notariat8`, ausgewählte Repositories | Getrennt vom App-Eigentümer; Zugriff auf `notariat8/ontology` |
| Fachliche Konten und Rollen | getrennte Zulassung und Rollen am Datenziel | Kein Zugriff auf Editorverwaltung oder Editor-Schreibrechte daraus ableiten |

Der alte Azure-Ressourcenname bezeichnet die bestehende Hostingressource, nicht den Eigentümer der GitHub-App. Sein Name entscheidet nicht über den Softwarestand. Bestehende Secrets liegen im Host beziehungsweise Key Vault und werden nicht zwischen Git-Repositories kopiert.

**Aktuell verifiziert:** App-ID `5119378`, Eigentümer `ontologie8`, Name **Ontologie8 Editor**, Kennung `ontologie8-editor`, Homepage `https://www.ontologie8.de`. Die öffentliche App-Abfrage ist erfolgreich. Die Installation in `notariat8` meldet weiterhin diese App-ID, die neue Kennung, `repository_selection: selected` und keine Sperrung; ihre Rechte sind `contents: write`, `pull_requests: write`, `metadata: read`. Die genaue Repository-Auswahl und der angemeldete Zugriff bleiben zusätzlich zu prüfen. In `ontologie8` ist keine Installation vorhanden oder für Software-Schreibzugriff erforderlich.

## Erfolgte Übertragung prüfen

Für diese Korrektur **keinen Registrierungshelfer ausführen** und keine zweite App anlegen. Der Betreiber ist in beiden Organisationen als Eigentümer bestätigt. GitHub beschreibt die [Eigentumsübertragung](https://docs.github.com/en/apps/maintaining-github-apps/transferring-ownership-of-a-github-app).

1. Die [aktuellen App-Einstellungen bei ontologie8](https://github.com/organizations/ontologie8/settings/apps/ontologie8-editor) mit dem Betreiberkonto öffnen. Eigentümer und Kennung immer mit den tatsächlichen GitHub-Metadaten vergleichen.
2. Der erfolgte Übertragungsweg lag bei der Ausgangsregistrierung unter **Advanced → Transfer ownership**, mit der **Organisation `ontologie8`** als Ziel. GitHub zeigt einen Hinweis an, falls eine Übertragung eine Installation entfernen würde. Die bereits bestätigte Übertragung nicht wiederholen.
3. App-ID und Client-ID mit der Ausgangsregistrierung vergleichen. Beide sind bei dieser Korrektur unverändert geblieben; einen Wechsel der Zugangsdaten nicht aus der Übertragung ableiten.
4. Unter **General** bei der übertragenen App den vom Betreiber gewählten Namen **Ontologie8 Editor** und **Homepage URL** `https://www.ontologie8.de` prüfen. Die öffentliche Registrierung und die erlaubte Rückkehradresse `https://www.ontologie8.de/callback` kontrollieren.
5. Die getrennte Dateninstallation unter `notariat8` prüfen. Das erlaubte Datenrepository bleibt `notariat8/ontology`. Die Softwareorganisation als Eigentümer benötigt dadurch keine Installation für Schreibzugriffe auf `ontologie8/editor8`.

Das Umbenennen kann die App-Kennung in GitHub-Links ändern. Die tatsächlich von GitHub gelieferte Kennung lautet nach der Betreiberänderung `ontologie8-editor`; Betriebslinks verwenden diese bestätigte Kennung. Die [öffentliche App-Seite](https://github.com/apps/ontologie8-editor) zeigt die Registrierung.

## Helfer im Softwareprojekt

`scripts/github_app_identity.py` leitet den App-Eigentümer aus dem Softwareprojekt ab. Datenziele werden ausdrücklich angegeben und das Software-Repository wird als Datenziel abgewiesen.

`scripts/register_github_app.py` ist ausschließlich ein Bootstrap für eine tatsächlich benötigte neue Registrierung. Er erstellt eine öffentliche App beim Editorbetreiber `ontologie8` und verlangt `--data-repository owner/repo`. Die alten Parameter `--org` und `--repo` werden nicht mehr verwendet. Der Helfer darf für die vorhandene App nicht erneut gestartet werden; ihr Name ist bereits registriert.

`scripts/recover_github_app_secret.py` ist ausschließlich für eine notwendige Wiederherstellung. Er verlangt `--app-slug`, `--client-id` und `--data-repository`. Bevor eine lokale Secret-Eingabe geöffnet wird, prüft er die öffentliche App-Identität: Eigentümer `ontologie8`, exakte App-Kennung und passende Client-ID. Die Eingabe geht weiterhin unmittelbar an Azure Key Vault, ohne Chat oder Git. Bei einer noch unter dem Datenbetreiber registrierten App wird dieser Ablauf angehalten.

## Nachweise für den Abschluss

- Öffentliche App-Metadaten: Eigentümer `ontologie8`, gewünschter Name und Homepage; unveränderte App- und Client-ID.
- Installation im Datenkonto: vorgesehene Berechtigungen und ausdrückliche Repository-Auswahl. Eigentumsübertragung allein bestätigt keine weiter funktionierende Installation.
- Neuer Anmeldeversuch: richtige Rückkehradresse und sichtbares zugelassenes Konto; Fachmodelle des gewählten Datenziels zugänglich. Ein öffentlicher Startseitenabruf ersetzt die angemeldete Prüfung nicht.
- Softwarelieferung: Python, JavaScript, synthetischer Browser und getrennte Datenintegration; erwartetes gesundes Azure-Image mit passender Release-Kennung.

Die Benutzerverwaltung ohne neue Builds ist eine weitere Aufgabe im [IAM-Zielbild](iam-zielbild.md). Die Eigentumskorrektur ersetzt diese Migration nicht.
