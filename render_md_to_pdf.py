import argparse
import os
from convert_pdf_to_structured_md_and_pdf import markdown_to_pdf


def main():
    parser = argparse.ArgumentParser(description='Rendre un Markdown structuré en PDF sans parser le PDF source.')
    parser.add_argument('--md_in', type=str, required=True, help='Fichier Markdown structuré en entrée')
    parser.add_argument('--pdf_out', type=str, required=True, help='Fichier PDF de sortie')
    args = parser.parse_args()

    if not os.path.exists(args.md_in):
        raise FileNotFoundError(f"Markdown introuvable: {args.md_in}")

    markdown_to_pdf(args.md_in, args.pdf_out)
    print(f"PDF généré dans {args.pdf_out}")


if __name__ == '__main__':
    main()
