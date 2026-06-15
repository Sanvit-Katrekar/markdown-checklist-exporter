import sys
import os
from md_to_tickable_pdf import (
    md_to_latex,
    build_latex_document,
    compile_pdf
)
def main():
    if len(sys.argv) < 2:
        print("Usage: uv run main.py input.md")
        sys.exit(1)

    md_path = sys.argv[1]
    if not os.path.exists(md_path):
        print(f"File not found: {md_path}")
        sys.exit(1)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(md_path))[0]
    output_path = os.path.join(output_dir, base_name + ".pdf")
    doc_title = base_name.replace("-", " ").replace("_", " ")

    print(f"Reading: {md_path}")
    body = md_to_latex(md_path)
    latex_doc = build_latex_document(body, doc_title)
    print("Compiling PDF...")
    compile_pdf(latex_doc, output_path)
    print(f"Done! Saved to: {output_path}")

if __name__ == "__main__":
    main()
