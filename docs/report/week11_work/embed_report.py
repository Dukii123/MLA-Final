from pathlib import Path
import zipfile, sys
from docx import Document
from docx.shared import RGBColor
from docx.oxml import parse_xml
from docx.oxml.ns import qn
from docx.opc.part import Part
from docx.opc.packuri import PackURI
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from PIL import Image, ImageDraw, ImageFont

# Nhúng gói ZIP minh chứng vào đoạn [[OBJECTS]] do build_report.py đặt sẵn ở Phụ lục.
P = Path(__file__).parent
out = Path(sys.argv[1]) if len(sys.argv) > 1 else P.parent / 'Group05_Week11_Report.docx'
D = Document(P / 'report_before_embed.docx')
_font = None
for c in ['C:/Windows/Fonts/times.ttf', '/System/Library/Fonts/Supplemental/Times New Roman.ttf']:
    if Path(c).exists():
        _font = c; break
im = Image.new('RGB', (660, 110), 'white'); dr = ImageDraw.Draw(im)
dr.rectangle((6, 5, 76, 99), outline='black', width=2)
dr.text((13, 38), 'ZIP', fill='black', font=ImageFont.truetype(_font, 22))
dr.text((92, 6), 'MINH CHỨNG TUẦN 11', fill='black', font=ImageFont.truetype(_font, 30))
dr.text((92, 52), 'Code, kết quả, log và ảnh', fill='black', font=ImageFont.truetype(_font, 27))
im.save(P / 'evidence_object.png')
objects = next(p for p in D.paragraphs if p.text == '[[OBJECTS]]')
for r in list(objects.runs):
    r._r.getparent().remove(r._r)
part = Part(PackURI('/word/embeddings/oleObject1.bin'), 'application/vnd.openxmlformats-officedocument.oleObject', (P / 'evidence.bin').read_bytes(), D.part.package)
rid = D.part.relate_to(part, RT.OLE_OBJECT)
imageid, _ = D.part.get_or_add_image(str(P / 'evidence_object.png'))
objects.add_run()._r.append(parse_xml(f'''<w:object xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" w:dxaOrig="4400" w:dyaOrig="733">
 <v:shapetype id="_x0000_t75" coordsize="21600,21600" o:spt="75" o:preferrelative="t" path="m@4@5l@4@11@9@11@9@5xe" filled="f" stroked="f"><v:stroke joinstyle="miter"/><v:path o:extrusionok="f" gradientshapeok="t" o:connecttype="rect"/><o:lock v:ext="edit" aspectratio="t"/></v:shapetype>
 <v:shape id="_x0000_i1101" type="#_x0000_t75" style="width:220pt;height:36.67pt" o:ole=""><v:imagedata r:id="{imageid}" o:title="evidence"/></v:shape>
 <o:OLEObject Type="Embed" ProgID="Package" ShapeID="_x0000_i1101" DrawAspect="Icon" ObjectID="_2100000001" r:id="{rid}"/>
</w:object>'''))
for p in D.paragraphs:
    p.paragraph_format.line_spacing = 1.5
for root in (D.styles.element, D.element):
    for color in root.iter(qn('w:color')):
        color.attrib.clear(); color.set(qn('w:val'), '000000')
D.save(out)
with zipfile.ZipFile(out) as z:
    assert z.read('word/embeddings/oleObject1.bin') == (P / 'evidence.bin').read_bytes() and z.testzip() is None
print(out, out.stat().st_size, 'bytes; evidence ZIP embedded')
