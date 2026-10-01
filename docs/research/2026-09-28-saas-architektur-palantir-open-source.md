> Historischer Software-Architekturentwurf aus ontology PR #5. Übernommen zur getrennten Softwarepflege; kein Nachweis einer Bereitstellung.

# NaC-Fallontologie als gehostete Pflegeplattform

Stand: 2026-09-28. Status: Architektur-Recherche und Aufwandsschätzung, keine Produktentscheidung und keine notarielle Fachfreigabe.

## Ausgangspunkt

- **USER-CONFIRMED:** Genau 20 kanonische NaC-Fälle; Turtle bleibt fachliche Pflegequelle, Mermaid wird daraus erzeugt. NaC-BPMN bleibt Quelle für den Prozessablauf. NaC pflegt per GitOps; Notarinnen und Notare prüfen fachlich.
- **USER-CONFIRMED:** Ein einziges Ontologie-Repository ist die dauerhafte Datenquelle. Zwei bis drei Notarinnen oder Notare bearbeiten den gemeinsamen Katalog über eine gehostete Webanwendung und GitOps. Das Frontend läuft im Browser, das Editor-Backend in der Cloud. Das Änderungsvolumen ist gering; die Sichtbarkeit des Repositorys (privat oder öffentlich) bleibt offen.
- **USER-CONFIRMED:** Im Repository liegen Fachmodell und daraus erzeugte Ansichten, weiterhin ohne reale Akten oder Laufzeitwerte. Getrennte Datenräume je Notariat sind nicht Teil dieses Ziels.
- **VERIFIED (Repository):** `ontology/core.ttl` und die 20 `cases/<slug>/ontology.ttl` sind die Pflegequelle. Ein statischer Suchindex kann beim Build erzeugt werden. Für diesen Katalog ist kein Triple Store erforderlich.

## Was Palantir öffentlich belegt

Der [Ontology Manager](https://www.palantir.com/docs/foundry/ontology-manager/overview) hat dauerhafte Suche, Erstellen und Branch-Auswahl, eine Discover-Startseite sowie eigene Seiten für Objekt-, Eigenschafts- und Beziehungstypen. Eine Objekttyp-Seite bündelt Metadaten, Eigenschaften, lokale Beziehungen, Abhängigkeiten, Daten und Nutzung. [Ontology proposals](https://www.palantir.com/docs/foundry/ontologies/review-ontology-proposals) erlauben Review einzelner Ressourcen mit Vorschau, Prüfern, Kommentaren und Änderungsverlauf. Das ist ein Produktvorbild für NaC.

Der [Backend-Überblick](https://www.palantir.com/docs/foundry/object-backend/overview) nennt Ontology Metadata Service, Objektdatenbanken, Object Set Service, Actions, Object Data Funnel und Functions on Objects. Sie verarbeiten auch laufende Objektdaten, Abfragen, Änderungen und Indexierung. Laut [Architekturüberblick](https://www.palantir.com/docs/foundry/architecture-center/overview) umfassen AIP und Foundry zusammen über 300 Dienste. **INFERENCE:** Für einen Git-versionierten Katalog mit 20 Fällen ohne Aktenwerte wäre dies überdimensioniert.

### Open-Source-Bezüge mit Evidenzgrenze

| Baustein | Öffentlich belegt | Bedeutung für NaC |
| --- | --- | --- |
| [Blueprint](https://github.com/palantir/blueprint) | Palantirs React-UI-Bibliothek (Apache-2.0). Palantir nennt Blueprint in der [Foundry-UI-Dokumentation](https://www.palantir.com/docs/foundry/object-views/widgets-filtering). | Geeignete Grundlage für dichte Desktop-Ansichten; liefert keine Ontologie- oder Review-Logik. |
| [Conjure](https://github.com/palantir/conjure) | Von Palantir veröffentlichter API-Generator für den eigenen Microservice-Ansatz. | Für eine kleine NaC-API nicht nötig. Seine Verwendung speziell im Ontology Manager ist öffentlich nicht belegt. |
| [Apache Spark](https://www.palantir.com/docs/foundry/ontologies/compute-usage) | Palantir dokumentiert Spark für Ontology-Indexierungsjobs. | Für kleine Turtle-Dateien und einen beim Build erzeugten Index unnötig. |
| [Kubernetes](https://www.palantir.com/docs/foundry/architecture-center/rubix) | Palantir beschreibt Rubix als Kubernetes-Unterbau für Foundry, AIP und Apollo. | Für eine kleine API nicht erforderlich. |

**OPEN:** Quellcode und genaue Komponenten des Ontology Managers selbst sind in den geprüften öffentlichen Quellen nicht offengelegt. Blueprint ist keine Open-Source-Ausgabe des Ontology Managers. Auch [AtlasDB](https://github.com/palantir/atlasdb) ist zwar ein öffentliches Palantir-Projekt; ein Einsatz im aktuellen Ontology Manager ist damit nicht bewiesen.

## Empfohlene Zielarchitektur für NaC

```mermaid
flowchart LR
  L[Lesende] --> W[Browser-Frontend]
  E[2 bis 3 notarielle Editoren] --> W
  W -->|gleiche Webadresse: /api| A[Kleine Cloud-API und GitHub-Anmeldung]
  A -->|Branch, Commit, PR| G[GitHub Repository]
  G -->|Pull Request| C[GitHub Actions: TTL, Katalog, Mermaid, später SHACL]
  G -->|Review| R[Notarielle Reviewer]
  G -->|freigegebener main-Stand| W
```

1. **Lesen:** Das Browser-Frontend erhält Suchindex, Fallseiten und fokussierte Graphdaten aus einem reproduzierbaren Build des freigegebenen `main`-Stands. Die Dateien können von einem statischen Host ausgeliefert werden. Eine lokale Installation ist nicht nötig: „lokal“ bedeutet hier, dass die Oberfläche im Browser der Nutzer läuft.
2. **Bearbeiten:** Ein kleiner Cloud-Dienst übernimmt GitHub-Anmeldung, serverseitige GitHub-App-Geheimnisse, Rechteprüfung, Branch, Commit und Pull Request. GitHub Apps bieten fein abgestufte Rechte auf [Inhalte und Pull Requests](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/choosing-permissions-for-a-github-app). [Nutzerzugriffstoken einer GitHub App](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-user-access-token-for-a-github-app) sind auf die Schnittmenge der Rechte von Person und App beschränkt. Frontend und API sollten unter derselben Webadresse bereitstehen; das vereinfacht Anmeldung und vermeidet Browser-Geheimnisse. Die API kann serverlos oder als kleiner Dienst betrieben werden.
3. **Prüfen:** Der Editor zeigt semantischen Vorher/Nachher-Vergleich, betroffene Beziehungen und den Turtle-Diff. Bestehende Validierung läuft vor dem PR und in GitHub Actions. [Erforderliche Statusprüfungen](https://docs.github.com/en/pull-requests/reference/status-checks) und notarielle Fachfreigabe bleiben getrennte Gates.
4. **Daten:** Turtle bleibt die maßgebliche Fachquelle. Suchindex, Mermaid und Ansichten werden daraus generiert. Der Editor liest einen konkreten Commit, prüft beim Speichern, ob sich der Ausgangsstand geändert hat, und legt Änderungen ausschließlich auf einem Branch mit PR ab. NaC-BPMN wird verlinkt oder separat betrachtet; der Fachgraph erzeugt keinen Prozessablauf.

**Bessere Betriebsform für diesen Umfang:** Ein Host liefert das statische Frontend und die API unter derselben Domain aus; GitHub bleibt der einzige dauerhafte Speicher für Ontologiedaten. Eine Trennung in GitHub Pages plus API auf einer zweiten Domain ist möglich, erhöht aber Aufwand für Anmeldung, Cookies und Zugriffssteuerung. GitHub selbst bleibt ein aktiver externer Dienst.

**Grenze von „alle Daten im Repo“:** Fachliche Turtle-Dateien, SHACL-Regeln, Quellenbezüge, Konfiguration und erzeugbare Dokumentation gehören ins Repository. PR-Kommentare, Freigaben und CI-Ergebnisse sind GitHub-Metadaten; sie können bei Bedarf als Review-Zusammenfassung ins Repo übernommen werden. App-Schlüssel, Sitzungen, Tokens und Betriebslogs dürfen nicht im Repository liegen. Eine eigene Ontologie-Datenbank ist dafür nicht nötig.

### Mögliche Open-Source-Bausteine

- [Blueprint](https://github.com/palantir/blueprint) für Bedienkomponenten; [Cytoscape.js](https://github.com/cytoscape/cytoscape.js) (MIT) für auf einen Baustein fokussierte Graphen. Beides ersetzt keine fachliche Informationsarchitektur.
- [RDFLib](https://github.com/RDFLib/rdflib) (BSD-3-Clause) für RDF/Turtle. Die vorhandene Python-Logik kann Ausgangspunkt für verlustarme Änderungen sein.
- [pySHACL](https://github.com/RDFLib/pySHACL) (Apache-2.0) für spätere Regelprüfung. Ein menschenfreundlicher SHACL-Editor ist ein eigenes Arbeitspaket.
- Für die kleine API ist ein leichtes Framework ausreichend; die konkrete Wahl folgt einem technischen Durchstich. Spark, Kafka, Kubernetes und ein Triple Store sind für die erste Version nicht begründet.

Der eigene Plattformcode kann gemäß Repository-Regel unter AGPL-3.0-or-later stehen und die Fachinhalte unter CC-BY-4.0; Drittbibliotheken benötigen ihre jeweiligen Lizenzhinweise. **GitHub als gehosteter Dienst ist selbst keine vollständig quelloffene Plattform.** Falls „alles Open Source“ später auch den Git-Host umfassen soll, ist [Forgejo](https://forgejo.org/) eine selbst betriebene Alternative mit Pull Requests und [Actions](https://forgejo.org/docs/latest/user/actions/reference/). Das würde jedoch Hosting, Updates, Backups und Betrieb des Git-Dienstes zusätzlich auf NaC verlagern. Für die genannte GitHub-Vorgabe ist GitHub daher die pragmatische Managed-Service-Ausnahme.

## Benötigte aktive Dienste

| Dienst | Erste Version | Zweck |
| --- | --- | --- |
| GitHub Repository, PRs, Actions | Ja, gemanagt | Quellstand, Review, Validierung, Publikation. Actions laufen ereignisbezogen. |
| Webhosting für Frontend und API | Ja, gemanagt | Statisches Frontend und kleine API bevorzugt unter einer Domain; bei öffentlichem Katalog kann GitHub Pages den Leseteil separat ausliefern. |
| Kleine API oder serverlose Funktionen | Ja, **wenn in der Website editiert wird** | Anmeldung, App-Schlüssel, Rechte, Branch/PR, serverseitige Prüfung. Serverlos bedeutet keinen eigenen 24/7-Prozess, aber einen aktiven Hosting-Dienst. |
| Geheimnisspeicher und Protokollierung | Ja, für Bearbeitung | Schlüssel und Betriebsdiagnose; gegebenenfalls Bestandteil des API-Hosts. |
| Eigene Datenbank, Triple Store, Suchcluster | Zunächst nein | Git ist bei wenig Änderungen die Quelle; Suche entsteht beim Build. |
| Separater Identity Provider | Zunächst nein, **wenn alle Bearbeitenden GitHub nutzen** | Andernfalls werden eigene Anmeldung und Rollenverwaltung nötig. |

**Sichtbarkeitsgrenze:** GitHub Pages ist normalerweise öffentlich erreichbar, auch wenn das Quell-Repository privat ist. [Private Pages](https://docs.github.com/en/enterprise-cloud%40latest/pages/getting-started-with-github-pages/changing-the-visibility-of-your-github-pages-site) setzen GitHub Enterprise Cloud und passende Organisationseinstellungen voraus. Bei privatem Katalog müssen daher auch die ausgelieferten Daten und das Frontend vor unberechtigtem Zugriff geschützt werden. Die Entscheidung öffentlich/privat kann bis zur Bereitstellung offenbleiben.

## Aufwandsschätzung

**USER-CONFIRMED:** Eine zentrale Instanz, ein Repository, 20 bestehende Fälle und zwei bis drei notarielle Editoren. **ASSUMPTION:** GitHub-Konten für die Editoren, keine Aktenwerte, keine Abrechnung und keine zugesagte Verfügbarkeits-SLA. Die Spannen sind Entwickler-Personenwochen, keine Anbieterangebote; UX, notarielle Review-Zeit und Wartezeiten kommen hinzu.

| Arbeitspaket | Aufwand |
| --- | ---: |
| Datenvertrag, 20-Fälle-Import, UX-Konzept mit Erbausschlagung | 2–3 Wochen |
| Discover, Suche, Fall- und Bausteinseiten, fokussierter Graph | 3–5 Wochen |
| Strukturierte Pflege, Turtle-Roundtrip, semantischer Diff | 3–5 Wochen |
| GitHub-App-Anmeldung, Rechte, Branch/PR | 3–4 Wochen |
| Validierung, CI, Review-Status, Quellen/BPMN-Verknüpfung | 2–3 Wochen |
| Sicherheit, Barrierefreiheit, Notariats-Tests, Deployment | 3–5 Wochen |
| **Zentrale produktionsfähige Version** | **16–25 Entwicklerwochen** |

Ein **bedienbarer Pilot für Erbausschlagung** mit Suche, Bausteinseite, Änderung und PR-Vorschau erscheint in **6–9 Kalenderwochen** realistisch. Bei einer Vollzeit-Entwicklungskraft liegt die zentrale produktionsfähige Plattform etwa bei **4–6 Monaten**. Diese eigene Schätzung hat besonders bei verlustfreiem Turtle-Roundtrip, Authentifizierung und fachlicher Nutzerprüfung Unsicherheit.

Getrennte Notariatsräume, Abrechnung und Aktenverwaltung sind ausdrücklich nicht Teil der Schätzung. Die Bezeichnung „SaaS“ meint hier eine zentral gehostete Editor-Anwendung für einen gemeinsamen Katalog, nicht eine mehrmandantenfähige Fachplattform.

## Offene Produktentscheidungen und Abnahme

1. **OPEN:** Ist der Katalog öffentlich lesbar? Das bestimmt den Zugriffsschutz beim Hosting; eine öffentliche URL ist noch nicht nötig.
2. **OPEN:** Erhalten die zwei bis drei Bearbeitenden GitHub-Konten? Das ist der einfachste Identitätsweg; eine andere Anmeldung würde zusätzliche Technik erfordern.
3. **Pilot-Abnahme:** Eine Person aus dem Notariat findet eine Frage, sieht Quelle, Status und Beziehungen, ändert sie ohne Turtle-Kenntnisse, prüft die semantische Vorschau und erstellt einen PR. Der RDF-Graph bleibt außerhalb der beabsichtigten Änderung inhaltlich gleich. Technische Checks und notarielle Freigabe sind getrennt sichtbar.

Palantirs Bedienkonzept ist ein Produktmaßstab, kein Hinweis auf frei verfügbaren Ontology-Manager-Code. NaC sollte zuerst diese konkrete Nutzerreise beherrschen und die GitOps-Regeln erhalten.
