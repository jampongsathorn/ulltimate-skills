#!/usr/bin/env python3
"""Fail-closed validator for facts-ledger.md.

Usage:
    python3 validate_facts_ledger.py facts-ledger.md
    python3 validate_facts_ledger.py facts-ledger.md --json

Exit codes: 0 = valid, 1 = validation errors, 2 = usage/IO error.

Every error names the entry, the field, and the accepted fix.
Pure stdlib, no dependencies.
"""

import json
import re
import sys
from datetime import datetime

ENTRY_RE = re.compile(r"^###\s+(F-\d{3,})\s*·\s*(.*)$")
FIELD_RE = re.compile(r"^-\s+([a-z_\-]+)\s*:\s*(.*)$")

PROVENANCE = ("agent-observed", "user-reported", "documented", "inferred", "hypothesis")
DECAY = ("immutable", "stable-until-change", "decaying", "volatile")
STATUS = ("active", "superseded", "retired")
REQUIRED_FIELDS = (
    "fact",
    "provenance",
    "as_of",
    "decay",
    "re-verify",
    "status",
    "supersedes",
    "superseded_by",
)
OPTIONAL_FIELDS = ("note",)
DASH = ("—", "-", "")  # "no value" markers

PLACEHOLDER_RE = re.compile(r"TODO|FIXME|TBD|<[^>]*>|XXX", re.IGNORECASE)


class Entry:
    def __init__(self, fid, title, lineno):
        self.fid = fid
        self.title = title.strip()
        self.lineno = lineno
        self.fields = {}
        self.field_lineno = {}

    def error(self, field, msg):
        return f"{self.fid} (line {self.lineno}): field '{field}' — {msg}"


def parse_ledger(text):
    entries = []
    current = None
    for lineno, line in enumerate(text.splitlines(), 1):
        m = ENTRY_RE.match(line)
        if m:
            current = Entry(m.group(1), m.group(2), lineno)
            entries.append(current)
            continue
        if current is None:
            continue
        m = FIELD_RE.match(line.strip())
        if m:
            field, value = m.group(1), m.group(2).strip()
            if field not in current.fields:
                current.fields[field] = value
                current.field_lineno[field] = lineno
    return entries


def is_dash(value):
    return value in DASH


def check_reverify(entry, errors):
    v = entry.fields["re-verify"]
    if PLACEHOLDER_RE.search(v):
        errors.append(
            entry.error(
                "re-verify",
                "placeholder value is not accepted. Fix: use one of "
                "`<exact one-liner command>`, `gated: <who/what must authorize>`, "
                "or `never: <safety reason>`.",
            )
        )
        return
    if v.startswith("`"):
        if not v.endswith("`") or len(v) < 3:
            errors.append(
                entry.error(
                    "re-verify",
                    "command form must be a complete backtick-quoted one-liner "
                    "like `curl -s https://...`. Fix: close the backtick with a real command.",
                )
            )
        return
    if v.startswith("gated:") or v.startswith("never:"):
        if len(v) <= len(v.split(":", 1)[0]) + 1:
            errors.append(
                entry.error(
                    "re-verify",
                    f"'{v.split(':', 1)[0]}' needs a reason after the colon. "
                    "Fix: `gated: <condition>` or `never: <safety reason>`.",
                )
            )
        return
    errors.append(
        entry.error(
            "re-verify",
            "value is not one of the three accepted forms. Fix: "
            "`<exact one-liner command>`, `gated: <condition>`, or `never: <safety reason>`.",
        )
    )


def validate(text):
    errors = []
    entries = parse_ledger(text)

    if not entries:
        errors.append(
            "ledger: no entries found. Fix: add entries as "
            "'### F-001 · <short title>' followed by '- field: value' lines."
        )
        return errors

    seen = {}
    for e in entries:
        if e.fid in seen:
            errors.append(
                f"{e.fid} (line {e.lineno}): duplicate id — first defined at line {seen[e.fid]}. "
                "Fix: give this entry a new unused F-id (e.g. F-003)."
            )
        else:
            seen[e.fid] = e.lineno
        if not e.title:
            errors.append(
                f"{e.fid} (line {e.lineno}): entry title is empty. "
                "Fix: '### F-001 · <short title — what the fact is>'."
            )

    for e in entries:
        for f in REQUIRED_FIELDS:
            if f not in e.fields:
                errors.append(
                    f"{e.fid} (line {e.lineno}): missing required field '{f}'. "
                    f"Fix: add '- {f}: <value>' to the entry."
                )
            elif not e.fields[f] and f != "re-verify":
                errors.append(
                    f"{e.fid} (line {e.lineno}): field '{f}' is empty. "
                    "Fix: fill it in (use '—' only for supersedes/superseded_by)."
                )

        unknown = set(e.fields) - set(REQUIRED_FIELDS) - set(OPTIONAL_FIELDS)
        for f in sorted(unknown):
            errors.append(
                f"{e.fid} (line {e.field_lineno[f]}): unknown field '{f}'. "
                f"Fix: accepted fields are {', '.join(REQUIRED_FIELDS + OPTIONAL_FIELDS)}."
            )

        if "provenance" in e.fields and e.fields["provenance"]:
            v = e.fields["provenance"]
            if v not in PROVENANCE:
                errors.append(
                    f"{e.fid} (line {e.field_lineno['provenance']}): provenance '{v}' is not in the vocabulary. "
                    f"Fix: one of {', '.join(PROVENANCE)}."
                )

        if "decay" in e.fields and e.fields["decay"]:
            v = e.fields["decay"]
            if v not in DECAY:
                errors.append(
                    f"{e.fid} (line {e.field_lineno['decay']}): decay '{v}' is not in the vocabulary. "
                    f"Fix: one of {', '.join(DECAY)}."
                )

        if "as_of" in e.fields and e.fields["as_of"]:
            v = e.fields["as_of"]
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                errors.append(
                    f"{e.fid} (line {e.field_lineno['as_of']}): as_of '{v}' is not a date. "
                    "Fix: YYYY-MM-DD (e.g. 2026-10-08)."
                )

        if "status" in e.fields and e.fields["status"]:
            v = e.fields["status"]
            if v not in STATUS:
                errors.append(
                    f"{e.fid} (line {e.field_lineno['status']}): status '{v}' is not in the vocabulary. "
                    f"Fix: one of {', '.join(STATUS)}."
                )

        if "re-verify" in e.fields and e.fields["re-verify"]:
            check_reverify(e, errors)

        # supersede link consistency
        sup = e.fields.get("supersedes", "—")
        sup_by = e.fields.get("superseded_by", "—")
        if not is_dash(sup):
            if not re.fullmatch(r"F-\d{3,}", sup):
                errors.append(
                    f"{e.fid} (line {e.field_lineno.get('supersedes', e.lineno)}): "
                    f"supersedes '{sup}' is not an F-id. Fix: '—' or 'F-###'."
                )
            elif sup not in seen:
                errors.append(
                    f"{e.fid} (line {e.field_lineno.get('supersedes', e.lineno)}): "
                    f"supersedes points to {sup}, which does not exist. "
                    "Fix: point at a real F-id, or use '—'."
                )
        if not is_dash(sup_by):
            if not re.fullmatch(r"F-\d{3,}", sup_by):
                errors.append(
                    f"{e.fid} (line {e.field_lineno.get('superseded_by', e.lineno)}): "
                    f"superseded_by '{sup_by}' is not an F-id. Fix: '—' or 'F-###'."
                )
            elif sup_by not in seen:
                errors.append(
                    f"{e.fid} (line {e.field_lineno.get('superseded_by', e.lineno)}): "
                    f"superseded_by points to {sup_by}, which does not exist. "
                    "Fix: point at a real F-id, or use '—'."
                )

        if e.fields.get("status") == "active" and not is_dash(sup_by):
            errors.append(
                f"{e.fid} (line {e.lineno}): status is 'active' but superseded_by is '{sup_by}'. "
                "Fix: set status to 'superseded', or clear superseded_by to '—'."
            )

    # two-sided supersede agreement
    by_id = {e.fid: e for e in entries}
    for e in entries:
        sup = e.fields.get("supersedes", "—")
        if is_dash(sup) or sup not in by_id:
            continue
        target = by_id[sup]
        if is_dash(target.fields.get("superseded_by", "—")):
            errors.append(
                f"{e.fid}: claims to supersede {sup}, but {sup}.superseded_by is '—'. "
                f"Fix: set {sup}.superseded_by to {e.fid} (both sides must agree)."
            )
        elif target.fields.get("superseded_by") != e.fid:
            errors.append(
                f"{e.fid}: claims to supersede {sup}, but {sup}.superseded_by is "
                f"'{target.fields.get('superseded_by')}'. Fix: make both sides point at each other."
            )

    return errors


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print((__doc__ or "").strip(), file=sys.stderr)
        return 2
    path = argv[1]
    as_json = "--json" in argv
    try:
        text = open(path, encoding="utf-8").read()
    except OSError as exc:
        print(f"error: cannot read {path}: {exc}", file=sys.stderr)
        return 2
    errors = validate(text)
    if as_json:
        print(json.dumps({"file": path, "valid": not errors, "errors": errors}, indent=2))
    else:
        if errors:
            for err in errors:
                print(f"INVALID: {err}")
            print(f"\n{len(errors)} error(s) in {path}.")
        else:
            print(f"OK: {path} — ledger is valid.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
