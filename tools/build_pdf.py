from pathlib import Path
import re,sys,json,math,hashlib

from lxml import html,etree
from reportlab.pdfgen import canvas
from reportlab import rl_config

from reportlab.platypus import BaseDocTemplate,PageTemplate,Frame,Paragraph,Spacer,PageBreak,NextPageTemplate,Table,TableStyle,Flowable,KeepTogether,CondPageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT,TA_JUSTIFY,TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.units import mm
from pypdf import PdfReader,PdfWriter
from pypdf.generic import RectangleObject,NameObject,TextStringObject
import html as htm
W=Path(__file__).resolve().parents[1];VERSION='v1.0.0';OUT=W/'dist';OUT.mkdir(parents=True,exist_ok=True)
BOOK=W/'book';BOOK.mkdir(parents=True,exist_ok=True)
for n,p in [('Serif','DejaVuSerif.ttf'),('SerifBold','DejaVuSerif-Bold.ttf'),('Sans','DejaVuSans.ttf'),('SansBold','DejaVuSans-Bold.ttf'),('Mono','DejaVuSansMono.ttf'),('MonoBold','DejaVuSansMono-Bold.ttf')]:pdfmetrics.registerFont(TTFont(n,str(W/'assets/fonts'/p)))
pdfmetrics.registerFontFamily('Serif',normal='Serif',bold='SerifBold',italic='Serif',boldItalic='SerifBold');pdfmetrics.registerFontFamily('Sans',normal='Sans',bold='SansBold',italic='Sans',boldItalic='SansBold');pdfmetrics.registerFontFamily('Mono',normal='Mono',bold='MonoBold',italic='Mono',boldItalic='MonoBold')
for n,f in [('SerifItalic','DejaVuSerif-Italic.ttf'),('SerifBoldItalic','DejaVuSerif-BoldItalic.ttf')]:pdfmetrics.registerFont(TTFont(n,str(W/'assets/fonts'/f)))
pdfmetrics.registerFontFamily('Serif',normal='Serif',bold='SerifBold',italic='SerifItalic',boldItalic='SerifBoldItalic')
rl_config.canvas_basefontname="Sans"
BLEED=0*mm;TW=148*mm;TH=210*mm;MW=TW+2*BLEED;MH=TH+2*BLEED;IW=113*mm
black=colors.CMYKColor(0,0,0,1);gray=colors.CMYKColor(0,0,0,.58);light=colors.CMYKColor(0,0,0,.10)
styles={}
def sty(n,**kw):styles[n]=ParagraphStyle(n,**kw);return styles[n]
body=sty('body',fontName='Serif',fontSize=10.2,leading=13.6,spaceAfter=4.2,textColor=black,alignment=TA_JUSTIFY,allowWidows=0,allowOrphans=0,hyphenationLang='en_US',splitLongWords=0)
sty('small',parent=body,fontSize=8.4,leading=11.2,alignment=TA_LEFT,spaceAfter=4)
sty('url',parent=styles['small'],fontName='Sans',fontSize=7.9,leading=10,spaceAfter=2,wordWrap='CJK',splitLongWords=1,hyphenationLang=None)
sty('list',parent=body,leftIndent=12,firstLineIndent=-12)
sty('h1',fontName='SansBold',fontSize=18.5,leading=23,spaceAfter=17,textColor=black,keepWithNext=True)
sty('h2',fontName='SansBold',fontSize=11.5,leading=15.1,spaceBefore=10,spaceAfter=5,textColor=black,keepWithNext=False)
sty('h3',fontName='SansBold',fontSize=10.2,leading=13,spaceBefore=10,spaceAfter=5,textColor=black,keepWithNext=False)
sty('table',fontName='Serif',fontSize=8.7,leading=11.7,spaceAfter=0,textColor=black,allowWidows=0,allowOrphans=0,hyphenationLang='en_US',splitLongWords=0)
sty('thead',parent=styles['table'],fontName='SansBold',fontSize=8.1,leading=10.6)
sty('quote',fontName='Mono',fontSize=9.0,leading=13,spaceBefore=3,spaceAfter=9,leftIndent=9,rightIndent=3,borderColor=gray,borderWidth=.7,borderPadding=(5,7,5,7),textColor=black,allowWidows=0,allowOrphans=0,splitLongWords=0)
sty('label',fontName='SansBold',fontSize=8,leading=11,spaceAfter=9,textColor=gray,tracking=1,keepWithNext=True)
sty('toc',fontName='Sans',fontSize=9.1,leading=12.6,spaceAfter=0,textColor=black)
sty('tocpage',parent=styles['toc'],alignment=2)
sty('cardbody',parent=body,fontSize=9.8,leading=13.0,spaceAfter=3)
sty('cardh1',parent=styles['h1'],fontSize=17,leading=21,spaceAfter=10)
sty('cardh2',parent=styles['h2'],fontSize=10.4,leading=12.5,spaceBefore=7,spaceAfter=3)
sty('cardquote',parent=styles['quote'],fontSize=8.7,leading=11.4,spaceAfter=5,borderPadding=(3,6,3,6))
root=html.parse(str(W/'source/guide.html'));bodyel=root.xpath('//body')[0];blocks=[];start=False
for el in bodyel:
 if el.tag=='h1' and 'How to use' in el.text_content():start=True
 if start:blocks.append(el)
# Stable external references survive printed pages; internal references get page numbers.
urls=[]
for el in blocks:
 for a in el.xpath('.//a[@href]'):
  u=a.get('href')
  if not u.startswith('#') and u not in urls:urls.append(u)
anchor_pages={};heads=[];headlabels={}
for el in blocks:
 if el.tag=='h1':
  aid=el.get('id');title=' '.join(el.text_content().split());heads.append((aid,title));headlabels[aid]=title

def escape(s):return htm.escape(s or '',quote=False)
def markup(e,pagemap,table=False):
 out=escape(e.text)
 for ch in e:
  t=ch.tag;inner=markup(ch,pagemap,table)
  if t=='strong':v='<b>'+inner+'</b>'
  elif t=='em':v='<i>'+inner+'</i>'
  elif t=='code':v='<font name="Mono">'+inner+'</font>'
  elif t=='br':v='<br/>'
  elif t=='a':
   u=ch.get('href','')
   if u.startswith('#'):
    aid=u[1:];page=pagemap.get(aid)
    v=f'<link href="#{htm.escape(aid,quote=True)}">{inner} (p. {page})</link>' if page else inner
   else:v=inner+f'<super>[{urls.index(u)+1}]</super>' if u in urls else inner
  else:v=inner
  out+=v+escape(ch.tail)
 return out

class ChapterBreak(Flowable):pass
class FinalPad(Flowable):pass
class Invisible(Flowable):
 def wrap(self,aW,aH):return 1,1
 def draw(self):pass
class BookDoc(BaseDocTemplate):
 def __init__(self,path):
  super().__init__(str(path),pagesize=(MW,MH),leftMargin=0,rightMargin=0,topMargin=0,bottomMargin=0,title='CW: A Practical Community Guide',author='Valeriy Bagrintsev',allowSplitting=True,pageCompression=1)
  self.blank_pages=set();self.open_pages=set();self.page_map={};self.entries=[];self.running='CW: A Practical Community Guide';self.art_pages={};self.layouts=[]
  for name,left in [('Right',20),('Left',15)]:
   frame=Frame(BLEED+left*mm,BLEED+20*mm,IW,170*mm,id=name,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
   self.addPageTemplates(PageTemplate(id=name,frames=[frame],onPage=self.start,onPageEnd=self.end,autoNextPageTemplate='Left' if name=='Right' else 'Right'))
 def _setPageTemplate(self):
  self.pageTemplate=self.pageTemplates[self.page%2]
 def filterFlowables(self,flowables):
  if not flowables:return
  if isinstance(flowables[0],ChapterBreak):
   flowables[0:1]=[PageBreak()]
  elif isinstance(flowables[0],FinalPad):
   if self.page%2==0:
    self.blank_pages.add(self.page+1);flowables[0:1]=[PageBreak(),Invisible(),PageBreak()]
   else:flowables[0:1]=[PageBreak()]
 def start(self,c,d):
  c.setFillColor(black);c.setStrokeColor(black)
  # Make the trim and bleed specification explicit in every PDF page dictionary.
  c.setTrimBox((BLEED,BLEED,BLEED+TW,BLEED+TH));c.setBleedBox((0,0,MW,MH))
 def end(self,c,d):
  p=d.page
  if p<=2 or p in d.blank_pages or p in d.art_pages:return
  c.saveState();left=BLEED+(20 if p%2 else 15)*mm;right=left+IW
  if p not in d.open_pages:
   c.setFont('Sans',7.1);c.setFillColor(gray)
   label='CW • A PRACTICAL COMMUNITY GUIDE' if p%2==0 else re.sub(r'^\d+\.\s*','',d.running).upper()
   while pdfmetrics.stringWidth(label,'Sans',7.1)>IW:label=label[:-2]+'…'
   c.drawString(left,BLEED+TH-13.1*mm,label)
  c.setFillColor(black);c.setFont('Sans',8.5)
  if p%2:c.drawRightString(BLEED+TW-15*mm,BLEED+11*mm,str(p))
  else:c.drawString(BLEED+15*mm,BLEED+11*mm,str(p))
  c.restoreState()
 def afterFlowable(self,f):
  if hasattr(f,'_anchor'):
   a=f._anchor;self.page_map[a]=self.page;self.canv.bookmarkPage(a)
   if getattr(f,'_level',None)==1:
    self.open_pages.add(self.page);self.entries.append((a,f._title,self.page));self.running=f._title
    self.canv.addOutlineEntry(f._title,a,0,False)

def paragraph(txt,styname='body',anchor=None,level=None,title=None):
 p=Paragraph(txt,styles[styname])
 if anchor:p._anchor=anchor;p._level=level;p._title=title
 return p

def tableflow(el,pm):
 trs=el.xpath('.//tr');data=[]
 for i,tr in enumerate(trs):
  data.append([Paragraph(markup(td,pm,True),styles['thead' if i==0 else 'table']) for td in tr])
 raw=[[td.text_content().strip() for td in tr] for tr in trs]
 n=len(data[0]);widths=None
 # Compact alphabet and number reference fits a single A5 page per principal table.
 if n==2 and raw[0][0] in ['Letter','Number'] and len(raw)>8:
  rr=raw[1:];mid=math.ceil(len(rr)/2);new=[['Digit' if raw[0][0]=='Number' else raw[0][0],'Pattern','Digit' if raw[0][0]=='Number' else raw[0][0],'Pattern']]
  for i in range(mid):new.append(rr[i]+(rr[i+mid] if i+mid<len(rr) else ['','']))
  data=[[Paragraph(escape(x) if j%2==0 else '<font name="Mono">'+escape(x)+'</font>',styles['thead' if i==0 else 'table']) for j,x in enumerate(r)] for i,r in enumerate(new)]
  widths=[15*mm,41.5*mm,15*mm,41.5*mm];n=4
 if widths is None:
  if n==2:
   h=raw[0]
   if h[0] in ['Group','Code','Signal','Mark','Form','Field','R','S','T','Word']:widths=[27*mm,86*mm]
   elif h[0] in ['Send']:widths=[61*mm,52*mm]
   else:widths=[45*mm,68*mm]
  elif n==3:
   h=raw[0]
   if h[0] in ['Signal','Mark']:widths=[17*mm,27*mm,69*mm]
   else:widths=[24*mm,44*mm,45*mm]
  else:widths=[IW/n]*n
 t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT',spaceBefore=5,spaceAfter=10,splitByRow=1)
 t.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),'Sans'),('TEXTCOLOR',(0,0),(-1,-1),black),('BACKGROUND',(0,0),(-1,0),light),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),('LINEBELOW',(0,0),(-1,0),.6,black),('LINEBELOW',(0,1),(-1,-1),.25,gray)]))
 return t


def draw_art(c,kind):
 navy=colors.CMYKColor(.68,.35,.20,.82);amber=colors.CMYKColor(0,.26,.65,.02);cream=colors.CMYKColor(.02,.03,.10,0);muted=colors.CMYKColor(.16,.05,.08,.12)
 c.setFillColor(navy);c.rect(0,0,TW,TH,fill=1,stroke=0)
 x=16*mm;right=TW-16*mm
 def line(y,text,font='Sans',size=10,color=cream):c.setFont(font,size);c.setFillColor(color);c.drawString(x,y,text)
 if kind=='front':
  line(TH-21*mm,'MORSE CODE • OPERATING • REFERENCE',size=8.2,color=muted)
  line(TH-66*mm,'CW','SansBold',102,amber)
  c.setStrokeColor(amber);c.setLineWidth(1.2);c.line(x,TH-80*mm,right,TH-80*mm)
  line(TH-97*mm,'A Practical','SansBold',23)
  line(TH-108*mm,'Community Guide','SansBold',23)
  line(TH-127*mm,'A friendly start for newcomers.',size=10.5)
  line(TH-135*mm,'A reference beside every key.',size=10.5)
  # The diagram spells CW with normal character and element spacing.
  xx=x
  for char in ['-.-.','.--']:
   for k in char:
    length=7.2*mm if k=='-' else 2.4*mm;c.setFillColor(amber);c.roundRect(xx,TH-153*mm,length,2.4*mm,1.2*mm,fill=1,stroke=0);xx+=length+2.4*mm
   xx+=4.8*mm
  line(31*mm,'Valeriy Bagrintsev','SansBold',12)
  line(22*mm,f'English community edition {VERSION} • 2026',size=8.6,color=muted)
  line(13*mm,'FREE TO SHARE • CC BY 4.0',size=8,color=muted)
 else:
  line(TH-26*mm,'A GOOD CONTACT STARTS WITH LISTENING.','SansBold',10.6,amber)
  ps=ParagraphStyle('back',fontName='Sans',fontSize=11,leading=16,textColor=cream)
  y=TH-41*mm
  for txt in ['Learn the rhythm, make a first contact, and keep useful words within reach. This guide is written for operators who enjoy a hand key and a notebook, those who use web tools, and everyone in between.','Inside: 139 abbreviation entries, 38 Q signals, 91 sample phrases, a worked contact, and a one-page desk card.','Share it with a club, print a copy for a friend, or help improve the next edition. Original material is licensed under Creative Commons Attribution 4.0 International.']:
   p=Paragraph(txt,ps);_,h=p.wrap(116*mm,300);p.drawOn(c,x,y-h);y-=h+10*mm
  line(24*mm,'CW: A Practical Community Guide','SansBold',11)
  line(15*mm,'Valeriy Bagrintsev • 2026 • CC BY 4.0',size=8.5,color=muted)

class ArtPage(Flowable):
 def __init__(self,kind):Flowable.__init__(self);self.kind=kind
 def wrap(self,w,h):return 1,1
 def draw(self):
  c=self.canv;d=c._doctemplate;d.art_pages[d.page]=self.kind;c.bookmarkPage('front-cover' if self.kind=='front' else 'back-cover');c.addOutlineEntry('Cover' if self.kind=='front' else 'Back cover','front-cover' if self.kind=='front' else 'back-cover',0,False)
  c.saveState();c.resetTransforms();draw_art(c,self.kind);c.restoreState()

def make_story(pm,prev_entries):
 story=[ArtPage('front'),PageBreak()]
 story += [paragraph('CW: A Practical Community Guide','h2'),paragraph(f'Valeriy Bagrintsev<br/>English community edition {VERSION} • 2026','small'),Spacer(1,6*mm),paragraph('A practical introduction to amateur Morse operation, with a reference section for operators at any level. Use it offline with a hand key and a notebook, alongside a radio, or with optional digital tools.','body'),Spacer(1,5*mm),paragraph('Free to share and adapt','h2'),paragraph('Original material © 2026 Valeriy Bagrintsev. Licensed under Creative Commons Attribution 4.0 International (CC BY 4.0). Share and adapt with attribution, a license link, and a note of changes. Linked resources and bundled fonts keep their own terms.','small'),paragraph('<link href="https://creativecommons.org/licenses/by/4.0/">creativecommons.org/licenses/by/4.0/</link>','small'),Spacer(1,5*mm),paragraph('This is an independently prepared guide. National rules, band plans, equipment manuals, and event regulations govern your actual operation. Examples use placeholder call signs and invented data.','small'),paragraph('AI tools were used in drafting, research support, layout, and consistency checks. Community corrections are welcome; see chapter 23.','small'),PageBreak()]
 story += [paragraph('Contents','h1','contents',1,'Contents')]
 entrymap={a:p for a,t,p in prev_entries};data=[]
 for a,t in heads+[('reference-links','Reference links')]:
  label=f'<link href="#{htm.escape(a,quote=True)}">{escape(t)}</link>'
  data.append([Paragraph(label,styles['toc']),Paragraph(str(entrymap.get(a,'—')),styles['tocpage'])])
 for part in range(2):
  if part:story.extend([PageBreak(),paragraph('Contents / continued','h1')])
  half=data[:13] if part==0 else data[13:]
  toc=Table(half,colWidths=[IW-10*mm,10*mm],hAlign='LEFT')
  toc.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),'Sans'),('TEXTCOLOR',(0,0),(-1,-1),black),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),5.5),('BOTTOMPADDING',(0,0),(-1,-1),5.5)]));story.append(toc)
 card=False
 for el in blocks:
  t=el.tag
  if t=='h1':card=el.get('id')=='deskcard'
  if t=='h1':
   story.append(ChapterBreak());title=' '.join(el.text_content().split());m=re.match(r'(\d+)\.\s*(.*)',title)
   if m:story.append(paragraph('CHAPTER '+m.group(1).zfill(2),'label'));display=m.group(2)
   else:display=title
   story.append(paragraph(escape(display),'cardh1' if card else 'h1',el.get('id'),1,title))
  elif t in ['h2','h3']:
   story.append(CondPageBreak((40 if card else 80) if t=='h2' else 55));story.append(paragraph(markup(el,pm),'cardh2' if card and t=='h2' else ('h2' if t=='h2' else 'h3'),el.get('id'),2,' '.join(el.text_content().split())))
  elif t=='p':story.append(paragraph(markup(el,pm),'cardbody' if card else 'body'))
  elif t=='blockquote':story.append(paragraph('<br/>'.join(markup(p,pm) for p in el.xpath('./p')),'cardquote' if card else 'quote'))
  elif t in ['ol','ul']:
   for i,li in enumerate(el.xpath('./li'),1):story.append(paragraph((str(i)+'. ' if t=='ol' else '• ')+markup(li,pm),'list'))
  elif t=='table':story.append(tableflow(el,pm))
 story += [ChapterBreak(),paragraph('Reference links','h1','reference-links',1,'Reference links'),paragraph('The numbered links in the text refer to this list. Links remain active in the PDF. You can use the guide and its exercises without opening any of them.','small')]
 for i,u in enumerate(urls,1):story.append(paragraph(f'<b>[{i}]</b> <link href="{htm.escape(u,quote=True)}">{escape(u)}</link>','url'))
 story += [FinalPad(),ArtPage('back')]
 grouped=[];i=0
 while i<len(story):
  f=story[i]
  if getattr(f,'_level',None)==2 and i+1<len(story) and isinstance(story[i+1],Table) and (re.fullmatch(r'Q[A-Z]{2}',getattr(f,'_title','')) or len(story[i+1]._cellvalues)<=8):grouped.append(KeepTogether([f,story[i+1]]));i+=2
  else:grouped.append(f);i+=1
 return grouped

def main():
 pm={};entries=[];prev=None
 for attempt in range(1,7):
  d=BookDoc(OUT/'cw-community-guide-raw.pdf');d.build(make_story(pm,entries))
  state=(d.page,tuple(d.entries),tuple(sorted(d.page_map.items())))
  print(f'Layout pass {attempt}: {d.page} pages',flush=True)
  if state==prev:break
  pm=d.page_map;entries=d.entries;prev=state
 else:raise RuntimeError('Pagination did not stabilize')
 reader=PdfReader(OUT/'cw-community-guide-raw.pdf');writer=PdfWriter();writer.clone_document_from_reader(reader)
 for p in writer.pages:p.trimbox=RectangleObject([0,0,TW,TH]);p.cropbox=RectangleObject([0,0,TW,TH]);p.bleedbox=RectangleObject([0,0,TW,TH])
 writer.add_metadata({'/Title':'CW: A Practical Community Guide','/Author':'Valeriy Bagrintsev','/Subject':f'A worldwide introduction and desk reference for amateur Morse operation. English community edition {VERSION}, 2026.','/Keywords':'Morse code, CW, amateur radio, community guide, CC BY 4.0, A5','/Copyright':'Original material © 2026 Valeriy Bagrintsev, CC BY 4.0','/License':'https://creativecommons.org/licenses/by/4.0/'})
 writer._root_object[NameObject('/Lang')]=TextStringObject('en')
 target=BOOK/f'CW-Community-Guide-English-A5-2026-{VERSION}.pdf'
 with target.open('wb') as f:writer.write(f)
 info={'pages':len(reader.pages),'blank_pages':sorted(d.blank_pages),'art_pages':d.art_pages,'entries':d.entries,'anchors':d.page_map,'page_mm':[148,210],'inside_mm':20,'outside_mm':15,'version':VERSION,'language':'en'}
 (OUT/'layout.json').write_text(json.dumps(info,ensure_ascii=False,indent=2));(OUT/'cw-community-guide-raw.pdf').unlink();print(target)
if __name__=='__main__':main()
