"""Maintenance helper: retain superseded code as comments per project policy."""
import ast
from pathlib import Path


def replace_definition(filename, qualified_name, replacement):
    path = Path(filename)
    source = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source)
    nodes = tree.body
    for name in qualified_name.split("."):
        node = next(n for n in nodes if getattr(n, "name", None) == name)
        nodes = getattr(node, "body", [])
    start = min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])]) - 1
    lines = source.splitlines(keepends=True)
    indent = " " * node.col_offset
    old = indent + "# Superseded 2026-10-12: retained for rollback; corrected implementation below.\n"
    old += "".join(indent + "# " + line[node.col_offset:] if line.strip() else indent + "#\n"
                   for line in lines[start:node.end_lineno])
    lines[start:node.end_lineno] = [old + "\n" + replacement.rstrip() + "\n"]
    path.write_text("".join(lines), encoding="utf-8")
