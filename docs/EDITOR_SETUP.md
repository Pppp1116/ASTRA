# Formatting and Editor Setup

Arixa defaults are chosen for readability and consistency across CLI, docs, and editor tooling.

## Formatter defaults

- Indentation: 4 spaces (no tabs)
- Blocks: multiline by default (`{` on header line, body on new lines, `}` on its own line)
- Top-level spacing: one blank line between declarations
- Line-width preference: 100 columns

You can configure indentation via either `arfmt.toml` or `Arixa.toml`:

```toml
indent_width = 4
```

Valid values are `2`, `4`, or `8`.

You can also set `line_width` (default `100`) in the same files.

## Recommended coding fonts

Arixa does not force a global font, but these are recommended:

- Atkinson Hyperlegible Mono (recommended)
- JetBrains Mono
- Fira Code (ligatures disabled)

## VS Code setup

The Arixa VS Code extension already provides Arixa-scoped defaults.

If you want to set them manually, add this to `settings.json`:

```json
"[arixa]": {
  "editor.tabSize": 4,
  "editor.insertSpaces": true,
  "editor.detectIndentation": false,
  "editor.rulers": [100],
  "editor.wordWrap": "on",
  "editor.renderWhitespace": "boundary",
  "editor.guides.indentation": true,
  "editor.bracketPairColorization.enabled": true,
  "editor.minimap.enabled": false,
  "editor.fontLigatures": false,
  "editor.fontFamily": "Atkinson Hyperlegible Mono, JetBrains Mono, Fira Code"
}
```
