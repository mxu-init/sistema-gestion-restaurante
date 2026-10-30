from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ALLOWED_TYPES: tuple[str, ...] = (
    "build",
    "chore",
    "ci",
    "docs",
    "feat",
    "fix",
    "perf",
    "refactor",
    "revert",
    "style",
    "test",
)

MAX_SUBJECT_LENGTH = 100
MAX_LINE_LENGTH = 100

SKIP_PREFIXES: tuple[str, ...] = ("Merge ", 'Revert "')

AUTOSQUASH_PREFIXES: tuple[str, ...] = ("amend! ", "fixup! ", "squash! ")

COMMIT_RE = re.compile(
    r"^(?P<type>[a-z]+)"
    r"(?:\((?P<scope>[a-z0-9]+(?:[-/][a-z0-9]+)*)\))?"
    r"(?P<breaking>!)?"
    r": (?P<subject>\S.*)$"
)

TRAILER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9-]*: ")

ACCENT_RE = re.compile(r"[áéíóúüñ¿¡ÁÉÍÓÚÜÑ]")

URL_RE = re.compile(r"https?://\S+|www\.\S+")

SPANISH_WORDS: frozenset[str] = frozenset(
    {
        "al",
        "ella",
        "ellos",
        "la",
        "lo",
        "los",
        "las",
        "de",
        "del",
        "el",
        "en",
        "esa",
        "ese",
        "esta",
        "este",
        "esto",
        "mi",
        "mis",
        "nosotros",
        "se",
        "su",
        "sus",
        "tu",
        "tus",
        "un",
        "una",
        "unas",
        "unos",
        "ustedes",
        "vosotros",
        "yo",
        "aunque",
        "como",
        "con",
        "cuando",
        "cuanto",
        "dónde",
        "desde",
        "donde",
        "entre",
        "hacia",
        "hasta",
        "mas",
        "ni",
        "para",
        "pero",
        "por",
        "porque",
        "que",
        "quien",
        "quienes",
        "sino",
        "sobre",
        "ya",
        "agrega",
        "agregado",
        "agregada",
        "agregar",
        "añade",
        "añadido",
        "añadir",
        "arregla",
        "arreglar",
        "arreglo",
        "borra",
        "borrado",
        "borrar",
        "cambia",
        "cambiado",
        "cambiar",
        "cambio",
        "cambios",
        "carga",
        "cargado",
        "cargar",
        "conecta",
        "conectar",
        "corrige",
        "corregir",
        "correccion",
        "corrección",
        "crea",
        "creado",
        "crear",
        "elimina",
        "eliminado",
        "eliminar",
        "envia",
        "enviado",
        "enviar",
        "ejecuta",
        "ejecutar",
        "guarda",
        "guardar",
        "implementa",
        "implementado",
        "implementacion",
        "implementación",
        "implementar",
        "inicia",
        "iniciado",
        "iniciar",
        "instala",
        "instalado",
        "instalar",
        "mejora",
        "mejorado",
        "mejorar",
        "modifica",
        "modificado",
        "modificacion",
        "modificación",
        "modificar",
        "muestra",
        "mostrar",
        "obtener",
        "refactoriza",
        "refactorizacion",
        "refactorización",
        "refactorizar",
        "selecciona",
        "seleccionar",
        "traduce",
        "traduccion",
        "traducción",
        "traducir",
        "valida",
        "validar",
        "verifica",
        "verificar",
        "campo",
        "campos",
        "carta",
        "cliente",
        "codigo",
        "código",
        "configuracion",
        "configuración",
        "conexion",
        "conexión",
        "contraseña",
        "descripcion",
        "descripción",
        "documentacion",
        "documentación",
        "funcion",
        "función",
        "mensaje",
        "mensajes",
        "mesa",
        "mesas",
        "nombre",
        "nombres",
        "nueva",
        "nuevo",
        "nuevas",
        "nuevos",
        "pedido",
        "pedidos",
        "peticion",
        "petición",
        "prueba",
        "pruebas",
        "problema",
        "problemas",
        "respuesta",
        "respuestas",
        "ruta",
        "rutas",
        "sistema",
        "tabla",
        "tablas",
        "usuario",
        "usuarios",
        "validacion",
        "validación",
        "versión",
    }
)

SPANISH_WORD_RE = re.compile(
    r"\b(?: " + "|".join(sorted(SPANISH_WORDS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)

FORMAT_HELP = (
    "Rules\n"
    "  format : <type>(<scope>): <subject>\n"
    f"  types  : {', '.join(ALLOWED_TYPES)}\n"
    f"  subject: lowercase start, no trailing period, max {MAX_SUBJECT_LENGTH} characters\n"
    f"  body   : blank line after the subject, max {MAX_LINE_LENGTH} characters (trailers exempt)\n"
    "  language: English only (no Spanish words or accented characters)\n"
    "\n"
    "Examples\n"
    "  feat(auth): add login endpoint\n"
    "  fix(db): correct nullable column\n"
    "  docs: update installation guide\n"
)


def load_lines(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    lines = [line for line in text.splitlines() if not line.lstrip().startswith("#")]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def find_spanish_words(text: str) -> list[str]:
    text = URL_RE.sub(" ", text)
    hits: list[str] = []
    for match in SPANISH_WORD_RE.finditer(text):
        token = match.group(0)
        if token.isupper():
            continue
        hits.append(token)
    return hits


def check_english(lines: list[str]) -> list[str]:
    errors: list[str] = []
    for number, line in enumerate(lines, start=1):
        if ACCENT_RE.search(line):
            errors.append(
                f"line {number}: accented characters are not allowed "
                "(write the message in English)"
            )
        words = find_spanish_words(line)
        if words:
            errors.append(
                f"line {number}: Spanish word(s) not allowed: {', '.join(sorted(set(words)))}"
            )
    return errors


def check_subject(subject: str) -> list[str]:
    errors: list[str] = []

    if subject != subject.rstrip():
        errors.append("the subject must not have trailing whitespace")
    if len(subject) > MAX_SUBJECT_LENGTH:
        errors.append(
            f"the subject is {len(subject)} characters long (max {MAX_SUBJECT_LENGTH})"
        )
    if subject.endswith("."):
        errors.append("the subject must not end with a period")

    match = COMMIT_RE.match(subject)
    if match is None:
        errors.append(f"'{subject}' does not follow the Conventional Commits format")
        errors.append("expected: <type>(<scope>): <subject in lowercase English>")
        return errors

    commit_type = match.group("type")
    if commit_type not in ALLOWED_TYPES:
        errors.append(
            f"type '{commit_type}' is not allowed; "
            f"use one of: {', '.join(ALLOWED_TYPES)}"
        )

    inner_subject = match.group("subject")
    if inner_subject[:1].isupper():
        errors.append("the subject must start with a lowercase letter")

    return errors


def check_body(lines: list[str]) -> list[str]:
    errors: list[str] = []

    if len(lines) > 1 and lines[1].strip():
        errors.append("separate the subject from the body with a blank line")

    for number, line in enumerate(lines[2:], start=3):
        if line != line.rstrip():
            errors.append(f"line {number} has trailing whitespace")
        if len(line) > MAX_LINE_LENGTH and not TRAILER_RE.match(line):
            errors.append(
                f"line {number} is {len(line)} characters long (max {MAX_LINE_LENGTH})"
            )

    return errors


def validate(lines: list[str]) -> list[str]:
    if not lines:
        return ["the commit message is empty"]

    if lines[0].startswith(SKIP_PREFIXES):
        return []

    subject = lines[0]
    for prefix in AUTOSQUASH_PREFIXES:
        if subject.startswith(prefix):
            subject = subject[len(prefix) :]
            break

    errors: list[str] = []
    errors.extend(check_english(lines))
    errors.extend(check_subject(subject))
    errors.extend(check_body(lines))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a git commit message (Conventional Commits, English)."
    )
    parser.add_argument(
        "message_file",
        help="path to the file that contains the commit message",
    )
    args = parser.parse_args(argv)

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, OSError):
            pass

    path = Path(args.message_file)
    if not path.is_file():
        print(
            f"commit-msg-guardian: cannot read '{path}' - file not found",
            file=sys.stderr,
        )
        return 1

    errors = validate(load_lines(path))
    if errors:
        print("commit-msg-guardian: the commit message was rejected\n", file=sys.stderr)
        for number, error in enumerate(errors, start=1):
            print(f"  {number}. {error}", file=sys.stderr)
        print(f"\n{FORMAT_HELP}", file=sys.stderr)
        return 1

    print("commit-msg-guardian: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
