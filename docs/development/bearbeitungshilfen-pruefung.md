# Prüfung der Bearbeitungshilfen

Stand: 13.10.2026. Geprüft ist das erste Paket der [eigenständigen Funktionen](eigenstaendige-funktionen.md). Der JSON-/Paketadapter für schema ist noch nicht Teil dieses Pakets.

## Lokale Prüfung

- Python 3.12.14 in einer temporären Umgebung aus dem verifizierten gebündelten Runtime; Abhängigkeiten aus requirements.txt. Die vorhandene lokale .venv war wegen eines fehlenden Python-Installationspfads nicht ausführbar und wurde nicht verändert.
- 62 synthetische Pythonprüfungen bestanden. Lernquellen und generierte Fassungen stimmen überein; JavaScript-Syntax geprüft.
- 35 synthetische Browserprüfungen mit installiertem Edge bestanden. Nach einer reinen Anordnungskorrektur drei betroffene Prüfungen erneut bestanden. Testkonto und Daten sind ausschließlich künstlich.
- Getrennte Datenintegration: 48 Python- und fünf Browserprüfungen gegen `notariat8/ontology`, Datencommit `d0b69e48d90b2ae42f81406833c094f74d9fdf77`, bestanden. Der Datencheckout war sauber und wurde nicht verändert. Browser-Schreibwege verwenden einen lokalen GitHub-Ersatz.

## Sichtprüfung

Die zentrale Browserprüfung erfasste Training auf Desktop und Mobil ohne Seitenfehler, Konsolenfehler oder fehlgeschlagene Anfragen. Die Aufnahmen wurden tatsächlich angesehen. Zusätzlich wurden Verbindungsauswahl, Bearbeitungsformular und die geänderte Trainingsfolie 9 im Editor bei 1536 × 760 CSS-Pixeln und Geräteskalierung 2,5 betrachtet. Menü, Bereichs- und Baumauswahl bleiben erreichbar; Formular und Graph scrollen intern. Die Satzvorschau steht nach der Auswahlzeile; Hinweise werden verständlich umgebrochen.

Die zusätzliche mobile Aufnahme bei 390 × 844 CSS-Pixeln zeigt keine Seitenüberläufe. Der Graph bleibt ein intern beweglicher Arbeitsbereich. Das sichtbare Konto wurde vor der Aufnahme als künstliches `browser-tester` geprüft. Bilder und Diagnoseprotokolle bleiben lokal; keine Browserprofile, Zugangsdaten oder privaten Inhalte werden veröffentlicht.

## Grenzen

Die lokale Sichtprüfung bestätigt keine Anmeldung eines echten Kontos auf Azure. GitHub-CI, Container, aktive Azure-Revision und ausgelieferte Release-Kennung benötigen ihren eigenen Auslieferungsnachweis. Die bestehende CI prüft zusätzlich die neu eingebundene guidance.js sowohl im Container als auch auf der produktiven Domain gegen ihren SHA256. Fachliche Abnahme und IAM-Aktivierung bleiben getrennte Aufgaben.
