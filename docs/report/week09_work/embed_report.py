from pathlib import Path
import shutil,zipfile
from docx import Document
from docx.shared import Pt, RGBColor
from docx.oxml import OxmlElement,parse_xml
from docx.oxml.ns import qn
from docx.opc.part import Part
from docx.opc.packuri import PackURI
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.text.paragraph import Paragraph
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).parent
out=P.parent/'Group05_Week09_Report.docx'
backup=P/'report_before_embed.docx'
if not backup.exists():shutil.copy2(out,backup)
D=Document(backup)
font='/System/Library/Fonts/Supplemental/Times New Roman.ttf'
im=Image.new('RGB',(660,110),'white');dr=ImageDraw.Draw(im)
dr.rectangle((6,5,76,99),outline='black',width=2)
dr.text((13,38),'ZIP',fill='black',font=ImageFont.truetype(font,22))
dr.text((92,6),'MINH CHỨNG',fill='black',font=ImageFont.truetype(font,30))
dr.text((92,52),'Code, nhãn, log và ảnh',fill='black',font=ImageFont.truetype(font,27))
im.save(P/'evidence_object.png')
# Khung trinh phat: dang song ve tu chinh 000010011.WAV; chi la hinh hien thi cua doi tuong nhung.
import wave,numpy as np
with wave.open(str(P/'000010011.WAV')) as w:
 sr=w.getframerate();x=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)
im=Image.new('RGB',(1200,200),'white');dr=ImageDraw.Draw(im)
dr.rounded_rectangle((3,3,1196,196),radius=26,fill='#F2F2F2',outline='#7F7F7F',width=3)
dr.ellipse((28,40,148,160),fill='black')
dr.polygon([(72,68),(72,132),(124,100)],fill='white')
dr.text((176,18),'000010011.WAV  ·  “WE CALL IT BEAR”',fill='black',font=ImageFont.truetype(font,34))
bars=np.array_split(np.abs(x),150);peak=np.array([b.max() for b in bars]);peak=peak/peak.max()
for k,v in enumerate(peak):
 cx=180+k*6;hh=max(2,v*34);dr.rectangle((cx,100-hh,cx+3,100+hh),fill='#404040')
dr.line((180,152,1080,152),fill='#A6A6A6',width=6);dr.ellipse((172,144,188,160),fill='black')
dr.text((1094,82),f'{len(x)/sr:.2f} s'.replace('.',','),fill='black',font=ImageFont.truetype(font,30))
dr.text((1092,140),'Nháy đúp',fill='black',font=ImageFont.truetype(font,20))
im.save(P/'audio_object.png')
SIZE={'audio':(330,55),'evidence':(220,36.67)}

def style(p):
 p.paragraph_format.line_spacing=1.5;p.paragraph_format.space_after=Pt(4)
 for r in p.runs:
  r.font.name='Times New Roman';r.font.size=Pt(12);r.font.color.rgb=RGBColor(0,0,0)
 return p


# build_report.py dat san doan [[OBJECTS]] tai Phu luc; chen hai doi tuong nhung vao dung doan do.
objects=next(p for p in D.paragraphs if p.text=='[[OBJECTS]]')
for r in list(objects.runs):r._r.getparent().remove(r._r)
objects.paragraph_format.keep_with_next=True
for i,name in enumerate(['audio','evidence'],1):
 part=Part(PackURI(f'/word/embeddings/oleObject{i}.bin'),'application/vnd.openxmlformats-officedocument.oleObject',(P/f'{name}.bin').read_bytes(),D.part.package)
 rid=D.part.relate_to(part,RT.OLE_OBJECT)
 imageid,_=D.part.get_or_add_image(str(P/f'{name}_object.png'))
 xml=f'''<w:object xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" w:dxaOrig="{round(SIZE[name][0]*20)}" w:dyaOrig="{round(SIZE[name][1]*20)}">
 <v:shapetype id="_x0000_t75" coordsize="21600,21600" o:spt="75" o:preferrelative="t" path="m@4@5l@4@11@9@11@9@5xe" filled="f" stroked="f"><v:stroke joinstyle="miter"/><v:path o:extrusionok="f" gradientshapeok="t" o:connecttype="rect"/><o:lock v:ext="edit" aspectratio="t"/></v:shapetype>
 <v:shape id="_x0000_i{1100+i}" type="#_x0000_t75" style="width:{SIZE[name][0]}pt;height:{SIZE[name][1]}pt" o:ole=""><v:imagedata r:id="{imageid}" o:title="{name}"/></v:shape>
 <o:OLEObject Type="Embed" ProgID="Package" ShapeID="_x0000_i{1100+i}" DrawAspect="Icon" ObjectID="_{2100000000+i}" r:id="{rid}"/>
 </w:object>'''
 objects.add_run()._r.append(parse_xml(xml))
 if i==1:objects.add_run().add_break()
for p in D.paragraphs:p.paragraph_format.line_spacing=1.5
for root in (D.styles.element,D.element):
 for color in root.iter(qn('w:color')):color.attrib.clear();color.set(qn('w:val'),'000000')
D.save(out)
with zipfile.ZipFile(out) as z:
 for i,name in enumerate(['audio','evidence'],1):assert z.read(f'word/embeddings/oleObject{i}.bin')==(P/f'{name}.bin').read_bytes()
 assert z.testzip() is None
print(out, out.stat().st_size,'bytes; audio and evidence embedded')
