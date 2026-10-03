# Entwurf, Prüfung und Übernahme

Tippen verändert zunächst den Browserzustand. Speichern öffnet die fachliche Vorschau. Bestätigung schreibt in deinen Entwurfszweig im Datenrepository. Einreichen erzeugt einen Pull Request. Diese Schritte erteilen keine notarielle Freigabe.

Eine andere berechtigte Person prüft die eingereichte Änderung. Fachliche Freigaben sind für eingetragene Notarkonten vorgesehen und beziehen sich auf den geprüften Commit. Änderungen nach der Prüfung benötigen eine Beurteilung des neuen Stands.

Der vereinbarte Pilot verwendet einen manuellen Merge-Weg: verantwortliche Person prüft fachliche Freigabe auf dem aktuellen Commit und erfolgreiche CI vor Übernahme. Eine technisch erzwungene GitHub-Mergesperre ist eine separate optionale Betriebsentscheidung.

Eigene gespeicherte Entwürfe lassen sich wieder öffnen oder ablegen. Beim Abmelden mit offenen Eingaben fragt der Editor vor dem Verwerfen. Ungespeicherte Eingaben sind nach Browserverlust nicht dauerhaft gesichert. Eine frühere Fassung erzeugt einen neuen Prüfentwurf nach Vergleich und ersetzt main nicht direkt.

Gespeichert wird genau die bestätigte Vorschau. Ändern sich Eingaben während deren Vorbereitung, muss Speichern erneut gewählt werden. Während des Schreibens bleiben Schließen und Weiter bearbeiten gesperrt. Bei einem Fehler zeigt die Vorschau den Hinweis und erlaubt einen erneuten Versuch; die Eingaben bleiben ungespeichert erhalten. Eine langsame Antwort beim Öffnen kann keine spätere Auswahl oder neu eingegebene Änderung ersetzen.

## Vorgehen

1. Änderungsgrund und fachlichen Quellenstand lesen.
2. Begriffe, Quellen und Beziehungen mit dem aktuellen Datencommit vergleichen.
3. Als andere berechtigte Person eine begründete Rückfrage oder Freigabe dokumentieren.
4. Bei neuem Commit den neuen Stand erneut prüfen.
5. Vor manuellem Merge Freigabe, Dateiumfang und CI bestätigen.

[Zur Übersicht](README.md) · [Training](../../training/README.md)
