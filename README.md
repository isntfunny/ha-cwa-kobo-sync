# CWA Kobo Sync

[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)

Bringt das aktuelle Kobo-Lesebuch aus Calibre-Web Automated (CWA) nach Home Assistant.

## Einrichtung

1. HACS -> Integrations -> Custom repositories.
2. Dieses Repository als Kategorie **Integration** hinzufuegen und installieren.
3. Home Assistant neu starten.
4. Einstellungen -> Geraete & Dienste -> **CWA Kobo Sync** hinzufuegen.
5. Den vollstaendigen Kobo-Sync-Link aus CWA einfuegen, z. B. `https://read.example.org/kobo/<token>`.

Der Link ist das einzige Eingabefeld. Er bleibt lokal in Home Assistant und wird weder geloggt noch als Entity-Attribut ausgegeben.

## Entitaeten

| Entitaet | Wert |
|---|---|
| Aktuelles Buch | Titel, mit Autor und Buch-ID als Attributen |
| Lesefortschritt | Kobo-Fortschritt in Prozent |
| Lesezeit | Von Kobo gemeldete Minuten fuer das aktuelle Buch |
| Verbleibende Lesezeit | Kobo-Schaetzung in Minuten |
| Letzte Kobo-Aenderung | Zeitstempel der letzten Fortschrittsaenderung |
| Liest gerade | Ob Kobo ein Buch mit Status `Reading` meldet |

Die Integration fragt CWA alle fuenf Minuten ab und verwaltet den Kobo-Delta-Sync-Token selbst. Sie greift nicht auf die CWA-Datenbank zu.

Kobo Sync stellt keine aktuelle Seitenzahl bereit. Kobo uebermittelt nur eine interne, vom Layout abhaengige Position und den Fortschritt in Prozent.
