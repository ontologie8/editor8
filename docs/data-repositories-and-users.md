# Datenrepositories und Benutzer

Die Software und ihre Release-Kennung gehören zu editor8. Die Liste erlaubter Datenziele steht in `config/data-repositories.json`; zurzeit ist ausschließlich das bereits eingerichtete `notariat8/ontology` enthalten. Ein Listeneintrag erteilt keine GitHub-Rechte und installiert keine GitHub App.

## Datenziel auswählen

Nach der Anmeldung zeigt die Oberfläche eine Auswahl „Datenrepository“. Sie enthält nur eingetragene Ziele, auf die das angemeldete GitHub-Konto mit dem GitHub-App-Benutzertoken zugreifen kann. Die Auswahl gilt für die einzelne Sitzung. Andere Nutzer behalten ihr Datenziel.

Vor einem Wechsel müssen ungespeicherte Eingaben gespeichert oder verworfen und geöffnete Entwürfe abgelegt werden. Der Server prüft das Ziel erneut und lädt dessen Datenkatalog, bevor er umschaltet. Nicht eingetragene Ziele werden abgewiesen. Ein Wechsel rotiert den Sitzungsschutz und lädt die Oberfläche neu; Suchindex und fachliche Rollen werden nicht zwischen Datenrepositories übernommen.

Weitere Datenziele benötigen einen Eintrag mit `repository` (`owner/repo`) und `label`. Sie müssen den [Datenvertrag](data-contract.md) erfüllen, für den Benutzer zugänglich sein und von der GitHub-App-Installation umfasst werden. Andere Datenschemata brauchen einen eigenen Adapter. editor8 selbst ist als Datenziel verboten.

## Anmeldung und Rechte

Die Anmeldung identifiziert den GitHub-Benutzer. Der Server prüft ihn gegen die Hosteinstellung `EDITOR_USERS`. Der anschließend verwendete GitHub-App-Benutzertoken hat nur die Rechte, die sowohl der Benutzer als auch die App besitzen. Siehe [GitHub: User access tokens](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-user-access-token-for-a-github-app).

Für einen weiteren Notar sind diese Stellen maßgeblich:

1. **Datenrepository auf GitHub:** Das GitHub-Konto einladen. `Write` ist für Änderungen, Branches und Pull Requests erforderlich; reine Leser erhalten `Read`. Der Nutzer benötigt keinen Zugriff auf das Software-Repository, um die gehostete App zu verwenden. Optionales `Read` auf editor8 erlaubt ihm, Quellcode und verlinkte Release-Commits einzusehen.
2. **Azure-Host:** Den GitHub-Benutzernamen in `EDITOR_USERS` aufnehmen. Das ist die Zulassung zum Editor, keine Erteilung von Repository-Rechten.
3. **Fachliche Rolle am Datenziel:** Optional `notary_reviewers` beziehungsweise `ontology_maintainers` im betreffenden Registry-Eintrag pflegen. Das sind Listen von GitHub-Benutzernamen. Reviewer können die fachliche Freigabe einer anderen Person dokumentieren; Maintainer können das gemeinsame Vokabular pflegen. Diese Rollen erteilen keine GitHub-Schreibrechte und benötigen zusätzlich die Editor-Zulassung.
4. **GitHub-App-Installation:** Sicherstellen, dass das Datenrepository ausgewählt ist. Die bestehende App wurde am 06.10.2026 öffentlich registriert, damit externe Repository-Mitarbeiter sie autorisieren können. Bei weiteren Organisationen bleibt die Installation auf ausdrücklich ausgewählten Datenrepositories erforderlich. Details: [Nutzer und Notare zulassen](editor-user-onboarding.md).

Ein optionales Feld `users` beschränkt einen Registry-Eintrag zusätzlich auf bestimmte bereits zum Editor zugelassene Konten. Ohne dieses Feld bestimmen Editor-Zulassung und GitHub-Zugriff die Sichtbarkeit. Eine leere Liste sperrt das Ziel für alle Benutzer.

Diese statischen Nutzer- und Rollenlisten sind der aktuelle Pilotstand. Änderungen von `EDITOR_USERS` benötigen eine neue Azure-Revision, Änderungen der Rollen im Image eine Softwareauslieferung. Für die vom Nutzer geforderte Benutzerverwaltung ohne Deployment beschreibt das [IAM-Zielbild](iam-zielbild.md) die Ablösung durch zentral verwaltete Berechtigungen.

Für das über `GITHUB_REPOSITORY` konfigurierte Standardziel bleiben die bestehenden Hosteinstellungen `NOTARY_REVIEWERS` und `ONTOLOGY_MAINTAINERS` als Rückfall erhalten, wenn der Registry-Eintrag die jeweilige Rolle nicht festlegt. Für weitere Datenziele werden diese Hostrollen nicht übernommen; dort gilt ausschließlich die explizite Rollenliste. Eine leere Rollenliste im Eintrag entzieht diese Rolle auch am Standardziel.

`Write` auf GitHub kann bei fehlenden Branchschutzregeln auch direkte Änderungen oder Merges erlauben. Die Reviewer-Rolle im Editor ist keine technisch erzwungene GitHub-Mergesperre. Die geltenden fachlichen Freigabe- und Merge-Regeln des Datenprojekts bleiben erforderlich.

## Release vergleichen

Die Fußzeile zeigt „Editor-Release“ mit den ersten zwölf Zeichen des beim Containerbuild eingebetteten Softwarecommits. Der Link öffnet genau diesen Commit in editor8 auf GitHub; der volle Hash steht auch am öffentlichen Endpunkt `/api/release`. Der Wert stammt aus dem ausgelieferten Image, nicht aus einer Abfrage des neuesten main-Standes. Lokale Starts ohne eingebetteten Buildstand zeigen „Entwicklung“.
