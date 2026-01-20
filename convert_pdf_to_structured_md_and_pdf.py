
import re
import markdown
from markdown.extensions.toc import TocExtension
import pdfplumber
import os
from fpdf import FPDF
import sys
import argparse

def extract_lines(pdf_path):
    def group_words_into_lines(words, y_tolerance=2.0):
        lines = []
        for word in sorted(words, key=lambda w: (w['top'], w['x0'])):
            placed = False
            for line in lines:
                if abs(word['top'] - line['top']) <= y_tolerance:
                    line['words'].append(word)
                    placed = True
                    break
            if not placed:
                lines.append({'top': word['top'], 'words': [word]})
        return lines

    def join_words(words):
        words = sorted(words, key=lambda w: w['x0'])
        text = ''
        for i, w in enumerate(words):
            if i == 0:
                text = w['text']
            else:
                gap = w['x0'] - words[i - 1]['x1']
                if gap <= 1.0:
                    text += w['text']
                else:
                    text += ' ' + w['text']
        # Nettoyer les espaces autour des ponctuations email
        text = re.sub(r'\s+([@\.])\s+', r'\1', text)
        text = re.sub(r'\s+([@\.])', r'\1', text)
        text = re.sub(r'([@\.])\s+', r'\1', text)
        return text.strip()

    all_lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words(x_tolerance=1.0, y_tolerance=1.0, keep_blank_chars=False, use_text_flow=True)
            if not words:
                page_text = page.extract_text(x_tolerance=1.5, y_tolerance=2, layout=True)
                if not page_text:
                    continue
                for raw_line in page_text.split('\n'):
                    if raw_line.strip():
                        all_lines.append({'text': raw_line.strip()})
                continue

            for line in group_words_into_lines(words):
                line_text = join_words(line['words'])
                if line_text:
                    all_lines.append({'text': line_text})
    return all_lines

def detect_sections(lines):
    # Repérage des titres/sections et reconstruction des paragraphes
    section_titles = {
        'Diplômes, formations et postes.': 'Diplômes, formations et postes',
        'Résumé des formations antérieures': 'Résumé des formations antérieures',
        'Principales publications.': 'Principales publications',
        'Principales responsabilités scientifiques.': 'Principales responsabilités scientifiques',
        'Rayonnement et responsabilités collectives scientifiques.': 'Rayonnement et responsabilités collectives scientifiques',
        'Autres responsabilités collectives.': 'Autres responsabilités collectives',
        'Principales communications scientifiques.': 'Principales communications scientifiques',
        'Financements.': 'Financements',
        'Autres publications ou productions scientifiques.': 'Autres publications ou productions scientifiques',
        'Compétences informatiques.': 'Compétences informatiques',
        'Logiciels documentaires et langages documentaires.': 'Logiciels documentaires et langages documentaires',
        'Langues.': 'Langues',
    }

    md_lines = []
    buffer = []
    entries = []

    def flush_entries_table():
        nonlocal entries
        if entries:
            md_lines.append("| Période | Détails |")
            md_lines.append("| --- | --- |")
            for date_text, details in entries:
                details = details.replace("|", "\\|")
                md_lines.append(f"| {date_text} | {details} |")
            md_lines.append('')
            entries = []

    def flush_paragraph():
        if buffer:
            paragraph = ' '.join(buffer).strip()
            if paragraph:
                md_lines.append(paragraph)
            buffer.clear()

    # Heuristiques de date
    months = r'(?:Janvier|Février|Mars|Avril|Mai|Juin|Juillet|Août|Septembre|Octobre|Novembre|Décembre|Janv|Fév|Fev|Mar|Avr|Juil|Aou|Août|Sept|Oct|Nov|Déc|Dec)'
    date_re_line = re.compile(
        rf'En\s+cours'
        rf'|Depuis\s+\d{{4}}'
        rf'|Depuis\s+{months}\s+\d{{4}}'
        rf'|depuis\s+{months}\s+\d{{4}}'
        rf'|courant\s+(19|20)\d{{2}}\s*(?:-|–|—|à)\s*(19|20)\d{{2}}'
        rf'|\b(19|20)\d{{2}}\s*(?:-|–|—|à)\s*(19|20)\d{{2}}\b'
        rf'|\d{{1,2}}\s+au\s+\d{{1,2}}\s+{months}\s+\d{{4}}'
        rf'|{months}\s+à\s+{months}\s+\d{{4}}'
        rf'|{months}\s+\d{{4}}\s+à\s+{months}\s+\d{{4}}'
        rf'|\d{{1,2}}\s+{months}\s+\d{{4}}'
        rf'|{months}\s+\d{{4}}'
        rf'|\b(19|20)\d{{2}}\b',
        re.IGNORECASE
    )
    date_re_inline = re.compile(
        rf'\d{{1,2}}\s+au\s+\d{{1,2}}\s+{months}\s+\d{{4}}'
        rf'|{months}\s+\d{{4}}\s+à\s+{months}\s+\d{{4}}'
        rf'|\d{{1,2}}\s+{months}\s+\d{{4}}'
        rf'|{months}\s+\d{{4}}',
        re.IGNORECASE
    )

    # Extraire l'en-tête (avant la première section)
    header_lines = []
    body_lines = []
    reached_sections = False
    for line in lines:
        text = line['text'].strip()
        if not reached_sections and text in section_titles:
            reached_sections = True
            body_lines.append(line)
            continue
        if not reached_sections:
            header_lines.append(text)
        else:
            body_lines.append(line)

    header_text = re.sub(r'\s+', ' ', ' '.join(header_lines)).strip()
    header_text_compact = re.sub(r'\s+', '', ' '.join(header_lines))
    email_match = re.search(r'[\w\.\-]+@[\w\-]+\.[\w\.]+', header_text)
    if not email_match:
        email_match = re.search(r'[\w\.\-]+@[\w\-]+\.[\w\.]+', header_text_compact)
    phone_match = re.search(r'(?:\+?\d[\d\s]{8,}\d)', header_text)
    postal_match = re.search(r'\b\d{5}\b', header_text)
    age_match = re.search(r'\b\d{2}\s*ans\b', header_text, re.IGNORECASE)
    name_match = re.findall(r'[A-ZÉÈÀÙÂÊÎÔÛÇ\-]{2,}(?:\s+[A-ZÉÈÀÙÂÊÎÔÛÇ\-]{2,})+', header_text)
    name = max(name_match, key=len) if name_match else 'Curriculum Vitae'

    md_lines.append(f"# {name}")
    md_lines.append('')

    # Construire une en-tête en colonnes (adresse / nom / contacts)
    cleaned_header_lines = []
    for hline in header_lines:
        line = hline.strip()
        if not line:
            continue
        if email_match:
            line = line.replace(email_match.group(0), '').strip()
        if name and name in line:
            line = line.replace(name, '').strip()
        if phone_match:
            line = line.replace(phone_match.group(0), '').strip()
            line = re.sub(r'\b(?:Tel|Tél|Téléphone)\s*:?\s*', '', line, flags=re.IGNORECASE).strip()
        if age_match:
            line = line.replace(age_match.group(0), '').strip()
        # Ne pas retirer le code postal de l'adresse (il sert à l'adresse)
        line = re.sub(r'\s{2,}', ' ', line).strip(' ,;-')
        if line:
            cleaned_header_lines.append(line)

    address_text = "<br>".join(cleaned_header_lines)
    contact_lines = []
    if email_match:
        contact_lines.append(f"Email : {email_match.group(0)}")
    if phone_match:
        contact_lines.append(f"Téléphone : {phone_match.group(0)}")
    # Le code postal reste dans l'adresse pour un en-tête plus fidèle
    if age_match:
        contact_lines.append(f"Âge : {age_match.group(0)}")
    contact_text = "<br>".join(contact_lines)

    if address_text or contact_text:
        md_lines.append("|  |  |")
        md_lines.append("| --- | --- |")
        md_lines.append(f"| {address_text} | {contact_text} |")
        md_lines.append('')

    current_date = None
    current_entry_lines = []

    def format_entry_text(text):
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def is_dangling_line(text):
        text = text.strip()
        if not text:
            return False
        # Conjonctions ou prépositions qui indiquent une continuation
        if re.search(r'(?:\b(et|ou|la|le|les|du|de|des|au|aux|à)\b)$', text, re.IGNORECASE):
            return True
        # Pas de ponctuation terminale
        if not re.search(r'[\.!?;:]\s*$', text):
            return True
        return False

    def flush_entry():
        nonlocal current_date, current_entry_lines
        if current_date:
            if current_entry_lines:
                entry_text = ' '.join(current_entry_lines).strip()
                entry_text = format_entry_text(entry_text)
                if entry_text:
                    if entries and entries[-1][0] == current_date:
                        merged = f"{entries[-1][1]} {entry_text}".strip()
                        entries[-1] = (current_date, merged)
                    else:
                        entries.append((current_date, entry_text))
            current_date = None
            current_entry_lines = []

    for line in body_lines:
        text = line['text'].strip()
        if not text or text == '.':
            continue

        # Section explicite
        if text in section_titles:
            flush_entry()
            flush_entries_table()
            flush_paragraph()
            md_lines.append(f"\n## {section_titles[text]}\n")
            continue

        # Titre principal implicite (mots clés)
        if text.lower().startswith('principales') or text.lower().startswith('autres'):
            flush_entry()
            flush_entries_table()
            flush_paragraph()
            md_lines.append(f"\n## {text.rstrip('.')}\n")
            continue

        # Compléter une période scindée sur la ligne suivante (ex: "2015" puis "-2018 ...")
        if current_date and not current_entry_lines:
            split_range_match = re.match(r'^-\s*((19|20)\d{2})\b\s*(.*)$', text)
            if split_range_match and re.match(r'^(19|20)\d{2}$', current_date):
                end_year = split_range_match.group(1)
                remainder = split_range_match.group(3).strip()
                current_date = f"{current_date}-{end_year}"
                if remainder:
                    current_entry_lines.append(remainder)
                continue

        # Date / période -> sous-titre
        date_match = date_re_line.match(text)
        if date_match:
            carryover = None
            if current_entry_lines and is_dangling_line(current_entry_lines[-1]):
                carryover = current_entry_lines.pop()
            flush_entry()
            flush_paragraph()
            date_text = date_match.group(0).strip()
            rest = text[len(date_text):].strip()
            # Normaliser les périodes du type "2015 -2018"
            range_inline = re.match(r'^(19|20)\d{2}\s*(?:-|–|—)\s*(19|20)\d{2}\b', date_text)
            if range_inline:
                date_text = re.sub(r'\s*(?:-|–|—)\s*', '-', date_text)
            # Si la période est suivie immédiatement d'un "-YYYY" séparé
            rest_range_match = re.match(r'^-\s*((19|20)\d{2})\b\s*(.*)$', rest)
            if rest_range_match:
                end_year = rest_range_match.group(1)
                date_text = f"{date_text}-{end_year}"
                rest = rest_range_match.group(3).strip()
            current_date = date_text
            if carryover:
                current_entry_lines.append(carryover)
            if rest:
                current_entry_lines.append(rest)
            continue

        # Sinon, accumuler dans l'entrée courante ou paragraphe
        if current_date:
            if current_entry_lines and current_entry_lines[-1].endswith('-'):
                current_entry_lines[-1] = current_entry_lines[-1][:-1] + text
            else:
                current_entry_lines.append(text)
        else:
            if buffer and buffer[-1].endswith('-'):
                buffer[-1] = buffer[-1][:-1] + text
            else:
                buffer.append(text)

    flush_entry()
    flush_entries_table()
    flush_paragraph()
    return '\n'.join(md_lines)

def save_markdown(md_text, md_path):
    os.makedirs(os.path.dirname(md_path), exist_ok=True)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_text)

def markdown_to_pdf(md_path, pdf_out):
    # Conversion avec police TTF compatible UTF-8
    os.makedirs(os.path.dirname(pdf_out), exist_ok=True)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    # Ajout d'une police TTF compatible UTF-8 (DejaVuSans)
    # Recherche d'une police DejaVu locale compatible
    font_candidates = [
        'DejaVuSans.ttf',
        'DejaVuSansCondensed.ttf',
        'DejaVuSansMono.ttf',
        'DejaVuSerif.ttf',
        'DejaVuSans-Oblique.ttf',
        'DejaVuSans-Bold.ttf',
        'DejaVuSerif-Bold.ttf',
        'DejaVuSerifCondensed.ttf',
        'DejaVuSans-ExtraLight.ttf',
        'DejaVuMathTeXGyre.ttf',
    ]
    font_path = None
    base_dir = os.path.dirname(__file__)
    fonts_dir = os.path.join(base_dir, 'fonts')
    cwd_fonts_dir = os.path.join(os.getcwd(), 'fonts')

    preferred_font = os.path.join(fonts_dir, 'DejaVuSans.ttf')
    if os.path.exists(preferred_font):
        cwd_font = os.path.join(os.getcwd(), 'DejaVuSans.ttf')
        if not os.path.exists(cwd_font):
            with open(preferred_font, 'rb') as src, open(cwd_font, 'wb') as dst:
                dst.write(src.read())
        font_path = cwd_font

    if not font_path:
        candidate_paths = []
        for candidate in font_candidates:
            candidate_paths.append(os.path.join(fonts_dir, candidate))
            candidate_paths.append(os.path.join(cwd_fonts_dir, candidate))
            candidate_paths.append(os.path.join(base_dir, candidate))

        for path in candidate_paths:
            if os.path.exists(path):
                font_path = path
                break

    if not font_path:
        for search_dir in [fonts_dir, cwd_fonts_dir, base_dir]:
            if os.path.isdir(search_dir):
                for fname in os.listdir(search_dir):
                    if fname.lower().endswith('.ttf') and 'dejavu' in fname.lower():
                        font_path = os.path.join(search_dir, fname)
                        break
            if font_path:
                break
    if not font_path:
        raise RuntimeError('Aucune police DejaVu compatible trouvée dans le dossier.')
    pdf.add_font('DejaVu', '', font_path, uni=True)
    pdf.set_font('DejaVu', '', 12)
    with open(md_path, 'r', encoding='utf-8') as f:
        for line in f:
            pdf.multi_cell(0, 10, line.strip())
    pdf.output(pdf_out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convertir un PDF en Markdown structuré et PDF.')
    parser.add_argument('--pdf_in', type=str, default=os.path.join('source', 'CV_GB_UNI_2020.pdf'), help='Fichier PDF source')
    parser.add_argument('--md_out', type=str, default=os.path.join('result', 'CV_GB_UNI_2020_structured.md'), help='Fichier Markdown de sortie')
    parser.add_argument('--pdf_out', type=str, default=os.path.join('result', 'CV_GB_UNI_2020_structured.pdf'), help='Fichier PDF de sortie')
    args = parser.parse_args()

    lines = extract_lines(args.pdf_in)
    md_text = detect_sections(lines)
    save_markdown(md_text, args.md_out)
    print(f'Markdown structuré sauvegardé dans {args.md_out}')
    try:
        markdown_to_pdf(args.md_out, args.pdf_out)
        print(f'PDF généré dans {args.pdf_out}')
    except Exception as e:
        print(f'Erreur lors de la génération du PDF : {e}')
