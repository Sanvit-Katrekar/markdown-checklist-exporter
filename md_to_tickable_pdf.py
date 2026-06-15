"""
Convert an Obsidian markdown file with checklists to a tickable PDF.
Usage: python md_to_tickable_pdf.py input.md
Output: output/<filename>.pdf (relative to the script)
"""

import re
import subprocess
import sys
import os
import shutil


def md_to_latex(md_path):
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    latex_lines = []
    in_itemize = False
    in_donotcarry = False
    in_table = False
    table_rows = []
    table_col_count = 0
    checkbox_counter = [0]

    def next_cb_name():
        checkbox_counter[0] += 1
        return f"cb{checkbox_counter[0]}"

    def close_list():
        nonlocal in_itemize
        if in_itemize:
            latex_lines.append(r'\end{itemize}')
            in_itemize = False

    def is_table_row(s):
        return s.startswith('|') and s.endswith('|')

    def is_separator_row(s):
        # e.g. |---|:---:|---|
        return is_table_row(s) and re.match(r'^\|[\s\|\-:]+\|$', s)

    def parse_table_cells(s):
        # Split on | and strip, dropping the empty first/last from leading/trailing |
        parts = s.split('|')
        return [cell.strip() for cell in parts[1:-1]]

    def flush_table():
        nonlocal in_table, table_rows, table_col_count
        if not table_rows:
            in_table = False
            return
        cols = table_col_count
        col_spec = 'l' + ('X' * (cols - 1)) if cols > 1 else 'X'
        # Use tabularx for auto-width, with first col left-aligned and rest auto
        col_spec = '|' + '|'.join(['l'] + ['X'] * (cols - 1)) + '|'
        latex_lines.append(r'\vspace{4pt}')
        latex_lines.append(r'{\small')
        latex_lines.append(r'\begin{tabularx}{\linewidth}{' + col_spec + r'}')
        latex_lines.append(r'\hline')
        for i, row in enumerate(table_rows):
            # Pad or trim to expected column count
            while len(row) < cols:
                row.append('')
            row = row[:cols]
            cells = ' & '.join(
                (r'\textbf{' + escape_latex(c) + r'}' if i == 0 else escape_latex(c))
                for c in row
            )
            latex_lines.append(cells + r' \\')
            latex_lines.append(r'\hline')
        latex_lines.append(r'\end{tabularx}')
        latex_lines.append(r'}')
        latex_lines.append(r'\vspace{4pt}')
        in_table = False
        table_rows = []
        table_col_count = 0

    for line in lines:
        stripped = line.rstrip()

        # Strip [[wikilinks]] entirely (including display text)
        stripped = re.sub(r'\[\[[^\]]*\]\]', '', stripped).strip()

        # Handle table rows
        if is_table_row(stripped):
            if is_separator_row(stripped):
                # Separator row — defines column count, skip output
                if not in_table and table_rows:
                    # We've just seen the header row; now separator confirms it's a table
                    in_table = True
                    table_col_count = len(table_rows[0])
            else:
                close_list()
                if not in_table:
                    # First row before separator — buffer as header
                    in_table = True
                    table_rows = [parse_table_cells(stripped)]
                    table_col_count = len(table_rows[0])
                else:
                    table_rows.append(parse_table_cells(stripped))
            continue

        # Non-table line: flush any open table first
        if in_table:
            flush_table()

        # Skip blank lines
        if stripped == '':
            continue

        # Detect do-not-carry sections
        if re.search(r'do not carry', stripped, re.IGNORECASE):
            in_donotcarry = True
        elif re.match(r'^#{1,4} ', stripped):
            in_donotcarry = False

        if m := re.match(r'^#### (.+)', stripped):
            close_list()
            title = m.group(1)
            latex_lines.append(r'\vspace{2pt}' + '\n' + r'{\small\itshape\color{muted}' + escape_latex(title) + r'}\vspace{8pt}')

        elif m := re.match(r'^### (.+)', stripped):
            close_list()
            title = m.group(1)
            latex_lines.append(f'\\subsubsection*{{{escape_latex(title)}}}\\vspace{{4pt}}')

        elif m := re.match(r'^## (.+)', stripped):
            close_list()
            title = m.group(1)
            latex_lines.append(f'\\subsection*{{{escape_latex(title)}}}\\vspace{{4pt}}')

        elif m := re.match(r'^# (.+)', stripped):
            close_list()
            title = m.group(1)
            latex_lines.append(f'\\section*{{{escape_latex(title)}}}\\vspace{{4pt}}')

        elif m := re.match(r'^- \[ \] (.+)', stripped):
            if not in_itemize:
                latex_lines.append(r'\begin{itemize}[leftmargin=1.6em,label={},itemsep=1pt,parsep=0pt,topsep=1pt,partopsep=0pt]')
                in_itemize = True
            text = m.group(1)
            if in_donotcarry:
                latex_lines.append(f'  \\item[\\raisebox{{0.15em}}{{\\textcolor{{muted}}{{\\tiny\\ding{{108}}}}}}] {escape_latex(text)}')
            else:
                name = next_cb_name()
                latex_lines.append(f'  \\item[\\mycheck{{{name}}}{{false}}] {escape_latex(text)}')

        elif m := re.match(r'^- \[x\] (.+)', stripped, re.IGNORECASE):
            if not in_itemize:
                latex_lines.append(r'\begin{itemize}[leftmargin=1.6em,label={},itemsep=1pt,parsep=0pt,topsep=1pt,partopsep=0pt]')
                in_itemize = True
            text = m.group(1)
            if in_donotcarry:
                latex_lines.append(f'  \\item[\\raisebox{{0.15em}}{{\\textcolor{{muted}}{{\\tiny\\ding{{108}}}}}}] {escape_latex(text)}')
            else:
                name = next_cb_name()
                latex_lines.append(f'  \\item[\\mycheck{{{name}}}{{true}}] {escape_latex(text)}')

        elif m := re.match(r'^- (.+)', stripped):
            if not in_itemize:
                latex_lines.append(r'\begin{itemize}[leftmargin=*,itemsep=1pt,parsep=0pt,topsep=1pt,partopsep=0pt]')
                in_itemize = True
            text = m.group(1)
            latex_lines.append(f'  \\item {escape_latex(text)}')

        else:
            close_list()
            latex_lines.append(escape_latex(stripped))

    # Flush any table or list still open at end of file
    if in_table:
        flush_table()
    close_list()
    return '\n'.join(latex_lines)


def escape_latex(text):
    # Strip [[wikilinks]] entirely
    text = re.sub(r'\[\[[^\]]*\]\]', '', text).strip()
    # Strip emojis and other non-Latin Unicode that pdflatex can't handle
    text = re.sub(r'[^\x00-\x7F\u00C0-\u024F]', '', text).strip()
    replacements = [
        ('\\', r'\textbackslash{}'),
        ('&', r'\&'),
        ('%', r'\%'),
        ('$', r'\$'),
        ('#', r'\#'),
        ('^', r'\^{}'),
        ('_', r'\_'),
        ('{', r'\{'),
        ('}', r'\}'),
        ('~', r'\~{}'),
    ]
    for char, replacement in replacements:
        text = text.replace(char, replacement)
    text = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', text)
    text = re.sub(r'\*(.+?)\*', r'\\textit{\1}', text)
    return text


def escape_latex_inline(text):
    replacements = [
        ('\\', r'\textbackslash{}'),
        ('&', r'\&'),
        ('%', r'\%'),
        ('$', r'\$'),
        ('#', r'\#'),
        ('^', r'\^{}'),
        ('_', r'\_'),
        ('{', r'\{'),
        ('}', r'\}'),
        ('~', r'\~{}'),
    ]
    for char, replacement in replacements:
        text = text.replace(char, replacement)
    return text


def build_latex_document(body, doc_title):
    escaped_title = escape_latex_inline(doc_title)
    return (
        r"""\documentclass[12pt]{article}
\usepackage[margin=0.85in, top=1.1in, bottom=1.1in, headheight=15pt]{geometry}
\usepackage{hyperref}
\usepackage{xcolor}
\usepackage{titlesec}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{microtype}
\usepackage{mdframed}
\usepackage{fancyhdr}
\usepackage[parfill]{parskip}
\usepackage{enumitem}
\usepackage{pifont}
\usepackage{tabularx}
\usepackage{booktabs}

% ── Colour palette ───────────────────────────────────────────────
\definecolor{primary}{HTML}{2B7FFF}
\definecolor{darkblue}{HTML}{1A5FCC}
\definecolor{muted}{HTML}{888888}
\definecolor{lightblue}{HTML}{EBF2FF}
\definecolor{checkborder}{HTML}{2B7FFF}

% ── Checkbox ─────────────────────────────────────────────────────
\newcommand{\mycheck}[2]{%
  \raisebox{-0.05em}{%
    \CheckBox[%
      name=#1,%
      width=11pt,%
      height=11pt,%
      bordercolor=checkborder,%
      backgroundcolor={},%
      checkboxsymbol=\ding{51},%
      checked=#2%
    ]{}%
  }%
}

% ── Section styling ──────────────────────────────────────────────
\titleformat{\section}{\color{primary}\Large\bfseries}{}{0em}{}[{\color{primary}\titlerule[1.5pt]}]
\titlespacing{\section}{0pt}{1.0em}{0.4em}

\titleformat{\subsection}{\color{primary}\large\bfseries}{}{0em}{}
\titlespacing{\subsection}{0pt}{0.8em}{0.2em}

\titleformat{\subsubsection}{\color{darkblue}\normalsize\bfseries}{}{0em}{}
\titlespacing{\subsubsection}{0pt}{0.6em}{0.1em}

% ── Header / Footer ──────────────────────────────────────────────
\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0.4pt}
\fancyhead[L]{\textcolor{primary}{\small """ + escaped_title + r"""}}
\fancyhead[R]{\textcolor{muted}{\small\thepage}}
\renewcommand{\headrule}{\color{primary}\hrule width\headwidth height\headrulewidth}

\setlength{\parskip}{3pt}
\setlength{\parindent}{0pt}

\begin{document}
\begin{Form}

% ── Title block ──────────────────────────────────────────────────
\begin{mdframed}[
  backgroundcolor=lightblue,
  linecolor=primary,
  linewidth=0.4pt,
  innerleftmargin=18pt,
  innerrightmargin=18pt,
  innertopmargin=14pt,
  innerbottommargin=14pt,
  roundcorner=0pt
]
  {\color{darkblue}\LARGE\mdseries """ + escaped_title + r"""}\\[3pt]
  {\color{muted}\small Tap a checkbox to mark it done}
\end{mdframed}

\vspace{0.5em}

"""
        + body +
        r"""

\end{Form}
\end{document}
"""
    )


def compile_pdf(latex_source, output_path):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tmpdir = os.path.join(script_dir, "temp")
    os.makedirs(tmpdir, exist_ok=True)
    try:
        tex_file = os.path.join(tmpdir, "output.tex")
        with open(tex_file, "w", encoding="utf-8") as f:
            f.write(latex_source)

        for _ in range(2):
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "output.tex"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                encoding="utf-8",   # FIX 1: force UTF-8 instead of system cp1252
                errors="replace",   # FIX 1: don't crash on undecodable bytes
            )

        compiled_pdf = os.path.join(tmpdir, "output.pdf")
        if not os.path.exists(compiled_pdf):
            print("LaTeX compilation failed. Log output:")
            print((result.stdout or "")[-3000:])
            sys.exit(1)

        shutil.copy(compiled_pdf, output_path)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
