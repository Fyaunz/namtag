#!/usr/bin/env python3
"""
Namensschilder-Generator (CLI-Einstiegspunkt)
=============================================
Verwendung:
    python3 namensschilder.py
    python3 namensschilder.py -i data/teilnehmer.csv -o out/namensschilder.pdf
    python3 namensschilder.py --logo img/Logo_NAJU_ohneSchriftzug_blau.png
"""

import argparse
import sys
from pathlib import Path

from src.csv_reader import read_csv_entries
from src.renderer import (
    A4_HEIGHT_MM,
    A4_WIDTH_MM,
    DEFAULT_BADGE_H_MM,
    DEFAULT_BADGE_W_MM,
    DEFAULT_FONT,
    generate_pdf,
)


def main() -> None:
    script_dir = Path(__file__).resolve().parent

    parser = argparse.ArgumentParser(
        description="Generiert druckfertige Namensschilder auf DIN A4 aus einer CSV-Datei."
    )
    parser.add_argument(
        "-i", "--input",
        default=str(script_dir / "data" / "teilnehmer.csv"),
        help="Pfad zur CSV-Datei mit Namen und Funktionen (Standard: data/teilnehmer.csv)",
    )
    parser.add_argument(
        "-o", "--output",
        default=str(script_dir / "out" / "namensschilder.pdf"),
        help="Pfad zur Ausgabedatei als PDF (Standard: out/namensschilder.pdf)",
    )
    parser.add_argument(
        "-l", "--logo",
        default=str(script_dir / "img" / "Logo_NAJU_ohneSchriftzug_blau.png"),
        help="Pfad zur Logo-Datei (.svg, .png, .jpg) (Standard: img/Logo_NAJU_ohneSchriftzug_blau.png)",
    )
    parser.add_argument(
        "--no-logo",
        action="store_true",
        help="Namensschilder ohne Logo generieren",
    )
    parser.add_argument(
        "-f", "--font",
        default=DEFAULT_FONT,
        help=f"Schriftart für Namen und Funktion (z. B. 'Open Sans', 'Arial', 'Helvetica', 'Verdana'; Standard: '{DEFAULT_FONT}')",
    )
    parser.add_argument(
        "--width",
        type=float,
        default=DEFAULT_BADGE_W_MM,
        help=f"Breite eines Namensschilds in mm (Standard: {DEFAULT_BADGE_W_MM})",
    )
    parser.add_argument(
        "--height",
        type=float,
        default=DEFAULT_BADGE_H_MM,
        help=f"Höhe eines Namensschilds in mm (Standard: {DEFAULT_BADGE_H_MM})",
    )
    parser.add_argument(
        "--fill-blank",
        action="store_true",
        default=True,
        help="Restliche Plätze auf dem letzten A4-Bogen mit Blanko-Schildern (mit Schreiblinien) auffüllen (Standard: aktiv)",
    )
    parser.add_argument(
        "--no-fill-blank",
        action="store_false",
        dest="fill_blank",
        help="Restliche Plätze auf dem letzten A4-Bogen komplett leer lassen",
    )
    parser.add_argument(
        "--no-pronouns",
        action="store_true",
        help="Schreiblinie für Pronomen unter dem Namen ausblenden",
    )

    args = parser.parse_args()

    csv_path = Path(args.input)
    output_pdf = Path(args.output)
    logo_path = None if args.no_logo else Path(args.logo)

    if logo_path and not logo_path.exists():
        print(f"Hinweis: Logo '{logo_path}' nicht gefunden – fahre ohne Logo fort.", file=sys.stderr)
        logo_path = None

    entries = read_csv_entries(csv_path)
    if not entries:
        print(f"Keine Einträge in '{csv_path}' gefunden.", file=sys.stderr)
        sys.exit(1)

    cols = int(A4_WIDTH_MM // args.width)
    rows = int(A4_HEIGHT_MM // args.height)
    per_page = cols * rows

    pages = generate_pdf(
        entries=entries,
        output_pdf=output_pdf,
        badge_w=args.width,
        badge_h=args.height,
        logo_path=logo_path,
        fill_empty=args.fill_blank,
        show_pronoun_field=not args.no_pronouns,
        font_name=args.font,
    )

    print(f"Erfolgreich erstellt: {output_pdf.resolve()}")
    print(f"  - Namensschilder: {len(entries)} Stück ({args.width:.0f} × {args.height:.0f} mm)")
    print(f"  - Schriftart:     {args.font}")
    print(f"  - Anordnung:      {cols} × {rows} = {per_page} Schilder pro A4-Blatt")
    print(f"  - Seitenumfang:   {pages} A4-Seite(n)")
    print("  - Druckhinweis:   Beim Drucken 'Tatsächliche Größe' / 'Skalierung: 100%' wählen!")


if __name__ == "__main__":
    main()
