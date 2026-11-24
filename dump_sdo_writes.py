#!/usr/bin/env python3
"""Dump the SDO write list of CODESYS CANopen remote devices.

CODESYS stores the start-up SDO writes of a CANopen remote device in the
device's .object file as an "SDO List" parameter, an array of
Struct_SDOParameters elements (Index, Subindex, Value, Size, ...). This
script prints each entry, in download order, as

    sdoWrite(nodeId, 0x1400, 0x01, 0x80000201); // Disable PDO
"""

import argparse
import json
import re
import sys

SDO_LIST_TYPE = "Struct_SDOParameters"
PARAMETER_TYPE = "8c994079"


def unwrap(value):
    """Strip the "(type)" prefix from a serialised scalar."""
    if isinstance(value, str):
        return re.sub(r"^\([^)]*\)", "", value, count=1)
    return value


def iec_int(literal):
    """Parse an IEC 61131-3 integer literal such as 16#80, 2#1010 or 200."""
    text = unwrap(literal).replace("_", "").strip()
    if "#" in text:
        base, digits = text.split("#", 1)
        return int(digits, int(base))
    return int(text)


def walk(node):
    """Yield every dict in a nested JSON structure."""
    if isinstance(node, dict):
        yield node
        for child in node.values():
            yield from walk(child)
    elif isinstance(node, list):
        for child in node:
            yield from walk(child)


def sub_elements(element):
    """Return the child elements of a DALA element, or an empty list."""
    # DALA stands for "Data Access Layer Abstraction" in CODESYS.
    subs = element.get("SubElements")
    if not subs:
        return []
    return subs["@Value"]["elements"]["@Value"]


def visible_name(element):
    name = element.get("VisibleName") or {}
    return unwrap((name.get("@Value") or {}).get("Default")) or ""


def file_node_id(data):
    """Return the configured Node-ID of the device, or None."""
    for node in walk(data):
        if node.get("@Type") != PARAMETER_TYPE:
            continue
        param = node["@Value"]
        if unwrap(param.get("ParamType")) != "localTypes:RangeNodeID":
            continue
        dala = param["DalaElement"]["@Value"]
        simple = dala.get("SimpleType", {}).get("@Value", dala)
        return iec_int(simple["Value"])
    return None


def sdo_entries(data):
    """Yield (name, index, subindex, value, size_bits) for each SDO list entry."""
    for node in walk(data):
        element = node.get("@Value")
        if not isinstance(element, dict):
            continue
        if unwrap(element.get("TypeName")) != SDO_LIST_TYPE:
            continue
        fields = {
            unwrap(sub["@Value"]["Identifier"]): sub["@Value"]["Value"]
            for sub in sub_elements(element)
        }
        yield (
            visible_name(element),
            iec_int(fields["Index"]),
            iec_int(fields["Subindex"]),
            iec_int(fields["Value"]),
            iec_int(fields["Size"]),
        )


def format_entry(entry, node_id, comments):
    name, index, subindex, value, size = entry
    width = max(2, (size + 3) // 4)
    line = f"sdoWrite({node_id}, 0x{index:04X}, 0x{subindex:02X}, {size}, 0x{value:0{width}X});"
    if comments:
        line += f" // {name} ({size}-bit)"
    return line


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("objects", nargs="+", help="CODESYS .object file(s)")
    parser.add_argument(
        "--node-id",
        default="nodeId",
        help='first sdoWrite argument; "file" uses the Node-ID configured '
        "in the .object file (default: nodeId)",
    )
    parser.add_argument(
        "--no-comments", action="store_true", help="omit trailing entry comments"
    )
    args = parser.parse_args()

    found = False
    for path in args.objects:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        entries = list(sdo_entries(data))
        if not entries:
            print(f"{path}: no SDO list found", file=sys.stderr)
            continue
        found = True
        node_id = args.node_id
        if node_id == "file":
            node_id = file_node_id(data)
            if node_id is None:
                sys.exit(f"{path}: no Node-ID parameter found")
        if len(args.objects) > 1 and not args.no_comments:
            print(f"// {path}")
        for entry in entries:
            print(format_entry(entry, node_id, not args.no_comments))
    if not found:
        sys.exit(1)


if __name__ == "__main__":
    main()
