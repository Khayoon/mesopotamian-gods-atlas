"""Canonical poster with restrained landscape context. Run: python scripts/render-poster.py
The suggested ancient Gulf is adapted from Forti et al. (2022), Figure 14.
The modern-terrain flood calculation remains separate in docs/exploration/.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageChops
import html, json, math, base64
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'docs'; DATA=OUT/'data'
L=json.loads((DATA/'poster-layout.json').read_text('utf8'))
C={c['id']:c for c in json.loads((DATA/'cities.json').read_text('utf8'))}
W,H=L['width'],L['height']; S=1.5
PAPER='#f5f0e4'; LAND='#e9e4d5'; WATER='#e4ebe6'; INK='#263d33'
MUTED='#727b6d'; COAST='#8f9a86'; RIVER='#68958f'; RUST='#a0523b'
GOLD='#e7b84e'; BLUE='#496c75'; LEADER='#9ca58f'
im=Image.new('RGB',(round(W*S),round(H*S)),PAPER); d=ImageDraw.Draw(im)
FONT={'serif':'GentiumPlus-Regular.ttf','bold':'GentiumPlus-Bold.ttf','sans':'SourceSans3-Regular.ttf','sansbold':'SourceSans3-Bold.ttf'}
cache={}; svg=[]; text_boxes=[]; blocks=[]; leaders=[]
def font(size,kind='serif'):
    key=(size,kind)
    if key not in cache:cache[key]=ImageFont.truetype(str(OUT/'vendor'/FONT[kind]),round(size*S))
    return cache[key]
def scaled(points):return [(round(x*S),round(y*S)) for x,y in points]
def path_string(points):return 'M'+'L'.join(f'{x:.3f},{y:.3f}' for x,y in points)
def width(string,size,kind='serif'):return d.textlength(string,font=font(size,kind))/S
def text(x,y,string,size=40,kind='serif',fill=INK,halo=0,track=True):
    f=font(size,kind); bbox=f.getbbox(string,anchor='ls'); baseline=y-bbox[1]/S
    d.text((round(x*S),round(baseline*S)),string,font=f,anchor='ls',fill=fill,stroke_width=round(halo*S),stroke_fill=PAPER)
    family='Gentium' if kind in ['serif','bold'] else 'SourceSans'; weight=700 if kind in ['bold','sansbold'] else 400
    svg.append(f'<text x="{x:.3f}" y="{baseline:.3f}" font-family="{family}" font-size="{size}" font-weight="{weight}" fill="{fill}"'+(f' stroke="{PAPER}" stroke-width="{halo*2}" paint-order="stroke fill" stroke-linejoin="round"' if halo else '')+'>'+html.escape(string)+'</text>')
    box=[x,y,x+width(string,size,kind),baseline+bbox[3]/S]
    if track:text_boxes.append({'text':string,'box':box})
    return box
def line(points,fill=COAST,stroke=2):
    d.line(scaled(points),fill=fill,width=max(1,round(stroke*S)),joint='curve')
    svg.append(f'<path d="{path_string(points)}" fill="none" stroke="{fill}" stroke-width="{stroke}"/>')
def ellipse(box,fill=None,outline=None,stroke=2):
    d.ellipse(tuple(round(v*S) for v in box),fill=fill,outline=outline,width=max(1,round(stroke*S)))
    x,y,x2,y2=box
    svg.append(f'<ellipse cx="{(x+x2)/2}" cy="{(y+y2)/2}" rx="{(x2-x)/2}" ry="{(y2-y)/2}" fill="{fill or "none"}" stroke="{outline or "none"}" stroke-width="{stroke}"/>')
def polygon(points,fill,outline=None,stroke=2):
    d.polygon(scaled(points),fill=fill)
    if outline:d.line(scaled(points+[points[0]]),fill=outline,width=round(stroke*S),joint='curve')
    svg.append(f'<path d="{path_string(points)}Z" fill="{fill}" stroke="{outline or "none"}" stroke-width="{stroke}"/>')
def marker(x,y,kind='cult'):
    if kind=='cult':ellipse((x-13,y-13,x+13,y+13),PAPER);ellipse((x-7,y-7,x+7,y+7),INK)
    elif kind=='birth':ellipse((x-16,y-16,x+16,y+16),GOLD,INK,2.5)
    elif kind=='conception':polygon([(x,y-17),(x+17,y),(x,y+17),(x-17,y)],BLUE,PAPER,2.5)
    elif kind=='inferred':ellipse((x-18,y-18,x+18,y+18),PAPER,RUST,2.5);ellipse((x-5,y-5,x+5,y+5),RUST)
def merc(lat):return math.log(math.tan(math.pi/4+math.radians(lat)/2))
P=L['projection']
def project(lon,lat):return P['x0']+P['scale']*math.radians(lon-P['lon0']),P['y0']+P['scale']*(merc(P['lat0'])-merc(lat))
def quadratic(a,c,b,n=64):
    return [((1-t)**2*a[0]+2*(1-t)*t*c[0]+t*t*b[0],(1-t)**2*a[1]+2*(1-t)*t*c[1]+t*t*b[1]) for t in [i/n for i in range(n+1)]]
styles=''.join(f'@font-face{{font-family:{family};src:url(vendor/{name});font-weight:{weight}}}' for family,name,weight in [('Gentium',FONT['serif'],400),('Gentium',FONT['bold'],700),('SourceSans',FONT['sans'],400),('SourceSans',FONT['sansbold'],700)])
frame=L['mapFrame'];x1,y1,x2,y2=frame;fw,fh=x2-x1,y2-y1
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><title>{html.escape(" ".join(L["title"]))}</title><desc>Most locations are cult seats. Explicit birth, conception and inferred shrine birth are distinguished. Complete evidence is in the companion catalogue.</desc><defs><style>{styles}</style><clipPath id="mapclip"><rect x="{x1}" y="{y1}" width="{fw}" height="{fh}"/></clipPath><pattern id="dots" width="46" height="46" patternUnits="userSpaceOnUse"><circle cx="23" cy="23" r="1.5" fill="#d9d2c2"/></pattern><linearGradient id="fadeX"><stop offset="0" stop-color="black"/><stop offset=".025" stop-color="white"/><stop offset=".975" stop-color="white"/><stop offset="1" stop-color="black"/></linearGradient><linearGradient id="fadeY" x2="0" y2="1"><stop offset="0" stop-color="black"/><stop offset=".035" stop-color="white"/><stop offset=".965" stop-color="white"/><stop offset="1" stop-color="black"/></linearGradient><mask id="mx" maskUnits="userSpaceOnUse" x="{x1}" y="{y1}" width="{fw}" height="{fh}"><rect x="{x1}" y="{y1}" width="{fw}" height="{fh}" fill="url(#fadeX)"/></mask><mask id="my" maskUnits="userSpaceOnUse" x="{x1}" y="{y1}" width="{fw}" height="{fh}"><rect x="{x1}" y="{y1}" width="{fw}" height="{fh}" fill="url(#fadeY)"/></mask></defs>')
svg.append(f'<rect width="{W}" height="{H}" fill="{PAPER}"/>')
# Muted modern-reference landscape. Original coastal/river vertices remain vectors.
layer=Image.new('RGBA',im.size,(0,0,0,0)); ld=ImageDraw.Draw(layer)
ld.rectangle(tuple(round(v*S) for v in frame),fill=WATER)
svg.append(f'<g id="geography" clip-path="url(#mapclip)" mask="url(#mx)"><g mask="url(#my)"><rect x="{x1}" y="{y1}" width="{fw}" height="{fh}" fill="{WATER}"/>')
context_manifest=json.loads((DATA/'context-manifest.json').read_text('utf8'))
assert context_manifest['projection']==P and context_manifest['mapFrame']==frame, 'Rebuild geographic context for the new frame'
context=(DATA/'context-base.png').read_bytes()
background=Image.open(DATA/'context-base.png').convert('RGBA').resize((round(fw*S),round(fh*S)),Image.Resampling.LANCZOS)
layer.paste(background,(round(x1*S),round(y1*S)));ld=ImageDraw.Draw(layer)
svg.append(f'<image id="landscape-context" x="{x1}" y="{y1}" width="{fw}" height="{fh}" href="data:image/png;base64,'+base64.b64encode(context).decode()+'"/>')
for feature in json.loads((DATA/'coastline.geojson').read_text('utf8'))['features']:
    if feature['properties']['level']!=1:continue
    g=feature['geometry'];polys=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
    for rings in polys:
        # Omit inland lake/reservoir outlines; preserve offshore islands.
        points=[project(lon,lat) for lon,lat,*_ in rings[0]]
        ld.line(scaled(points),fill=COAST,width=round(1.8*S),joint='curve')
        svg.append(f'<path data-geometry="ocean-coast" d="{path_string(points)}Z" fill="none" stroke="{COAST}" stroke-width="1.8"/>')
river_count=0
for feature in json.loads((DATA/'rivers-display.geojson').read_text('utf8'))['features']:
    g=feature['geometry'];a=feature['properties'];area=a['UPLAND_SKM'];flow=a['DIS_AV_CMS']
    if area<15000 and flow<80:continue
    stroke=5.2 if area>=85000 else 2.6 if flow>=300 else 1.2
    colour=RIVER if area>=85000 else '#afbfaf';river_count+=1
    for path in (g['coordinates'] if g['type']=='MultiLineString' else [g['coordinates']]):
        points=[project(lon,lat) for lon,lat,*_ in path]
        ld.line(scaled(points),fill=colour,width=max(1,round(stroke*S)),joint='curve')
        svg.append(f'<path data-geometry="river-centerline" d="{path_string(points)}" fill="none" stroke="{colour}" stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round"/>')
# A published historical hypothesis is not the modern-terrain +4 m calculation.
# Draw it over the modern river/coast reference so those lines become subdued
# within the suggested Gulf; its crop edges must never masquerade as shores.
historic=json.loads((DATA/'palaeogulf.geojson').read_text('utf8'))['features']
water_feature=next(f for f in historic if f['properties']['role']=='suggested-water-area')
points=[project(*p) for p in water_feature['geometry']['coordinates'][0]]
overlay=Image.new('RGBA',im.size,(0,0,0,0));od=ImageDraw.Draw(overlay)
od.polygon(scaled(points),fill=(218,232,227,235))
layer=Image.alpha_composite(layer,overlay);ld=ImageDraw.Draw(layer)
svg.append(f'<g id="suggested-ancient-gulf"><path d="{path_string(points)}Z" fill="#dae8e3" fill-opacity="{235/255:.6f}"/>')
shore=next(f for f in historic if f['properties']['role']=='suggested-shore')
for path in shore['geometry']['coordinates']:
    points=[project(*p) for p in path];distance=0
    # Same dashed symbol in Pillow and SVG, independent of source vertex spacing.
    for a,b in zip(points[:-1],points[1:]):
        length=math.dist(a,b);at=0
        while at<length:
            stop=min(length,at+(18-distance%18))
            if distance%18<10:
                stop=min(stop,at+(10-distance%18))
                ld.line(scaled([(a[0]+(b[0]-a[0])*t/length,a[1]+(b[1]-a[1])*t/length) for t in [at,stop]]),fill='#7eaaa1',width=round(2.1*S))
            distance+=stop-at;at=stop
    svg.append(f'<path data-geometry="suggested-ancient-shore" d="{path_string(points)}" fill="none" stroke="#7eaaa1" stroke-width="2.1" stroke-dasharray="10 8"/>')
svg.append('</g>');del overlay,od
svg.append('</g></g>')
pixel_frame=tuple(round(v*S) for v in frame);crop=layer.crop(pixel_frame);cw,ch=crop.size
fx=Image.new('L',(cw,ch),255);fy=Image.new('L',(cw,ch),255);xd=ImageDraw.Draw(fx);yd=ImageDraw.Draw(fy)
for a in range(round(90*S)):
    v=round(255*a/(90*S));xd.line([(a,0),(a,ch)],fill=v);xd.line([(cw-a-1,0),(cw-a-1,ch)],fill=v)
for a in range(round(120*S)):
    v=round(255*a/(120*S));yd.line([(0,a),(cw,a)],fill=v);yd.line([(0,ch-a-1),(cw,ch-a-1)],fill=v)
crop.putalpha(ImageChops.multiply(crop.getchannel('A'),ImageChops.multiply(fx,fy)))
im.paste(crop,pixel_frame[:2],crop);d=ImageDraw.Draw(im)
del layer,ld,crop,fx,fy,xd,yd
for y in range(23,H,46):
    for x in range(23,W,46):d.ellipse((round((x-1.5)*S),round((y-1.5)*S),round((x+1.5)*S),round((y+1.5)*S)),fill='#d9d2c2')
svg.append(f'<rect width="{W}" height="{H}" fill="url(#dots)"/>')
text(155,125,L['title'][0],215,'bold');text(155,360,L['title'][1],215,'bold')
text(166,655,L['subtitle'],61);text(166,765,L['readingNote'],47,'sans',MUTED)
# Curves are independently authored; the pin endpoint never moves.
for label in L['labels']:
    a=project(*C[label['cityId']]['coordinates']);b=label['leader']['end'];c=label['leader']['control'];points=quadratic(a,c,b)
    d.line(scaled(points),fill=LEADER,width=round(2.1*S),joint='curve')
    original=' '.join(f'{x:.3f},{y:.3f}' for x,y in [a,c,b])
    svg.append(f'<path id="leader-{label["cityId"]}" data-curve="quadratic" data-original="{original}" d="M{a[0]:.3f},{a[1]:.3f}Q{c[0]:.3f},{c[1]:.3f} {b[0]:.3f},{b[1]:.3f}" fill="none" stroke="{LEADER}" stroke-width="2.1"/>')
    leaders.append({'cityId':label['cityId'],'points':points,'control':c,'end':b,'length':sum(math.dist(p,q) for p,q in zip(points[:-1],points[1:]))})
for label in L['labels']:marker(*project(*C[label['cityId']]['coordinates']),label['mark'])
for label in L['labels']:
    x,y=label['x'],label['y'];top=y;own=[];size=label.get('nameSize',80)
    svg.append(f'<g id="label-{label["cityId"]}" data-city="{label["cityId"]}">')
    for row in label['names']:
        tokens=[];start=0
        for term,kind in label.get('emphasis',{}).items():
            at=row.find(term)
            if at>=0:tokens.append((at,at+len(term),kind))
        cursor=x
        for lo,hi,kind in sorted(tokens)+[(len(row),len(row),None)]:
            if lo>start:
                part=row[start:lo];own.append(text(cursor,y,part,size,'bold',halo=2.4));cursor+=width(part,size,'bold')
            if hi>lo:
                part=row[lo:hi];own.append(text(cursor,y,part,size,'bold',RUST if kind=='birth' else BLUE,2.4));cursor+=width(part,size,'bold')
            start=hi
        y+=size*1.08
    refs=','.join(str(v) for v in label['refs']);last=label['names'][-1]
    own.append(text(x+width(last,size,'bold')+16,y-size*1.02,refs,27,'sansbold',RUST,1.5))
    own.append(text(x,y+5,C[label['cityId']]['name'],50,'sansbold',INK,2.2));y+=66
    if label.get('note'):own.append(text(x,y,label['note'],39,'sans',MUTED,2));y+=49
    box=[min(b[0] for b in own),top,max(b[2] for b in own),max(b[3] for b in own)]
    blocks.append({'cityId':label['cityId'],'box':box});label['actualBottom']=box[3];svg.append('</g>')
geo=[]
for item in L['geographicLabels']:
    colour=RIVER if item['text'] in ['Tigris','Euphrates','Persian Gulf','Southern marshes'] else MUTED
    b=text(item['x'],item['y'],item['text'],item.get('size',40),'serif',colour,2);geo.append({'text':item['text'],'box':b})
nx,ny=3700,1170
line([(nx,ny+70),(nx,ny-38)],COAST,2);polygon([(nx,ny-55),(nx-10,ny-26),(nx+10,ny-26)],COAST)
text(nx-13,ny-105,'N',32,'serif',MUTED)
sx,sy=240,4320;length=P['scale']*50000/(6371008.8*math.cos(math.radians(32)))
line([(sx,sy),(sx+length,sy)],COAST,2)
for xx in [sx,sx+length]:line([(xx,sy-8),(xx,sy+8)],COAST,2)
text(sx,sy+18,'0',29,'sans',MUTED);text(sx+length-65,sy+18,'50 km',29,'sans',MUTED)
for x,kind,caption in [(190,'cult','Cult seat / patronage'),(1260,'birth','Explicit city birth'),(2220,'conception','Conception'),(2990,'inferred','Inferred shrine birth')]:
    marker(x,4495,kind);text(x+34,4473,caption,40,'sansbold',INK)
line([(165,4600),(3835,4600)],'#b9bead',1.5);text(165,4630,'SOURCES',29,'sansbold',MUTED)
for i,source in enumerate(L['sources']):
    col=i//3;row=i%3;text(165+col*1240,4680+row*43,f'{source["number"]}  {source["posterShort"]}',30,'sans',MUTED)
text(165,4855,'Full passages, competing traditions and bibliography: khayoon.github.io/mesopotamian-gods-atlas',34,'sans',MUTED)
text(165,4920,'Geography: GSHHG · HydroRIVERS · Pleiades · Mapzen / USGS · RESOLVE. Suggested ancient Gulf: Forti et al. (2022), Fig. 14.',28,'sans',MUTED)
svg.append('</svg>');im=im.resize((W,H),Image.Resampling.LANCZOS)
im.save(OUT/'mesopotamian-gods.png',optimize=True,dpi=(300,300))
im.resize((1600,2000),Image.Resampling.LANCZOS).save(OUT/'poster-preview.jpg',quality=93)
(OUT/'mesopotamian-gods.svg').write_text('\n'.join(svg),'utf8')
(ROOT/'layout-verification.json').write_text(json.dumps({'labels':L['labels'],'textBoxes':text_boxes,'calloutBoxes':blocks,'leaders':leaders,'geographicLabels':geo,'riverFeaturesDrawn':river_count,'projection':P},ensure_ascii=False,indent=2)+'\n','utf8')
print('Rendered quiet 4000 × 5000 poster, editable SVG and preview.')
