"""
PDF-Renderer für DIN-A4-Namensschilder mit fpdf2.
"""

import math
import sys
from pathlib import Path
from typing import List, Optional, Tuple

try:
    from fpdf import FPDF
except ImportError:
    print(
        "Fehler: Die Python-Bibliothek 'fpdf2' ist nicht installiert.\n"
        "Bitte installieren mit:  pip install -r namensschilder/requirements.txt",
        file=sys.stderr,
    )
    sys.exit(1)

# DIN A4 Maße in Millimetern
A4_WIDTH_MM = 210.0
A4_HEIGHT_MM = 297.0

# Standard-Namensschild (Durable / Avery Standard-Einleger)
DEFAULT_BADGE_W_MM = 90.0
DEFAULT_BADGE_H_MM = 54.0
DEFAULT_FONT = "Open Sans"


def _find_ttf_pair(font_name: str) -> Optional[Tuple[Path, Path]]:
    """
    Sucht im lokalen 'fonts/'-Ordner sowie in gängigen System-Schriftordnern
    (macOS, Windows, Linux) nach einem Regular- und Bold-TTF-Paar für font_name.
    """
    project_fonts_dir = Path(__file__).resolve().parent.parent / "fonts"
    clean_key = font_name.lower().replace(" ", "").replace("-", "").replace("_", "")

    # Bekannte direkte Zuordnungen für häufige Schriftarten
    known_map = {
        "opensans": (
            [
                project_fonts_dir / "OpenSans-Regular.ttf",
                Path("/Library/Fonts/OpenSans-Regular.ttf"),
                Path.home() / "Library/Fonts/OpenSans-Regular.ttf",
                Path("/usr/share/fonts/truetype/open-sans/OpenSans-Regular.ttf"),
                Path("C:/Windows/Fonts/OpenSans-Regular.ttf"),
            ],
            [
                project_fonts_dir / "OpenSans-Bold.ttf",
                Path("/Library/Fonts/OpenSans-Bold.ttf"),
                Path.home() / "Library/Fonts/OpenSans-Bold.ttf",
                Path("/usr/share/fonts/truetype/open-sans/OpenSans-Bold.ttf"),
                Path("C:/Windows/Fonts/OpenSans-Bold.ttf"),
            ],
        ),
        "arial": (
            [
                Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
                Path("C:/Windows/Fonts/arial.ttf"),
                Path("/usr/share/fonts/truetype/msttcorefonts/Arial.ttf"),
            ],
            [
                Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
                Path("C:/Windows/Fonts/arialbd.ttf"),
                Path("/usr/share/fonts/truetype/msttcorefonts/Arial_Bold.ttf"),
            ],
        ),
        "verdana": (
            [
                Path("/System/Library/Fonts/Supplemental/Verdana.ttf"),
                Path("C:/Windows/Fonts/verdana.ttf"),
            ],
            [
                Path("/System/Library/Fonts/Supplemental/Verdana Bold.ttf"),
                Path("C:/Windows/Fonts/verdanab.ttf"),
            ],
        ),
        "georgia": (
            [
                Path("/System/Library/Fonts/Supplemental/Georgia.ttf"),
                Path("C:/Windows/Fonts/georgia.ttf"),
            ],
            [
                Path("/System/Library/Fonts/Supplemental/Georgia Bold.ttf"),
                Path("C:/Windows/Fonts/georgiab.ttf"),
            ],
        ),
        "trebuchetms": (
            [
                Path("/System/Library/Fonts/Supplemental/Trebuchet MS.ttf"),
                Path("C:/Windows/Fonts/trebuc.ttf"),
            ],
            [
                Path("/System/Library/Fonts/Supplemental/Trebuchet MS Bold.ttf"),
                Path("C:/Windows/Fonts/trebucbd.ttf"),
            ],
        ),
        "liberationsans": (
            [Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf")],
            [Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf")],
        ),
        "dejavusans": (
            [Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")],
            [Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")],
        ),
    }

    if clean_key in known_map:
        reg_candidates, bold_candidates = known_map[clean_key]
        reg = next((p for p in reg_candidates if p.exists()), None)
        bold = next((p for p in bold_candidates if p.exists()), None)
        if reg and bold:
            return reg, bold

    # Generische Suche in Schriftordnern nach Dateinamen
    search_dirs = [
        project_fonts_dir,
        Path("/System/Library/Fonts/Supplemental"),
        Path("/Library/Fonts"),
        Path.home() / "Library/Fonts",
        Path("C:/Windows/Fonts"),
        Path("/usr/share/fonts/truetype"),
    ]
    for sdir in search_dirs:
        if not sdir.exists():
            continue
        try:
            ttf_files = list(sdir.glob("*.ttf"))
        except PermissionError:
            continue

        matching = [
            f for f in ttf_files
            if clean_key in f.stem.lower().replace(" ", "").replace("-", "").replace("_", "")
            and "italic" not in f.stem.lower()
        ]
        if matching:
            bold_files = [f for f in matching if "bold" in f.stem.lower() or f.stem.lower().endswith("bd")]
            reg_files = [f for f in matching if f not in bold_files]
            if reg_files and bold_files:
                return reg_files[0], bold_files[0]
            if reg_files:
                return reg_files[0], reg_files[0]

    return None


def configure_fonts(pdf: FPDF, font_name: str = DEFAULT_FONT) -> str:
    """
    Konfiguriert die gewünschte Schriftart (Standard: 'Open Sans') im PDF.
    Unterstützt eingebettete TTF-Schriften sowie die PDF-Standardschriften
    (Helvetica, Times, Courier).
    """
    core_fonts = {"helvetica": "Helvetica", "times": "Times", "courier": "Courier"}
    if font_name.strip().lower() in core_fonts:
        return core_fonts[font_name.strip().lower()]

    pair = _find_ttf_pair(font_name)
    if pair is not None:
        reg_path, bold_path = pair
        pdf.add_font("CustomBadgeFont", style="", fname=str(reg_path))
        pdf.add_font("CustomBadgeFont", style="B", fname=str(bold_path))
        return "CustomBadgeFont"

    print(
        f"Hinweis: Schriftart '{font_name}' nicht als TTF gefunden – nutze Standard 'Open Sans' bzw. 'Helvetica'.",
        file=sys.stderr,
    )
    fallback_pair = _find_ttf_pair(DEFAULT_FONT)
    if fallback_pair is not None:
        reg_path, bold_path = fallback_pair
        pdf.add_font("CustomBadgeFont", style="", fname=str(reg_path))
        pdf.add_font("CustomBadgeFont", style="B", fname=str(bold_path))
        return "CustomBadgeFont"

    return "Helvetica"


def fit_font_size(
    pdf: FPDF,
    font_family: str,
    font_style: str,
    text: str,
    target_pt: float,
    max_width_mm: float,
    min_pt: float = 4.0,
) -> float:
    """
    Berechnet die passende Schriftgröße in Punkt (pt), damit der Text garantiert
    in max_width_mm passt (inkl. exakter Nachmessung in einer Schleife als Failsafe).
    """
    pdf.set_font(font_family, style=font_style, size=target_pt)
    if not text:
        return target_pt
    text_w = pdf.get_string_width(text)
    if text_w <= max_width_mm or text_w == 0:
        return target_pt

    scaled_pt = max(min_pt, target_pt * (max_width_mm / text_w) * 0.98)
    pdf.set_font(font_family, style=font_style, size=scaled_pt)
    while pdf.get_string_width(text) > max_width_mm and scaled_pt > min_pt:
        scaled_pt = max(min_pt, scaled_pt - 0.5)
        pdf.set_font(font_family, style=font_style, size=scaled_pt)
    return scaled_pt


def split_text_two_lines(text: str) -> List[str]:
    """
    Teilt einen langen Namen an Leerzeichen oder Bindestrichen so in 2 Zeilen,
    dass die längere der beiden Zeilen möglichst kurz ist.
    """
    words = text.split()
    if len(words) >= 2:
        best_pair = [text]
        best_max_len = len(text)
        for i in range(1, len(words)):
            l1 = " ".join(words[:i])
            l2 = " ".join(words[i:])
            current_max = max(len(l1), len(l2))
            if current_max < best_max_len:
                best_max_len = current_max
                best_pair = [l1, l2]
        # Nur umbrechen, wenn die längste Zeile dadurch spürbar kürzer wird (mind. 20 %)
        if best_max_len <= len(text) * 0.80:
            return best_pair

    if "-" in text and len(text) > 20:
        parts = text.split("-")
        mid_part = max(1, len(parts) // 2)
        l1 = "-".join(parts[:mid_part]) + "-"
        l2 = "-".join(parts[mid_part:])
        if max(len(l1), len(l2)) <= len(text) * 0.80:
            return [l1, l2]

    return [text]


def draw_badge(
    pdf: FPDF,
    x: float,
    y: float,
    w: float,
    h: float,
    name: str,
    func_lines: List[str],
    logo_path: Optional[Path],
    font_family: str = "Helvetica",
    show_pronoun_field: bool = True,
) -> None:
    """Zeichnet ein einzelnes Namensschild an Position (x, y) in mm auf die aktuelle PDF-Seite."""
    # Harter Clip-Bereich innerhalb des Schildes als absoluter Failsafe gegen Überragen
    margin_clip = 2.0
    with pdf.local_context(), pdf.rect_clip(
        x + margin_clip, y + 1.0, w - 2 * margin_clip, h - 2.0
    ):
        # 1. Logo oben links
        if logo_path is not None and logo_path.exists():
            pdf.image(
                str(logo_path),
                x=x + w * 0.068,
                y=y + h * 0.075,
                w=w * 0.30,
                h=h * 0.175,
                keep_aspect_ratio=True,
            )

        max_text_width = w * 0.86  # 77.4 mm maximale Textbreite

        # Prüfen, ob der Name einzeilig gut lesbar passt oder besser zweizeilig umgebrochen wird
        target_name_pt = (h * 0.136) * (72.0 / 25.4)  # ~20.8 pt
        wrap_threshold_pt = (h * 0.095) * (72.0 / 25.4)  # ~14.5 pt
        name_lines = [name] if name else []

        if name:
            pdf.set_font(font_family, style="B", size=target_name_pt)
            raw_w = pdf.get_string_width(name)
            single_line_pt = target_name_pt * (max_text_width / raw_w) if raw_w > max_text_width else target_name_pt
            if single_line_pt < wrap_threshold_pt and (" " in name or "-" in name):
                name_lines = split_text_two_lines(name)

        is_multiline_name = len(name_lines) > 1

        # Vertikale Ankerpunkte (dynamisch angepasst für 1- oder 2-zeilige Namen)
        if show_pronoun_field:
            name_baseline_y = y + (h * 0.365 if is_multiline_name else h * 0.42)
            pronoun_line_y = y + (h * 0.62 if is_multiline_name else h * 0.60)
            first_func_y = y + (h * 0.78 if len(func_lines) > 1 else h * 0.81)
        else:
            if not func_lines:
                name_baseline_y = y + (h * 0.50 if is_multiline_name else h * 0.56)
            elif len(func_lines) == 1:
                name_baseline_y = y + (h * 0.44 if is_multiline_name else h * 0.50)
            else:
                name_baseline_y = y + (h * 0.42 if is_multiline_name else h * 0.475)
            pronoun_line_y = 0.0
            first_func_y = name_baseline_y + (h * 0.24 if is_multiline_name else h * 0.185)

        # 2. Name (zentriert, fett, mit zweizeiligem Umbruch + exakter Skalierung als Failsafe)
        if name_lines:
            longest_name_line = max(name_lines, key=pdf.get_string_width)
            desired_pt = target_name_pt * (0.82 if is_multiline_name else 1.0)
            name_pt = fit_font_size(
                pdf, font_family, "B", longest_name_line, desired_pt, max_text_width
            )
            pdf.set_text_color(36, 36, 36)
            name_line_spacing = (name_pt * (25.4 / 72.0)) * 1.22

            for idx, nline in enumerate(name_lines):
                ny = name_baseline_y + idx * name_line_spacing
                line_w = pdf.get_string_width(nline)
                pdf.text(x=x + (w - line_w) / 2.0, y=ny, text=nline)

        # 3. Dezente hellgraue Schreiblinie für Pronomen direkt unter dem Namen
        if show_pronoun_field:
            line_w = w * 0.46
            line_start_x = x + (w - line_w) / 2.0
            pdf.set_draw_color(195, 195, 195)
            pdf.set_line_width(0.3)
            pdf.line(line_start_x, pronoun_line_y, line_start_x + line_w, pronoun_line_y)

        # 4. Funktion / Untertitel (inkl. exakter Breiten-Skalierung als Failsafe)
        if func_lines:
            target_func_pt = (h * 0.082) * (72.0 / 25.4)
            pdf.set_font(font_family, style="", size=target_func_pt)
            longest_line = max(func_lines[:3], key=pdf.get_string_width)
            func_pt = fit_font_size(
                pdf, font_family, "", longest_line, target_func_pt, max_text_width
            )
            pdf.set_text_color(48, 48, 48)

            line_spacing = (func_pt * (25.4 / 72.0)) * 1.42
            for idx, fline in enumerate(func_lines[:3]):
                fy = first_func_y + idx * line_spacing
                line_w = pdf.get_string_width(fline)
                pdf.text(x=x + (w - line_w) / 2.0, y=fy, text=fline)


def draw_cut_lines(
    pdf: FPDF,
    margin_x: float,
    margin_y: float,
    cols: int,
    rows: int,
    badge_w: float,
    badge_h: float,
) -> None:
    """Zeichnet gestrichelte innere Schnittlinien und äußere Schnittmarken."""
    grid_w = cols * badge_w
    grid_h = rows * badge_h

    with pdf.local_context():
        pdf.set_draw_color(184, 184, 184)
        pdf.set_line_width(0.15)
        pdf.set_dash_pattern(dash=1.5, gap=1.5)

        for c in range(cols + 1):
            lx = margin_x + c * badge_w
            pdf.line(lx, margin_y, lx, margin_y + grid_h)

        for r in range(rows + 1):
            ly = margin_y + r * badge_h
            pdf.line(margin_x, ly, margin_x + grid_w, ly)

        pdf.set_dash_pattern(dash=0, gap=0)
        pdf.set_draw_color(102, 102, 102)
        pdf.set_line_width(0.25)
        mark_len, mark_gap = 5.0, 2.0

        for c in range(cols + 1):
            lx = margin_x + c * badge_w
            pdf.line(lx, max(0.0, margin_y - mark_gap - mark_len), lx, margin_y - mark_gap)
            pdf.line(
                lx,
                margin_y + grid_h + mark_gap,
                lx,
                min(A4_HEIGHT_MM, margin_y + grid_h + mark_gap + mark_len),
            )

        for r in range(rows + 1):
            ly = margin_y + r * badge_h
            pdf.line(max(0.0, margin_x - mark_gap - mark_len), ly, margin_x - mark_gap, ly)
            pdf.line(
                margin_x + grid_w + mark_gap,
                ly,
                min(A4_WIDTH_MM, margin_x + grid_w + mark_gap + mark_len),
                ly,
            )


def generate_pdf(
    entries: List[Tuple[str, List[str]]],
    output_pdf: Path,
    badge_w: float = DEFAULT_BADGE_W_MM,
    badge_h: float = DEFAULT_BADGE_H_MM,
    logo_path: Optional[Path] = None,
    fill_empty: bool = False,
    show_pronoun_field: bool = True,
    font_name: str = DEFAULT_FONT,
) -> int:
    """Erstellt das mehrseitige A4-PDF und gibt die Anzahl der erzeugten Seiten zurück."""
    cols = int(A4_WIDTH_MM // badge_w)
    rows = int(A4_HEIGHT_MM // badge_h)
    per_page = cols * rows

    if per_page <= 0:
        raise ValueError(f"Ungültige Schildgröße {badge_w}x{badge_h} mm (passt nicht auf A4).")

    margin_x = (A4_WIDTH_MM - cols * badge_w) / 2.0
    margin_y = (A4_HEIGHT_MM - rows * badge_h) / 2.0

    total_entries = list(entries)
    if fill_empty and len(total_entries) % per_page != 0:
        missing = per_page - (len(total_entries) % per_page)
        total_entries.extend([("", [])] * missing)

    num_pages = max(1, math.ceil(len(total_entries) / per_page))

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)
    pdf.set_creator("Namensschilder-Generator")
    pdf.set_title("Namensschilder DIN A4")
    font_family = configure_fonts(pdf, font_name=font_name)

    for page_idx in range(num_pages):
        pdf.add_page()
        chunk = total_entries[page_idx * per_page : (page_idx + 1) * per_page]

        for idx, (name, func_lines) in enumerate(chunk):
            col, row = idx % cols, idx // cols
            if row >= rows:
                break
            draw_badge(
                pdf=pdf,
                x=margin_x + col * badge_w,
                y=margin_y + row * badge_h,
                w=badge_w,
                h=badge_h,
                name=name,
                func_lines=func_lines,
                logo_path=logo_path,
                font_family=font_family,
                show_pronoun_field=show_pronoun_field,
            )

        draw_cut_lines(pdf, margin_x, margin_y, cols, rows, badge_w, badge_h)

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_pdf))
    return num_pages

