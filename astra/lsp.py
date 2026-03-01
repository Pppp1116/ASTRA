import json
import sys
from dataclasses import is_dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse

from astra.ast import (
    ComptimeStmt,
    EnumDecl,
    FnDecl,
    ForStmt,
    IfStmt,
    LetStmt,
    MatchStmt,
    Name,
    StructDecl,
    WhileStmt,
)
from astra.check import run_check_source
from astra.parser import ParseError, parse
from astra.semantic import BUILTIN_SIGS, SemanticError, analyze


KEYWORDS = [
    "fn",
    "let",
    "return",
    "if",
    "else",
    "while",
    "for",
    "break",
    "continue",
    "struct",
    "enum",
    "type",
    "import",
    "mut",
    "pub",
    "extern",
    "async",
    "await",
    "unsafe",
    "match",
    "drop",
    "none",
]


def send(msg):
    b = json.dumps(msg).encode()
    sys.stdout.write(f"Content-Length: {len(b)}\r\n\r\n")
    sys.stdout.write(b.decode())
    sys.stdout.flush()


def read_msg():
    headers = {}
    while True:
        line = sys.stdin.readline()
        if not line:
            return None
        if line in ("\r\n", "\n", ""):
            break
        k, v = line.split(":", 1)
        headers[k.lower().strip()] = v.strip()
    n = int(headers.get("content-length", "0"))
    if n == 0:
        return None
    return json.loads(sys.stdin.read(n))


def _parse_diagnostics(text: str, uri: str):
    filename = _uri_to_filename(uri)
    result = run_check_source(text, filename=filename, collect_errors=True)
    out = []
    for diag in result.diagnostics:
        start_line = max(0, diag.span.line - 1)
        start_col = max(0, diag.span.col - 1)
        end_line = max(start_line, diag.span.end_line - 1)
        end_col = max(start_col + 1, diag.span.end_col - 1)
        item = {
            "range": {
                "start": {"line": start_line, "character": start_col},
                "end": {"line": end_line, "character": end_col},
            },
            "severity": 1,
            "source": "astra",
            "code": diag.code,
            "message": diag.message,
        }
        related = []
        for note in diag.notes:
            if note.span is None:
                continue
            note_uri = uri if note.span.filename == filename else _filename_to_uri(note.span.filename)
            related.append(
                {
                    "location": {
                        "uri": note_uri,
                        "range": {
                            "start": {
                                "line": max(0, note.span.line - 1),
                                "character": max(0, note.span.col - 1),
                            },
                            "end": {
                                "line": max(0, note.span.end_line - 1),
                                "character": max(0, note.span.end_col - 1),
                            },
                        },
                    },
                    "message": note.message,
                }
            )
        if related:
            item["relatedInformation"] = related
        out.append(item)
    return out


def _uri_to_filename(uri: str) -> str:
    if uri.startswith("file://"):
        parsed = urlparse(uri)
        path = unquote(parsed.path)
        if parsed.netloc:
            path = f"/{parsed.netloc}{path}"
        return path
    return uri


def _filename_to_uri(filename: str) -> str:
    if filename.startswith("file://"):
        return filename
    if filename.startswith("<") and filename.endswith(">"):
        return filename
    return Path(filename).resolve().as_uri()


def _word_at(text: str, line: int, character: int) -> str:
    lines = text.splitlines()
    if line < 0 or line >= len(lines):
        return ""
    row = lines[line]
    if not row:
        return ""
    pos = min(max(0, character), len(row) - 1)
    if not (row[pos].isalnum() or row[pos] == "_"):
        return ""
    s = pos
    e = pos
    while s > 0 and (row[s - 1].isalnum() or row[s - 1] == "_"):
        s -= 1
    while e + 1 < len(row) and (row[e + 1].isalnum() or row[e + 1] == "_"):
        e += 1
    return row[s : e + 1]


def _parse_and_analyze(text: str, uri: str):
    filename = _uri_to_filename(uri)
    try:
        prog = parse(text, filename=filename)
    except ParseError:
        return None
    try:
        analyze(prog, filename=filename)
    except SemanticError:
        # Keep partially typed AST if semantic analysis stops early.
        pass
    return prog


def _iter_ast(node):
    if is_dataclass(node):
        yield node
        for field in node.__dataclass_fields__.keys():
            yield from _iter_ast(getattr(node, field))
        return
    if isinstance(node, list):
        for item in node:
            yield from _iter_ast(item)
        return
    if isinstance(node, tuple):
        for item in node:
            yield from _iter_ast(item)


def _find_name_node_at(prog, line: int, character: int, word: str):
    line1 = line + 1
    col0 = character
    for node in _iter_ast(prog):
        if not isinstance(node, Name):
            continue
        if node.line != line1:
            continue
        start = max(0, node.col - 1)
        end = start + len(node.value)
        if start <= col0 < end and node.value == word:
            return node
    return None


def _decl_map(prog):
    out = {}
    for item in getattr(prog, "items", []):
        if isinstance(item, FnDecl):
            sig = ", ".join(f"{n}: {t}" for n, t in item.params)
            out[item.name] = {
                "kind": "function",
                "line": item.line,
                "col": item.col,
                "detail": f"fn {item.name}({sig}) -> {item.ret}",
            }
        elif isinstance(item, StructDecl):
            out[item.name] = {"kind": "struct", "line": item.line, "col": item.col, "detail": f"struct {item.name}"}
        elif isinstance(item, EnumDecl):
            out[item.name] = {"kind": "enum", "line": item.line, "col": item.col, "detail": f"enum {item.name}"}
    return out


def _stmt_max_line(st) -> int:
    max_line = getattr(st, "line", 0)
    for node in _iter_ast(st):
        ln = getattr(node, "line", 0)
        if isinstance(ln, int) and ln > max_line:
            max_line = ln
    return max_line


def _before_or_at(line: int, col: int, pos_line: int, pos_col: int) -> bool:
    return line < pos_line or (line == pos_line and col <= pos_col)


def _contains_line(st, line: int) -> bool:
    return getattr(st, "line", 0) <= line <= _stmt_max_line(st)


def _collect_locals_in_block(stmts, pos_line: int, pos_col: int, out: set[str]) -> None:
    for st in stmts:
        st_line = getattr(st, "line", 0)
        st_col = getattr(st, "col", 0)
        if not _before_or_at(st_line, st_col, pos_line, pos_col):
            break
        if isinstance(st, LetStmt):
            out.add(st.name)
            continue
        if isinstance(st, IfStmt):
            if st.then_body and _contains_line(st.then_body[0], pos_line):
                _collect_locals_in_block(st.then_body, pos_line, pos_col, out)
                return
            if st.else_body and _contains_line(st.else_body[0], pos_line):
                _collect_locals_in_block(st.else_body, pos_line, pos_col, out)
                return
            continue
        if isinstance(st, WhileStmt):
            if st.body and _contains_line(st.body[0], pos_line):
                _collect_locals_in_block(st.body, pos_line, pos_col, out)
                return
            continue
        if isinstance(st, ForStmt):
            if isinstance(st.init, LetStmt):
                out.add(st.init.name)
            if st.body and _contains_line(st.body[0], pos_line):
                _collect_locals_in_block(st.body, pos_line, pos_col, out)
                return
            continue
        if isinstance(st, MatchStmt):
            for _, arm_body in st.arms:
                if arm_body and _contains_line(arm_body[0], pos_line):
                    _collect_locals_in_block(arm_body, pos_line, pos_col, out)
                    return
            continue
        if isinstance(st, ComptimeStmt):
            if st.body and _contains_line(st.body[0], pos_line):
                _collect_locals_in_block(st.body, pos_line, pos_col, out)
                return


def _fn_for_line(prog, line: int):
    items = getattr(prog, "items", [])
    for i, item in enumerate(items):
        if not isinstance(item, FnDecl):
            continue
        next_line = None
        for nxt in items[i + 1 :]:
            ln = getattr(nxt, "line", 0)
            if ln:
                next_line = ln
                break
        if item.line <= line and (next_line is None or line < next_line):
            return item
    return None


def _completions(text: str, uri: str, line: int, character: int):
    items = []
    seen = set()

    def add(label: str, kind: int, detail: str):
        if not label or label in seen:
            return
        seen.add(label)
        items.append({"label": label, "kind": kind, "detail": detail})

    for k in KEYWORDS:
        add(k, 14, "keyword")
    for b in BUILTIN_SIGS:
        if b.startswith("__"):
            continue
        add(b, 3, "builtin")

    prog = _parse_and_analyze(text, uri)
    if prog is None:
        return items
    dmap = _decl_map(prog)
    for name, info in dmap.items():
        kind = 3 if info["kind"] == "function" else 7
        add(name, kind, info["kind"])

    fn = _fn_for_line(prog, line + 1)
    if fn is not None:
        for name, _typ in fn.params:
            add(name, 6, "param")
        locals_in_scope: set[str] = set()
        _collect_locals_in_block(fn.body, line + 1, character + 1, locals_in_scope)
        for name in sorted(locals_in_scope):
            add(name, 6, "local")
    return items


def main(argv=None):
    docs: dict[str, str] = {}
    while True:
        msg = read_msg()
        if not msg:
            break
        method = msg.get("method")
        if method == "initialize":
            send(
                {
                    "jsonrpc": "2.0",
                    "id": msg["id"],
                    "result": {
                        "capabilities": {
                            "textDocumentSync": 1,
                            "hoverProvider": True,
                            "completionProvider": {"resolveProvider": False},
                            "definitionProvider": True,
                        }
                    },
                }
            )
            continue
        if method == "textDocument/didOpen":
            td = msg.get("params", {}).get("textDocument", {})
            uri = td.get("uri", "<memory>")
            text = td.get("text", "")
            docs[uri] = text
            send({"jsonrpc": "2.0", "method": "textDocument/publishDiagnostics", "params": {"uri": uri, "diagnostics": _parse_diagnostics(text, uri)}})
            continue
        if method == "textDocument/didChange":
            params = msg.get("params", {})
            uri = params.get("textDocument", {}).get("uri", "<memory>")
            changes = params.get("contentChanges", [])
            if changes:
                docs[uri] = changes[-1].get("text", "")
            send({"jsonrpc": "2.0", "method": "textDocument/publishDiagnostics", "params": {"uri": uri, "diagnostics": _parse_diagnostics(docs.get(uri, ""), uri)}})
            continue
        if method == "textDocument/hover":
            params = msg.get("params", {})
            uri = params.get("textDocument", {}).get("uri", "<memory>")
            pos = params.get("position", {})
            text = docs.get(uri, "")
            line = pos.get("line", 0)
            character = pos.get("character", 0)
            symbol = _word_at(text, line, character)
            if symbol in KEYWORDS:
                contents = f"`{symbol}` keyword"
            elif symbol:
                prog = _parse_and_analyze(text, uri)
                node = _find_name_node_at(prog, line, character, symbol) if prog is not None else None
                inferred = getattr(node, "inferred_type", None) if node is not None else None
                if inferred:
                    contents = f"`{symbol}`: `{inferred}`"
                else:
                    dmap = _decl_map(prog) if prog is not None else {}
                    decl = dmap.get(symbol)
                    if decl is not None:
                        contents = decl["detail"]
                    elif symbol in BUILTIN_SIGS:
                        sig = BUILTIN_SIGS[symbol]
                        args = ", ".join(sig.args or ["..."])
                        contents = f"`builtin {symbol}({args}) -> {sig.ret}`"
                    else:
                        contents = f"Astra symbol `{symbol}`"
            else:
                contents = "Astra source"
            send({"jsonrpc": "2.0", "id": msg["id"], "result": {"contents": contents}})
            continue
        if method == "textDocument/completion":
            params = msg.get("params", {})
            uri = params.get("textDocument", {}).get("uri", "<memory>")
            pos = params.get("position", {})
            send(
                {
                    "jsonrpc": "2.0",
                    "id": msg["id"],
                    "result": _completions(docs.get(uri, ""), uri, pos.get("line", 0), pos.get("character", 0)),
                }
            )
            continue
        if method == "textDocument/definition":
            params = msg.get("params", {})
            uri = params.get("textDocument", {}).get("uri", "<memory>")
            pos = params.get("position", {})
            text = docs.get(uri, "")
            symbol = _word_at(text, pos.get("line", 0), pos.get("character", 0))
            prog = _parse_and_analyze(text, uri)
            target = None
            if prog is not None:
                target = _decl_map(prog).get(symbol)
            if target is None:
                send({"jsonrpc": "2.0", "id": msg["id"], "result": None})
                continue
            line0 = max(0, int(target["line"]) - 1)
            col0 = max(0, int(target["col"]) - 1)
            send(
                {
                    "jsonrpc": "2.0",
                    "id": msg["id"],
                    "result": {
                        "uri": uri,
                        "range": {
                            "start": {"line": line0, "character": col0},
                            "end": {"line": line0, "character": col0 + 1},
                        },
                    },
                }
            )
            continue
        if "id" in msg:
            send({"jsonrpc": "2.0", "id": msg["id"], "result": None})


if __name__ == "__main__":
    main()
