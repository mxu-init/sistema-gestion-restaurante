# sistema-gestion-restaurante

## Guía de commits

Este repositorio está protegido por un **guardián de commits** construido con
[pre-commit](https://pre-commit.com/). El guardián se ejecuta en local en cada
`git commit` y **rechaza** cualquier mensaje que no cumpla las reglas siguientes,
para que el historial sea coherente y esté escrito en inglés.

### Instalar el guardián (una vez por clonación local)

```bash
pip install pre-commit
pre-commit install
```

### Formato del mensaje

```
<type>(<scope>): <asunto escrito en inglés, empieza en minúscula, máx 100 caracteres>
```

| Regla | Detalle |
| --- | --- |
| Formato | Conventional Commits: `type(scope): subject` |
| Tipos | `build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`, `refactor`, `revert`, `style`, `test` |
| Asunto | empieza en minúscula, sin punto final, sin espacios al final, máximo **100** caracteres |
| Cuerpo | opcional; separado del asunto por una línea en blanco, máximo **100** caracteres por línea (los trailers como `Signed-off-by:` están exentos) |
| Idioma | **Solo inglés**: se rechazan palabras en español y caracteres con tilde (`á é í ó ú ü ñ ¿ ¡`) |
| Scope | opcional, en minúsculas con guiones (`auth`, `db`, `api-endpoints`) |
| Excepciones | los mensajes generados por git (`Merge ...` / `Revert "..."`) se aceptan tal cual |

### Ejemplos

**Aceptados**

```bash
git commit -m "feat(auth): add login endpoint"
git commit -m "fix(db): correct nullable column"
git commit -m "docs: update installation guide"
```

**Rechazados**

```bash
git commit -m "first commit"
git commit -m "feat: Add users."
git commit -m "fix: corrección del login"
git commit -m "arreglo: cosa rara"
```

### Validar un mensaje manualmente

```bash
pre-commit run commit-msg --hook-stage commit-msg --commit-msg-filename ruta/al/mensaje.txt
```

El guardián vive en [`scripts/check_commit_msg.py`](scripts/check_commit_msg.py)
y su configuración en [`.pre-commit-config.yaml`](.pre-commit-config.yaml).
