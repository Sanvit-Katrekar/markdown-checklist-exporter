# Markdown Checklist Exporter

Convert any Markdown checklist into a beautiful, interactive PDF with clickable checkboxes.

Perfect for travel packing lists, shopping lists, project planning, event preparation, and any checklist you want to use digitally or print.

## Features

* ✅ Interactive PDF checkboxes
* 🎨 Clean, modern PDF styling
* 📋 Supports Obsidian task syntax (`- [ ]`, `- [x]`)
* 📑 Preserves Markdown headings
* 📊 Supports Markdown tables
* 🖨️ Print-friendly layout
* 🔗 Removes Obsidian wikilinks (`[[Link]]`)
* 🚫 Special handling for "Do Not Carry" sections
* ⚡ Simple CLI powered by UV

---

## Example

### Input

```md
# Packing List

## Essentials

- [ ] Passport
- [ ] Wallet
- [ ] Phone Charger

## Clothes

- [ ] T-Shirts
- [ ] Jeans
```

### Output

A clean PDF with interactive checkboxes that can be ticked directly in most PDF viewers.

---

## Requirements

### UV

Install UV:

```bash
uv --version
```

If UV is not installed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### LaTeX

The project requires `pdflatex`.

#### Ubuntu / Debian

```bash
sudo apt install texlive-full
```

#### macOS

```bash
brew install --cask mactex
```

#### Windows

Install MiKTeX:

https://miktex.org

Verify installation:

```bash
pdflatex --version
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/Sanvit-Katrekar/markdown-checklist-exporter.git
cd markdown-checklist-exporter
```

## Usage

Convert a markdown file into a tickable PDF:

```bash
uv run main.py checklist.md
```

Output:

```text
output/checklist.pdf
```

---

## Supported Markdown

### Headings

```md
# Section
## Subsection
### Category
#### Notes
```

### Checklists

```md
- [ ] Passport
- [ ] Laptop
- [x] Phone Charger
```

### Lists

```md
- Item 1
- Item 2
- Item 3
```

### Tables

```md
| Item | Quantity |
|------|----------|
| Shirt | 3 |
| Socks | 5 |
```

---

## How It Works

1. Reads an Obsidian Markdown file
2. Parses headings, checklists, lists, and tables
3. Converts Markdown into LaTeX
4. Creates interactive PDF form checkboxes
5. Compiles the document using `pdflatex`
6. Saves the generated PDF to the `output/` directory

---

## Notes

### Wikilinks

Obsidian wikilinks are removed:

```md
[[Trip Planning]]
```

### Unicode & Emojis

Unsupported Unicode characters and emojis are stripped to maximize compatibility with `pdflatex`.

---

## Use Cases

* Travel packing lists
* Student checklists
* Shopping lists
* Project planning
* Event preparation
* Printable planners
* Personal productivity workflows

---

## License

MIT License
