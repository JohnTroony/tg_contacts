#!/usr/bin/env python3
import json
import csv
import argparse
import os
import sys
from datetime import datetime

# ---------- Colors ----------
class C:
    ENABLED = True
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

def color(text, c):
    if not C.ENABLED:
        return text
    return f"{c}{text}{C.RESET}"

# ---------- Banner ----------
def banner():
    print(color("\n╔════════════════════════════════════════════╗", C.CYAN))
    print(color("║ Telegram Contacts → Android Import Tool    ║", C.CYAN))
    print(color("║        Convert to CSV or VCF (Ultimate)    ║", C.CYAN))
    print(color("╚════════════════════════════════════════════╝\n", C.CYAN))

# ---------- Phone Normalization ----------
COUNTRY_CODES = {
    "KE": "254"
}

def normalize_phone(phone, country=None):
    if not phone:
        return phone, False, False

    phone = phone.strip()
    normalized_00 = False
    normalized_country = False

    if phone.startswith("00"):
        phone = "+" + phone[2:]
        normalized_00 = True

    if country in COUNTRY_CODES:
        cc = COUNTRY_CODES[country]

        if phone.startswith("0") and len(phone) >= 9:
            phone = f"+{cc}{phone[1:]}"
            normalized_country = True

        elif phone.startswith(cc) and not phone.startswith("+"):
            phone = f"+{phone}"
            normalized_country = True

        elif phone.startswith("7") and len(phone) >= 9:
            phone = f"+{cc}{phone}"
            normalized_country = True

    return phone, normalized_00, normalized_country

# ---------- Progress ----------
def progress(current, total):
    percent = int((current / total) * 100)
    bar = "#" * (percent // 4)
    print(f"\rProcessing: [{bar:<25}] {percent}%", end="", flush=True)

# ---------- Main ----------
def main():
    parser = argparse.ArgumentParser(
        description="Convert Telegram JSON contacts to CSV or VCF (Android-ready)"
    )
    parser.add_argument("-i", "--input", required=True, help="Telegram JSON file")
    parser.add_argument("-o", "--output", help="Output file name")
    parser.add_argument("--name-mode", choices=["first", "last", "both"], default="both")
    parser.add_argument("--country", help="Country code (e.g. KE)")
    parser.add_argument("--dedupe", choices=["phone"], help="Deduplicate contacts")
    parser.add_argument("--format", choices=["csv", "vcf"], default="csv")
    parser.add_argument("--no-color", action="store_true")

    args = parser.parse_args()
    C.ENABLED = not args.no_color

    banner()

    if not os.path.exists(args.input):
        print(color("✖ Input file not found", C.RED))
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        contacts = data["contacts"]["list"]
    except KeyError:
        print(color("✖ Invalid Telegram JSON structure", C.RED))
        sys.exit(1)

    output = args.output or f"android_contacts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{args.format}"

    seen_phones = set()
    total = len(contacts)
    written = 0
    dupes = 0
    normalized_00 = 0
    normalized_country = 0

    if args.format == "csv":
        out = open(output, "w", newline="", encoding="utf-8")
        writer = csv.writer(out)

        headers = []
        if args.name_mode in ("first", "both"):
            headers.append("First Name")
        if args.name_mode in ("last", "both"):
            headers.append("Last Name")
        headers.append("Phone")
        writer.writerow(headers)

    else:
        out = open(output, "w", encoding="utf-8")

    for i, c in enumerate(contacts, 1):
        first = c.get("first_name", "")
        last = c.get("last_name", "")
        phone_raw = c.get("phone_number", "")

        phone, n00, ncty = normalize_phone(phone_raw, args.country)
        normalized_00 += n00
        normalized_country += ncty

        if args.dedupe == "phone":
            if phone in seen_phones:
                dupes += 1
                continue
            seen_phones.add(phone)

        if args.format == "csv":
            row = []
            if args.name_mode in ("first", "both"):
                row.append(first)
            if args.name_mode in ("last", "both"):
                row.append(last)
            row.append(phone)
            writer.writerow(row)

        else:
            out.write("BEGIN:VCARD\n")
            out.write("VERSION:3.0\n")
            out.write(f"N:{last};{first};;;\n")
            out.write(f"FN:{first} {last}".strip() + "\n")
            out.write(f"TEL;TYPE=CELL:{phone}\n")
            out.write("END:VCARD\n\n")

        written += 1
        if total >= 100:
            progress(i, total)

    out.close()
    if total >= 100:
        print()

    # ---------- Stats ----------
    print(color("\n✔ Conversion complete\n", C.GREEN))
    print(color("[+] Summary", C.BOLD))
    print(color(f"• Input contacts        : {total}", C.CYAN))
    print(color(f"• Written contacts      : {written}", C.CYAN))
    print(color(f"• Duplicates removed    : {dupes}", C.YELLOW))
    print(color(f"• 00 → + normalized     : {normalized_00}", C.CYAN))
    print(color(f"• Country normalized    : {normalized_country}", C.CYAN))
    print(color(f"• Output format         : {args.format.upper()}", C.CYAN))
    print(color(f"\n[-] Output file: {output}\n", C.GREEN))

if __name__ == "__main__":
    main()

def entry():
    main()
