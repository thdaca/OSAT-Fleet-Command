"""Render the maintained guide; --package includes it at the release ZIP root.

This is documentation tooling, never imported by the application. It invokes
the unchanged release builder, then adds the root PDF and verifies the result.
"""
from pathlib import Path
import json
import re
import argparse
import ast
import hashlib
import importlib.util
import zipfile
from xml.sax.saxutils import escape

import reportlab
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    BaseDocTemplate, Flowable, Frame, NextPageTemplate, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle, KeepTogether,
)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parents[1]
arguments = argparse.ArgumentParser(description=__doc__)
arguments.add_argument('--package', action='store_true', help='Update the current-version ZIP with the root-level guide; existing same-version application bytes must match.')
args = arguments.parse_args()
SPEC = json.loads((ROOT / 'docs/ARCHITECTURE_PDF_STYLE.json').read_bytes())
OUT = ROOT / '.artifacts/output/pdf' / SPEC['output_name']
OUT.parent.mkdir(parents=True, exist_ok=True)
fonts = Path(reportlab.__file__).parent / 'fonts'
for name, file in [('Guide', 'Vera.ttf'), ('Guide-Bold', 'VeraBd.ttf'), ('Guide-Italic', 'VeraIt.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(fonts / file)))
pdfmetrics.registerFontFamily('Guide', normal='Guide', bold='Guide-Bold', italic='Guide-Italic', boldItalic='Guide-Bold')
C = {name: colors.HexColor(value) for name, value in SPEC['colors'].items()}
W, H = letter
M = SPEC['margins_points']
BODY_W = W - 2 * M

styles = {
    'body': ParagraphStyle('Body', fontName='Guide', fontSize=SPEC['body_font_points'], leading=SPEC['body_leading_points'], textColor=C['ink'], spaceAfter=8),
    'heading': ParagraphStyle('Section', fontName='Guide-Bold', fontSize=SPEC['heading_font_points'], leading=27.5, textColor=C['navy'], spaceAfter=15),
    'sub': ParagraphStyle('Subheading', fontName='Guide-Bold', fontSize=SPEC['subheading_font_points'], leading=16.0, textColor=C['navy'], spaceBefore=9, spaceAfter=6, keepWithNext=True),
    'smallsub': ParagraphStyle('SmallSubheading', fontName='Guide-Bold', fontSize=10.9, leading=14.7, textColor=C['navy'], spaceBefore=8, spaceAfter=5, keepWithNext=True),
    'kicker': ParagraphStyle('Kicker', fontName='Guide-Bold', fontSize=10, leading=14, textColor=C['teal'], spaceAfter=6, keepWithNext=True),
    'bullet': ParagraphStyle('Bullet', fontName='Guide', fontSize=10.5, leading=14.6, textColor=C['ink'], leftIndent=14, bulletIndent=0, spaceAfter=5),
    'cell': ParagraphStyle('Cell', fontName='Guide', fontSize=9.4, leading=12.4, textColor=C['ink']),
    'cellhead': ParagraphStyle('CellHead', fontName='Guide-Bold', fontSize=9.4, leading=12.4, textColor=C['paper']),
    'quote': ParagraphStyle('Quote', fontName='Guide', fontSize=10.3, leading=14.2, textColor=C['navy']),
    'code': ParagraphStyle('Code', fontName='Courier-Bold', fontSize=9.0, leading=12.8, textColor=C['ink']),
    'toc': ParagraphStyle('TOC', fontName='Guide', fontSize=10.1, leading=16.8, textColor=C['ink'], spaceBefore=3.3, leftIndent=0, rightIndent=24, firstLineIndent=0),
}


def inline(text):
    parts = re.split(r'(`[^`]+`)', text)
    formatted = []
    for part in parts:
        if part.startswith('`') and part.endswith('`'):
            formatted.append('<font name="Courier-Bold" size="9.0">' + escape(part[1:-1]) + '</font>')
        else:
            formatted.append(re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', escape(part)))
    return ''.join(formatted)


class Diagram(Flowable):
    def __init__(self, rows, overview=False):
        Flowable.__init__(self)
        self.rows = rows
        self.overview = overview
        self.width = BODY_W
        self.height = 122 if overview else len(rows) * 36

    def draw(self):
        canvas = self.canv
        if self.overview:
            gap = 14
            width = (self.width - gap * 2) / 3
            for i, (label, description) in enumerate(self.rows):
                x = i * (width + gap)
                canvas.setFillColor(C['teal'] if i == 1 else C['navy'])
                canvas.roundRect(x, 8, width, 106, 5, fill=1, stroke=0)
                title = Paragraph(escape(label), ParagraphStyle('CardTitle', fontName='Guide-Bold', fontSize=12.1, leading=16, textColor=C['paper']))
                tw, th = title.wrap(width - 22, 40)
                title.drawOn(canvas, x + 11, 94 - th)
                p = Paragraph(escape(description), ParagraphStyle('CardBody', fontName='Guide', fontSize=10.0, leading=13.5, textColor=C['paper']))
                pw, ph = p.wrap(width - 22, 75)
                p.drawOn(canvas, x + 11, 73 - ph)
                if i < 2:
                    canvas.setStrokeColor(C['navy'])
                    canvas.setFillColor(C['navy'])
                    canvas.line(x + width + 2, 61, x + width + gap - 3, 61)
                    arrow = canvas.beginPath()
                    arrow.moveTo(x + width + gap - 2, 61)
                    arrow.lineTo(x + width + gap - 6, 64)
                    arrow.lineTo(x + width + gap - 6, 58)
                    arrow.close()
                    canvas.drawPath(arrow, fill=1, stroke=0)
        else:
            for i, (number, title, description) in enumerate(self.rows):
                y = self.height - i * 36 - 15
                if i < len(self.rows) - 1:
                    canvas.setStrokeColor(C['line'])
                    canvas.line(13, y - 13, 13, y - 30)
                canvas.setFillColor(C['navy'])
                canvas.circle(13, y, 12, fill=1, stroke=0)
                canvas.setFillColor(C['paper'])
                canvas.setFont('Guide-Bold', 8.7)
                canvas.drawCentredString(13, y - 3.1, number)
                p = Paragraph('<b>' + escape(title) + '</b><br/>' + escape(description), ParagraphStyle('Sequence', fontName='Guide', fontSize=10.0, leading=13.4, textColor=C['ink']))
                pw, ph = p.wrap(self.width - 40, 42)
                p.drawOn(canvas, 36, y + 11 - ph)


def cover(canvas, doc):
    canvas.setFillColor(C['navy'])
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    canvas.setFillColor(C['paper'])
    canvas.setFont('Guide-Bold', 10)
    canvas.drawString(M, 744, 'OSAT STUDENT ENGINEERING')
    canvas.setFillColor(C['teal'])
    canvas.roundRect(M, 688, 276, 27, 3, fill=1, stroke=0)
    canvas.setFillColor(C['paper'])
    canvas.setFont('Guide-Bold', 9.4)
    canvas.drawString(M + 12, 697, 'CONTROLLED END-TO-END PROOF OF CONCEPT')
    canvas.setFont('Guide-Bold', 40)
    canvas.drawString(M, 622, SPEC['title'])
    canvas.setFont('Guide', 23)
    canvas.drawString(M, 578, SPEC['subtitle'])
    canvas.setFont('Guide-Bold', 48)
    canvas.drawString(M, 496, SPEC['software_version'])
    canvas.setFont('Guide', 14)
    canvas.drawString(M, 461, 'A plain-English guide for student engineers')
    canvas.setFont('Guide', 11.5)
    canvas.drawString(M, 438, 'Current architecture + cumulative changelog from 0.2.6')
    canvas.setStrokeColor(C['paper'])
    canvas.setLineWidth(0.7)
    canvas.line(M, 411, W - M, 411)
    canvas.setFillColor(C['paper'])
    canvas.roundRect(M, 220, BODY_W, 150, 5, fill=1, stroke=0)
    canvas.setFillColor(C['teal'])
    canvas.setFont('Guide-Bold', 10)
    canvas.drawString(M + 18, 346, 'FROZEN ' + SPEC['software_version'] + ' APPLICATION CODE')
    p = Paragraph('Understand the full system, find your team\'s boundary, and follow measurements into evidence.<br/><br/>The demonstration is synthetic. Real OSAT validation, prospective plant validation and production qualification remain false.', ParagraphStyle('CoverText', fontName='Guide', fontSize=11.2, leading=16, textColor=C['ink']))
    pw, ph = p.wrap(BODY_W - 36, 95)
    p.drawOn(canvas, M + 18, 324 - ph)
    for i, (title, subtitle) in enumerate([('PRE-STEPS', 'Identity & trust'), ('STEPS', 'Analysis & maintenance'), ('POST-STEPS', 'Proof & research')]):
        x = M + i * (BODY_W / 3)
        canvas.setFillColor(C['paper'])
        canvas.setFont('Guide-Bold', 12)
        canvas.drawString(x, 170, title)
        canvas.setFont('Guide', 9.5)
        canvas.drawString(x, 149, subtitle)
    canvas.setFont('Guide', 9)
    canvas.drawString(M, 54, 'Documentation edition ' + SPEC['document_edition'] + ' | Reviewed ' + SPEC['reviewed_on'])
    canvas.drawRightString(W - M, 54, 'OSAT SemiGuard')


def header_footer(canvas, doc):
    canvas.setFillColor(C['navy'])
    canvas.setFont('Guide-Bold', 8.4)
    canvas.drawString(M, H - 32, 'OSAT SEMIGUARD  /  ' + SPEC['software_version'])
    canvas.setFont('Guide', 8)
    canvas.drawRightString(W - M, H - 32, 'ARCHITECTURE & VERSION HISTORY')
    canvas.setStrokeColor(C['line'])
    canvas.setLineWidth(0.55)
    canvas.line(M, H - 42, W - M, H - 42)
    canvas.line(M, 43, W - M, 43)
    canvas.setFillColor(C['ink'])
    canvas.setFont('Guide', SPEC['footer_font_points'])
    canvas.drawString(M, 28, 'CONTROLLED POC  /  CODE FROZEN')
    canvas.drawRightString(W - M, 28, f'PAGE {doc.page}')


class GuideDoc(BaseDocTemplate):
    def beforeDocument(self):
        self.section_pages = {}
        self.stage_pages = {}

    def afterFlowable(self, flowable):
        if hasattr(flowable, 'section'):
            sid, title = flowable.section
            self.section_pages[sid] = self.page
            self.canv.bookmarkPage(sid)
            label = chapter_numbers[sid] + '  ' + title
            self.canv.addOutlineEntry(label, sid, 0, False)
            self.notify('TOCEntry', (0, label, self.page, sid))
        elif hasattr(flowable, 'stage'):
            sid, stage, title = flowable.stage
            key = sid + '.' + stage
            self.stage_pages[stage] = self.page
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(stage + '  ' + title, key, 1, False)


source = (ROOT / 'docs/ARCHITECTURE_GUIDE.md').read_text(encoding='utf-8') + '\n' + (ROOT / 'docs/CHANGELOG.md').read_text(encoding='utf-8')
section_ids = re.findall(r'^# (S\d+) \| ', source, flags=re.M)
if len(section_ids) != len(set(section_ids)):
    raise ValueError('Guide section IDs must be unique')
chapter_numbers = {sid: f'{number:02d}' for number, sid in enumerate(section_ids, start=1)}


doc = GuideDoc(str(OUT), pagesize=letter, title=SPEC['title'] + ' ' + SPEC['software_version'] + ' - ' + SPEC['subtitle'], author='OSAT SemiGuard student engineering project', subject='Plain-English current architecture and cumulative version history', leftMargin=M, rightMargin=M, topMargin=66, bottomMargin=55, pageCompression=1)
frame = Frame(M, 55, BODY_W, H - 121, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
doc.addPageTemplates([PageTemplate(id='Cover', frames=[frame], onPage=cover), PageTemplate(id='Body', frames=[frame], onPage=header_footer)])
story = [Spacer(1, 590), NextPageTemplate('Body'), PageBreak()]
story.append(Paragraph('CONTENTS', styles['kicker']))
story.append(Paragraph('Find your route', styles['heading']))
story.append(Paragraph('Read from the top for a full introduction, or use the clickable contents and PDF bookmarks to jump to one responsibility.', styles['body']))
toc = TableOfContents()
toc.levelStyles = [styles['toc']]
toc.dotsMinLevel = 0
toc.tableStyle = TableStyle([('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0), ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0)])
story.extend([toc, Spacer(1, 18)])
story.append(Paragraph('A useful first pass', styles['sub']))
for line in [
    f'New to the system: chapters {chapter_numbers["S01"]}-{chapter_numbers["S03"]}, then execution in {chapter_numbers["S21"]}-{chapter_numbers["S09"]}.',
    f'Working on a contribution: your team in {chapter_numbers["S16"]}-{chapter_numbers["S17"]}, then its stage and tests.',
    f'Reviewing a version: chapters {chapter_numbers["S15"]}, {chapter_numbers["S18"]} and the changelog in {chapter_numbers["S20"]}.',
]:
    story.append(Paragraph(inline(line), styles['bullet'], bulletText='-'))

lines = source.splitlines()
i = 0
section_id = None
section_title = None
stage_headings = set()
while i < len(lines):
    line = lines[i].strip()
    i += 1
    if not line or line.startswith('<!--'):
        continue
    if line.startswith('# '):
        section_id, title = line[2:].split(' | ', 1)
        section_title = title
        while story and isinstance(story[-1], Spacer):
            story.pop()
        story.append(PageBreak())
        story.append(Paragraph('CHAPTER ' + chapter_numbers[section_id] + '  /  ' + ('VERSION HISTORY' if section_id == 'S20' else 'CURRENT ARCHITECTURE'), styles['kicker']))
        heading = Paragraph(escape(title), styles['heading'])
        heading.section = (section_id, title)
        story.append(heading)
    elif line.startswith('### '):
        story.append(Paragraph(inline(line[4:]), styles['smallsub']))
    elif line.startswith('## '):
        heading = Paragraph(inline(line[3:]), styles['sub'])
        stage_match = re.fullmatch(r'((?:PRE|STEP|POST)\d+[ab]?) - (.+)', line[3:])
        if stage_match:
            stage, stage_title = stage_match.groups()
            # A continued explanation belongs to the original stage bookmark.
            if stage not in stage_headings:
                heading.stage = (section_id, stage, stage_title)
                stage_headings.add(stage)
        story.append(heading)
    elif line == '::: pagebreak':
        while story and isinstance(story[-1], Spacer):
            story.pop()
        story.append(PageBreak())
        story.append(Paragraph('CHAPTER ' + chapter_numbers[section_id] + '  /  CURRENT ARCHITECTURE  /  CONTINUED', styles['kicker']))
        story.append(Paragraph(escape(section_title), styles['heading']))
    elif line.startswith('::: '):
        kind = line[4:]
        rows = []
        while i < len(lines) and lines[i].strip() != ':::':
            rows.append(tuple(part.strip() for part in lines[i].split('|')))
            i += 1
        i += 1
        story.extend([Diagram(rows, kind == 'overview'), Spacer(1, 8)])
    elif line.startswith('|'):
        rows = [[part.strip() for part in line.strip('|').split('|')]]
        while i < len(lines) and lines[i].strip().startswith('|'):
            rows.append([part.strip() for part in lines[i].strip().strip('|').split('|')])
            i += 1
        widths = {'S03': [136, 166, BODY_W - 302], 'S04': [56, 157, BODY_W - 213], 'S10': [115, 120, BODY_W - 235], 'S12': [94, BODY_W - 94], 'S19': [130, BODY_W - 130]}[section_id]
        cells = [[Paragraph(inline(value), styles['cellhead'] if index == 0 else styles['cell']) for value in row] for index, row in enumerate(rows)]
        table = Table(cells, colWidths=widths, repeatRows=1, hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), C['navy']),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [C['paper'], C['pale']]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LINEBELOW', (0, 0), (-1, 0), 0.6, C['navy']),
            ('LINEBELOW', (0, 1), (-1, -1), 0.35, C['line']),
        ]))
        story.extend([table, Spacer(1, 11)])
    elif line.startswith('```'):
        code = []
        while i < len(lines) and not lines[i].strip().startswith('```'):
            code.append(escape(lines[i]))
            i += 1
        i += 1
        p = Paragraph('<br/>'.join(code), styles['code'])
        box = Table([[p]], colWidths=[BODY_W])
        box.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), C['pale']), ('LEFTPADDING', (0, 0), (-1, -1), 10), ('RIGHTPADDING', (0, 0), (-1, -1), 10), ('TOPPADDING', (0, 0), (-1, -1), 9), ('BOTTOMPADDING', (0, 0), (-1, -1), 9)]))
        story.extend([box, Spacer(1, 8)])
    elif line.startswith('> '):
        p = Paragraph(inline(line[2:]), styles['quote'])
        box = Table([[p]], colWidths=[BODY_W])
        box.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), C['pale']), ('LINEBEFORE', (0, 0), (0, -1), 3, C['teal']), ('LEFTPADDING', (0, 0), (-1, -1), 12), ('RIGHTPADDING', (0, 0), (-1, -1), 12), ('TOPPADDING', (0, 0), (-1, -1), 9), ('BOTTOMPADDING', (0, 0), (-1, -1), 9)]))
        story.extend([box, Spacer(1, 10)])
    elif line.startswith('- '):
        story.append(Paragraph(inline(line[2:]), styles['bullet'], bulletText='-'))
    elif re.match(r'\d+\. ', line):
        number, text = line.split('. ', 1)
        story.append(Paragraph(inline(text), styles['bullet'], bulletText=number + '.'))
    else:
        story.append(Paragraph(inline(line), styles['body']))

def invariant_canvas(*args, **kwargs):
    kwargs['invariant'] = 1
    return Canvas(*args, **kwargs)


doc.multiBuild(story, canvasmaker=invariant_canvas)
summary = {'output': str(OUT), 'section_start_pages': doc.section_pages, 'stage_start_pages': doc.stage_pages, 'reader_chapters': chapter_numbers, 'page_count': doc.page, 'bytes': OUT.stat().st_size}
(ROOT / '.artifacts/pdf-layout.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, indent=2))

if args.package:
    code_tree = ast.parse((ROOT / 'osat_edge/roadmap/pre_steps/pre01_common/contracts.py').read_text(encoding='utf-8'))
    code_version = next(ast.literal_eval(node.value) for node in code_tree.body
                        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'VERSION' for target in node.targets))
    if code_version != SPEC['software_version']:
        raise ValueError('PDF metadata version must match the application VERSION before packaging')

    builder_path = ROOT / 'osat_edge/roadmap/pre_steps/pre01_common/resources/build_release.py'
    module_spec = importlib.util.spec_from_file_location('documentation_release_builder', builder_path)
    builder = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(builder)
    destination = ROOT.parent / 'snapshots' / (code_version + '.zip')
    files = builder.release_files(ROOT)
    application = {builder.archive_member_name(ROOT, path): path.read_bytes()
                   for path in files if path.is_relative_to(ROOT / 'osat_edge') or path == ROOT / 'requirements.txt'}
    if destination.exists():
        with zipfile.ZipFile(destination) as old:
            prior_names = {name for name in old.namelist() if name.startswith(ROOT.name + '/osat_edge/') or name == ROOT.name + '/requirements.txt'}
            if prior_names != set(application) or any(old.read(name) != content for name, content in application.items()):
                raise ValueError('Existing released application bytes changed; assign a new software version rather than overwriting a frozen release')

    staging = ROOT / '.artifacts/releases' / (code_version + '-with-guide.zip')
    builder.build_release_archive(ROOT, staging)
    member = ROOT.name + '/' + SPEC['output_name']
    with zipfile.ZipFile(staging, 'a', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        if member in archive.namelist():
            raise ValueError('Duplicate root architecture PDF')
        archive.write(OUT, member)
    names = builder.validate_release_archive(staging, ROOT.name)
    with zipfile.ZipFile(staging) as archive:
        expected = {builder.archive_member_name(ROOT, path): path.read_bytes() for path in files}
        expected[member] = OUT.read_bytes()
        if set(names) != set(expected) or any(archive.read(name) != content for name, content in expected.items()):
            raise ValueError('Release file set or content does not match the maintained sources and PDF')
    destination.parent.mkdir(exist_ok=True)
    staging.replace(destination)
    print(json.dumps({'archive': str(destination), 'members': len(names), 'pdf_member': member,
                      'sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
                      'existing_application_bytes_preserved': True}, indent=2))
