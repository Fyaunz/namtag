"""
CSV-Parser für Teilnehmerlisten (Namen und Funktionen).
"""

import csv
from pathlib import Path
from typing import List, Tuple


def wrap_text_two_lines(text: str) -> List[str]:
    """Bricht einen langen Text möglichst gleichmäßig an einem Leerzeichen in 2 Zeilen um."""
    words = text.split()
    if len(words) <= 1:
        return [text]
    mid = len(text) / 2
    best_split = 1
    best_diff = float("inf")
    running = 0
    for i in range(1, len(words)):
        running += len(words[i - 1]) + (1 if i > 1 else 0)
        diff = abs(mid - running)
        if diff < best_diff:
            best_diff = diff
            best_split = i
    return [" ".join(words[:best_split]), " ".join(words[best_split:])]


def read_csv_entries(csv_path: Path) -> List[Tuple[str, List[str]]]:
    """
    Liest Namen und Funktion(en) aus einer CSV-Datei.
    Unterstützt ',' und ';' als Trennzeichen sowie mehrzeilige Funktionen
    getrennt durch '|' (z. B. 'Zeile 1 | Zeile 2') oder zusätzliche Spalten.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV-Datei nicht gefunden: {csv_path}")

    raw_text = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            raw_text = csv_path.read_text(encoding=encoding)
            break
        except UnicodeDecodeError:
            continue

    if raw_text is None:
        raise ValueError(f"Konnte Kodierung der Datei {csv_path} nicht lesen.")

    lines = [line for line in raw_text.splitlines() if line.strip()]
    if not lines:
        return []

    sample = "\n".join(lines[:10])
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ";" if ";" in lines[0] else ","

    rows = list(csv.reader(lines, delimiter=delimiter))
    if not rows:
        return []

    first_row_lower = [c.strip().lower() for c in rows[0]]
    header_keywords = {
        "name", "vorname", "nachname", "funktion", "rolle", "titel", "organisation", "abteilung"
    }
    has_header = any(col in header_keywords for col in first_row_lower)

    name_idx = 0
    func_indices = [1]

    if has_header:
        header = first_row_lower
        data_rows = rows[1:]
        if "vorname" in header and "nachname" in header:
            vn_idx = header.index("vorname")
            nn_idx = header.index("nachname")
            name_idx = (vn_idx, nn_idx)
            func_indices = [i for i in range(len(header)) if i not in (vn_idx, nn_idx)]
        else:
            for i, col in enumerate(header):
                if "name" in col:
                    name_idx = i
                    break
            func_indices = [i for i in range(len(header)) if i != name_idx]
    else:
        data_rows = rows
        func_indices = list(range(1, len(rows[0])))

    entries: List[Tuple[str, List[str]]] = []
    for row in data_rows:
        if not any(cell.strip() for cell in row):
            continue

        if isinstance(name_idx, tuple):
            vn = row[name_idx[0]].strip() if name_idx[0] < len(row) else ""
            nn = row[name_idx[1]].strip() if name_idx[1] < len(row) else ""
            name = f"{vn} {nn}".strip()
        else:
            name = row[name_idx].strip() if name_idx < len(row) else ""

        if not name:
            continue

        func_lines: List[str] = []
        for idx in func_indices:
            if idx < len(row) and row[idx].strip():
                cell_val = row[idx].strip()
                parts = [p.strip() for p in cell_val.replace("\\n", "|").split("|") if p.strip()]
                func_lines.extend(parts)

        wrapped_func_lines: List[str] = []
        for line in func_lines:
            if len(line) > 28 and " " in line:
                wrapped_func_lines.extend(wrap_text_two_lines(line))
            else:
                wrapped_func_lines.append(line)

        entries.append((name, wrapped_func_lines))

    return entries

