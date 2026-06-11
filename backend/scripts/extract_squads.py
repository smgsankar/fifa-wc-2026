"""Extract squad lists from the official FIFA squad-list PDF into seed_data/.

Usage (from the backend directory):
    python scripts/extract_squads.py ~/Downloads/SquadLists-English.pdf

Requires pdfplumber (not part of the server requirements):
    pip install pdfplumber

Each PDF page holds one team: a "Team Name (CODE)" line followed by a
26-player table (#, POS, PLAYER NAME, ... DOB, CLUB, ...) and a head-coach
row. Names are printed surname-first ("MASTIL Melvin") and reordered to
given-name-first ("Melvin MASTIL") on the way out.

Outputs:
  - squads.csv   country_code,team,number,position,name,dob,club
  - coaches.csv  country_code,team,name
"""

import csv
import logging
import re
import sys

import pdfplumber

from common import SEED_DIR

TEAM_HEADER = re.compile(r"^(.+?)\s*\(([A-Z]{3})\)$")
POSITIONS = {"GK", "DF", "MF", "FW"}


def clean(text: str) -> str:
    """The PDF font drops fi/ffi ligatures as NUL bytes; restore them."""
    text = text.replace("She\x00eld", "Sheffield").replace("\x00", "fi")
    return " ".join(text.split())


def is_surname_token(token: str) -> bool:
    """Surnames are printed in caps; 'Mc'/'Mac' prefixes stay mixed (McKENNIE)."""
    if token == token.upper():
        return True
    for prefix in ("Mc", "Mac"):
        rest = token.removeprefix(prefix)
        if rest != token and rest and rest == rest.upper():
            return True
    return False


def reorder_name(display: str) -> str:
    """'MASTIL Melvin' -> 'Melvin MASTIL'; mononyms ('ALISSON') unchanged."""
    tokens = display.split()
    i = 0
    while i < len(tokens) and is_surname_token(tokens[i]):
        i += 1
    if i == 0:
        raise ValueError(f"No surname prefix in player name {display!r}")
    return " ".join(tokens[i:] + tokens[:i])


def extract_team(page) -> tuple[str, str, list[dict], str]:
    team_name = country_code = None
    for line in (page.extract_text() or "").splitlines():
        m = TEAM_HEADER.match(line.strip())
        if m:
            team_name, country_code = m.groups()
            break
    if team_name is None:
        raise ValueError(f"No 'Team (CODE)' header on page {page.page_number}")

    players = []
    coach = None
    for row in page.extract_table() or []:
        cells = [clean(c) for c in row if c not in (None, "")]
        if not cells:
            continue
        if cells[0] == "Head coach":
            if coach is not None:
                raise ValueError(f"{team_name}: multiple head-coach rows")
            coach = reorder_name(cells[1])
            continue
        if len(cells) < 8 or not cells[0].isdigit():
            continue  # column headers
        number, position, name = cells[0], cells[1], cells[2]
        dob, club = cells[6], cells[7]
        if position not in POSITIONS:
            raise ValueError(f"{team_name} #{number}: unexpected position {position!r}")
        players.append(
            {
                "country_code": country_code,
                "team": team_name,
                "number": int(number),
                "position": position,
                "name": reorder_name(name),
                "dob": dob,
                "club": club,
            }
        )
    if coach is None:
        raise ValueError(f"{team_name}: no head-coach row")
    return team_name, country_code, players, coach


def main(pdf_path: str) -> None:
    rows, coaches = [], []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            team_name, country_code, players, coach = extract_team(page)
            if len(players) != 26:
                raise ValueError(f"{team_name}: expected 26 players, got {len(players)}")
            if sorted(p["number"] for p in players) != list(range(1, 27)):
                raise ValueError(f"{team_name}: shirt numbers are not 1-26")
            rows.append(sorted(players, key=lambda p: p["number"]))
            coaches.append({"country_code": country_code, "team": team_name, "name": coach})

    out_path = SEED_DIR / "squads.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0][0].keys()))
        writer.writeheader()
        for players in rows:
            writer.writerows(players)
    print(f"squads.csv: {len(rows)} teams, {sum(len(r) for r in rows)} players written")

    coaches_path = SEED_DIR / "coaches.csv"
    with open(coaches_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["country_code", "team", "name"])
        writer.writeheader()
        writer.writerows(coaches)
    print(f"coaches.csv: {len(coaches)} head coaches written")


if __name__ == "__main__":
    logging.getLogger("pdfminer").setLevel(logging.ERROR)
    if len(sys.argv) != 2:
        sys.exit("Usage: python scripts/extract_squads.py <SquadLists.pdf>")
    main(sys.argv[1])
