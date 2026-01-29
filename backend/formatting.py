import string


def format_fmt_name(fmt: str, resolve_token):
    """
    Pure formatter for fmt_name. resolve_token(field_name) returns value for a token.
    """
    formatter = string.Formatter()
    pieces = []
    has_field = False
    for literal_text, field_name, format_spec, conversion in formatter.parse(fmt):
        if literal_text:
            pieces.append(literal_text)
        if field_name is None:
            continue
        has_field = True

        value = resolve_token(field_name)

        if conversion:
            if conversion == "s":
                value = str(value)
            elif conversion == "r":
                value = repr(value)
            elif conversion == "a":
                value = ascii(value)

        fmt_spec = format_spec or ""
        pieces.append(format(value, fmt_spec))

    if not has_field and "{" not in fmt and "}" not in fmt:
        # compatible: fmt_name used as a single token
        return str(resolve_token(fmt))

    return "".join(pieces)


def resolve_fmt_value(token: str, package_nodes, packages):
    # token 格式: p#0.attr 或 p#0.f#0.attr 或 p@name.f@name.attr
    parts = token.split(".", 2)
    if len(parts) < 2:
        raise RuntimeError(f"fmt_name token invalid: {token}")

    pkg_sel = parts[0]
    if pkg_sel.startswith("p@"):
        pkg_name = pkg_sel[2:]
        pkg = next((p for p in packages if p.name == pkg_name), None)
        pkg_idx = next((i for i, p in enumerate(packages) if p.name == pkg_name), -1)
    elif pkg_sel.startswith("p#") and pkg_sel[2:].isdigit():
        pkg_idx = int(pkg_sel[2:])
        if pkg_idx < 0 or pkg_idx >= len(packages):
            raise RuntimeError(f"fmt_name package index out of range: {pkg_sel}")
        pkg = packages[pkg_idx]
    else:
        raise RuntimeError(f"fmt_name package selector invalid: {pkg_sel}")

    if pkg is None:
        raise RuntimeError(f"fmt_name package not found: {pkg_sel}")

    if len(parts) == 2:  # 直接取包属性
        return get_package_attr(pkg, package_nodes[pkg_idx], parts[1])

    field_sel = parts[1]
    attr = parts[2]
    field, field_idx = select_field(pkg, pkg_idx, package_nodes, field_sel)
    return get_field_attr(field, package_nodes[pkg_idx], field_idx, attr)


def get_package_attr(package, pkg_xml_node, attr: str):
    # 优先取运行时属性，其次xml
    if hasattr(package, attr):
        return getattr(package, attr)
    fields_node = pkg_xml_node.find("Fields")
    if fields_node is not None and attr in fields_node.attrib:
        return maybe_int(fields_node.attrib.get(attr))
    if attr in pkg_xml_node.attrib:
        return maybe_int(pkg_xml_node.attrib.get(attr))
    raise RuntimeError(f"fmt_name package attr not found: {attr}")


def select_field(package, pkg_idx: int, package_nodes, selector: str):
    """Select a field object and index by f#序号 or f@名称."""
    if not selector.startswith("f"):
        raise RuntimeError(f"fmt_name field selector invalid: {selector}")

    field_nodes_xml = []
    fields_xml = package_nodes[pkg_idx].find("Fields")
    if fields_xml is None:
        raise RuntimeError(f"fmt_name package has no Fields")
    for node in list(fields_xml):
        if node.attrib.get("class", None) is None:
            continue
        field_nodes_xml.append(node)

    field_obj = None
    field_idx = -1
    if selector.startswith("f@"):
        fname = selector[2:]
        for idx, f in enumerate(package.all_field_list):
            if f.name == fname:
                field_obj = f
                field_idx = idx
                break
        if field_obj is None:
            raise RuntimeError(f"fmt_name field not found: {fname}")
    else:
        if not selector.startswith("f#"):
            raise RuntimeError(f"fmt_name field selector invalid: {selector}")
        idx_str = selector[2:]
        if idx_str == "" or not idx_str.isdigit():
            raise RuntimeError(f"fmt_name field index invalid: {selector}")
        field_idx = int(idx_str)
        if field_idx < 0 or field_idx >= len(package.all_field_list):
            raise RuntimeError(f"fmt_name field index out of range: {selector}")
        field_obj = package.all_field_list[field_idx]

    return field_obj, field_idx


def get_field_attr(field_obj, pkg_xml_node, field_idx: int, attr: str):
    """Resolve a field attribute (runtime attr first, then XML)."""
    if hasattr(field_obj, attr):
        return getattr(field_obj, attr)

    fields_node = pkg_xml_node.find("Fields")
    if fields_node is not None:
        field_nodes_xml = []
        for node in list(fields_node):
            if node.attrib.get("class", None) is None:
                continue
            field_nodes_xml.append(node)
        if 0 <= field_idx < len(field_nodes_xml):
            node = field_nodes_xml[field_idx]
            if attr in node.attrib:
                return maybe_int(node.attrib.get(attr))

    raise RuntimeError(f"fmt_name field attr not found: {attr}")


def maybe_int(val):
    """Try to convert numeric strings to int, otherwise return original."""
    if isinstance(val, str):
        try:
            return int(val, 0)
        except Exception:
            return val
    return val


def validate_filename(name: str):
    """Validate filename for Windows filesystem; return (ok, reason)."""
    if name is None:
        return False, "empty name"
    name = str(name)
    if name == "":
        return False, "empty name"

    invalid_chars = '<>:"/\\\\|?*'
    for ch in invalid_chars:
        if ch in name:
            return False, f"contains invalid char '{ch}'"

    base = name.rstrip(" .")
    if base == "":
        return False, "name ends with dot/space"
    if base != name:
        return False, "name ends with dot/space"

    upper = base.upper()
    reserved = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }
    if upper in reserved:
        return False, f"reserved name '{upper}'"

    if len(name) > 255:
        return False, "name too long (>255)"

    return True, ""
