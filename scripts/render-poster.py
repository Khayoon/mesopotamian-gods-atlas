"""Deterministic 4:5 PNG + editable SVG. All geography is sourced geometry.
Run from any directory: python scripts/render-poster.py
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import json, math, html, random, base64
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'docs'; DATA=OUT/'data'
L=json.loads((DATA/'poster-layout.json').read_text('utf-8'))
C={v['id']:v for v in json.loads((DATA/'cities.json').read_text('utf-8'))}
W,H=L['width'],L['height']; S=1.5
PAPER='#f5f0e5'; INK='#273f3a'; MUTED='#66766d'; LAND='#e9e5d7'; WATER='#dfe9e5'
RIVER='#477f87'; COAST='#708b81'; RUST='#a45035'; GOLD='#ac883b'
im=Image.new('RGB',(int(W*S),int(H*S)),PAPER); d=ImageDraw.Draw(im)
fontdir=OUT/'vendor'; FONT={'serif':fontdir/'GentiumPlus-Regular.ttf','bold':fontdir/'GentiumPlus-Bold.ttf'}
fonts={}; svg=[]; boxes=[]; leaders=[]
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><title>{html.escape(L["title"][0]+" "+L["title"][1])}</title><desc>Cult seats and separately identified birth traditions. Full source data accompanies this image.</desc><defs><style>@font-face{{font-family:Gentium;src:url(vendor/GentiumPlus-Regular.ttf)}}@font-face{{font-family:Gentium;src:url(vendor/GentiumPlus-Bold.ttf);font-weight:700}}text{{font-family:Gentium,serif}}</style><clipPath id="mapclip"><rect x="120" y="1030" width="3760" height="3310"/></clipPath><pattern id="dots" width="31" height="31" patternUnits="userSpaceOnUse"><circle cx="15" cy="15" r="1.1" fill="#d9d2c2"/></pattern></defs>')
svg.append(f'<rect width="4000" height="5000" fill="{PAPER}"/><rect width="4000" height="5000" fill="url(#dots)"/>')
svg.append('<defs><filter id="labelwash" x="-25%" y="-80%" width="150%" height="260%"><feGaussianBlur stdDeviation="24"/></filter></defs>')
def font(size,kind='serif'):
    key=(size,kind)
    if key not in fonts:fonts[key]=ImageFont.truetype(str(FONT[kind]),round(size*S))
    return fonts[key]
def pts(p):return [(round(x*S),round(y*S)) for x,y in p]
def line(p,fill=COAST,width=2,dash=False,record=True):
    if len(p)<2:return
    if dash:
        for a,b in zip(p[:-1],p[1:]):
            length=math.dist(a,b);steps=max(1,math.ceil(length/12))
            for i in range(0,steps,2):
                lo=i/steps;hi=min(i+1,steps)/steps
                d.line(pts([(a[0]+(b[0]-a[0])*lo,a[1]+(b[1]-a[1])*lo),(a[0]+(b[0]-a[0])*hi,a[1]+(b[1]-a[1])*hi)]),fill=fill,width=max(1,round(width*S)))
    else:d.line(pts(p),fill=fill,width=max(1,round(width*S)),joint='curve')
    if record:svg.append('<polyline points="'+' '.join(f'{x:.3f},{y:.3f}' for x,y in p)+f'" fill="none" stroke="{fill}" stroke-width="{width}" stroke-linejoin="round"'+(' stroke-dasharray="6 6"' if dash else '')+'/>')
def poly(p,fill,outline=None,width=2):
    if len(p)<3:return
    d.polygon(pts(p),fill=fill)
    if outline:d.line(pts(p+[p[0]]),fill=outline,width=round(width*S),joint='curve')
    svg.append('<polygon points="'+' '.join(f'{x:.3f},{y:.3f}' for x,y in p)+f'" fill="{fill}"'+(f' stroke="{outline}" stroke-width="{width}"' if outline else '')+'/>')
def ellipse(box,fill=None,outline=None,width=2):
    d.ellipse(tuple(round(a*S) for a in box),fill=fill,outline=outline,width=round(width*S))
    x,y,x2,y2=box
    svg.append(f'<ellipse cx="{(x+x2)/2}" cy="{(y+y2)/2}" rx="{(x2-x)/2}" ry="{(y2-y)/2}" fill="{fill or "none"}" stroke="{outline or "none"}" stroke-width="{width}"/>')
def text(x,y,string,size=42,kind='serif',fill=INK,halo=True,track=True):
    f=font(size,kind);d.text((round(x*S),round(y*S)),string,font=f,fill=fill,anchor='lt',stroke_width=round(3*S) if halo else 0,stroke_fill=PAPER)
    width=d.textlength(string,font=f)/S
    if track:boxes.append({'text':string,'box':[x,y,x+width,y+size*1.05]})
    svg.append(f'<text x="{x}" y="{y+size*.74}" font-size="{size}" font-weight="{700 if kind=="bold" else 400}" fill="{fill}"'+(f' stroke="{PAPER}" stroke-width="5" paint-order="stroke fill"' if halo else '')+'>'+html.escape(string)+'</text>')
    return width
def wrap_rows(string,width,size=42,kind='serif'):
    words=string.split();rows=[];cur=''
    for word in words:
        nxt=(cur+' '+word).strip()
        if cur and d.textlength(nxt,font=font(size,kind))/S>width:rows.append(cur);cur=word
        else:cur=nxt
    if cur:rows.append(cur)
    return rows

def wrapped(x,y,string,width,size=42,kind='serif',fill=MUTED,leading=1.14):
    rows=wrap_rows(string,width,size,kind)
    for j,row in enumerate(rows):text(x,y+j*size*leading,row,size,kind,fill)
    return y+len(rows)*size*leading
for y in range(15,H,31):
    for x in range(15,W,31):d.ellipse((round((x-1)*S),round((y-1)*S),round((x+1)*S),round((y+1)*S)),fill='#d9d2c2')
text(155,130,L['title'][0],215,'bold',halo=False)
text(155,365,L['title'][1],215,'bold',halo=False)
text(166,655,L['subtitle'],63,halo=False)
text(166,755,L['readingNote'],45,fill=MUTED,halo=False)
line([(166,858),(3835,858)],'#bdc4b4',2)
def star(x,y,r=15,color=RUST):
    p=[]
    for i in range(10):
        a=-math.pi/2+i*math.pi/5;rr=r if i%2==0 else r*.44;p.append((x+rr*math.cos(a),y+rr*math.sin(a)))
    poly(p,color)
def marker(x,y,kind='cult',r=12):
    ellipse((x-r-5,y-r-5,x+r+5,y+r+5),PAPER)
    ellipse((x-7,y-7,x+7,y+7),INK)
    if kind=='birth':star(x,y,19)
    elif kind=='conception':poly([(x,y-19),(x+19,y),(x,y+19),(x-19,y)],PAPER,GOLD,4)
    elif kind=='inferred':ellipse((x-17,y-17,x+17,y+17),PAPER,RUST,3);ellipse((x-5,y-5,x+5,y+5),RUST)
legend=[(185,'cult','Cult seat / patronage'),(1160,'birth','Explicit city birth'),(2100,'conception','Conception'),(2890,'inferred','Inferred shrine birth')]
for x,kind,s in legend:marker(x,928,kind);text(x+35,900,s,42,fill=MUTED,halo=False)
for x,color,s in [(185,'#ccd9b7','Alluvial plain'),(1160,'#b5c8ab','Marsh region'),(2100,'#eddfc3','Desert'),(2890,'#c9c4af','Mountain relief')]:
    poly([(x-12,983),(x+12,983),(x+12,1005),(x-12,1005)],color)
    text(x+35,972,s,34,fill=MUTED,halo=False)
p=L['projection']
def project(lon,lat):return p['x0']+p['pxPerLon']*(lon-p['lon0']),p['y0']+p['pxPerLat']*(p['lat0']-lat)
# Source-derived terrain is an embedded raster; original coastal paths remain vectors.
clip=(round(120*S),round(1030*S),round(3880*S),round(4340*S))
background=(DATA/'landscape-base.png').read_bytes()
landscape=Image.open(DATA/'landscape-base.png').convert('RGB').resize((clip[2]-clip[0],clip[3]-clip[1]),Image.Resampling.LANCZOS)
im.paste(landscape,clip[:2]);d=ImageDraw.Draw(im)
svg.append('<g clip-path="url(#mapclip)">')
svg.append('<image id="landscape" x="120" y="1030" width="3760" height="3310" href="data:image/png;base64,'+base64.b64encode(background).decode()+'"/>')
# Only ocean coastline / offshore islands are shown. Inland lakes/reservoirs are omitted.
cl=Image.new('RGBA',im.size,(0,0,0,0));cd=ImageDraw.Draw(cl)
for feature in json.loads((DATA/'coastline.geojson').read_text())['features']:
    geom=feature['geometry'];level=feature['properties']['level']
    if level!=1:continue
    polygons=geom['coordinates'] if geom['type']=='MultiPolygon' else [geom['coordinates']]
    for rings in polygons:
        for ring in rings[:1]:
            pp=[project(x,y) for x,y,*_ in ring]
            cd.line(pts(pp),fill=COAST,width=round(1.6*S),joint='curve')
            svg.append('<path data-geometry="ocean-coast" d="M'+'L'.join(f'{x:.3f},{y:.3f}' for x,y in pp)+f'Z" fill="none" stroke="{COAST}" stroke-width="1.6"/>')
im.paste(cl.crop(clip),clip[:2],cl.crop(clip));d=ImageDraw.Draw(im)
# A native-cell, Gulf-connected threshold scenario. It is never called an ancient coast.
if (DATA/'flood-4m.geojson').exists():
    fl=Image.new('RGBA',im.size,(0,0,0,0));fd=ImageDraw.Draw(fl)
    svg.append('<g id="flood-overlay" data-datum="EGM2008" data-level-metres="4">')
    for f in json.loads((DATA/'flood-4m.geojson').read_text('utf8'))['features']:
        g=f['geometry'];polys=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
        for rings in polys:
            svgpath=[]
            for j,ring in enumerate(rings):
                pp=[project(x,y) for x,y,*_ in ring]
                fd.polygon(pts(pp),fill=(114,173,183,96) if j==0 else (0,0,0,0))
                fd.line(pts(pp),fill=(76,132,146,110),width=max(1,round(1.25*S)),joint='curve')
                svgpath.append('M'+'L'.join(f'{x:.3f},{y:.3f}' for x,y in pp)+'Z')
            svg.append('<path d="'+''.join(svgpath)+'" fill="#72adb7" fill-opacity=".38" fill-rule="evenodd" stroke="#4c8492" stroke-opacity=".43" stroke-width="1.25"/>')
    im.paste(fl.crop(clip),clip[:2],fl.crop(clip));d=ImageDraw.Draw(im)
    svg.append('</g>')
svg.append('<rect x="120" y="1030" width="3760" height="3310" fill="url(#dots)" opacity=".5"/>')
for y in range(1040,4340,31):
    for x in range(130,3880,31):d.point((round(x*S),round(y*S)),fill='#d0d4c5')
rl=Image.new('RGBA',im.size,(0,0,0,0));rd=ImageDraw.Draw(rl)
for feature in json.loads((DATA/'rivers-display.geojson').read_text())['features']:
    g=feature['geometry'];prop=feature['properties']
    if g['type'] not in ['LineString','MultiLineString']:continue
    paths=g['coordinates'] if g['type']=='MultiLineString' else [g['coordinates']]
    for path in paths:
        pp=[project(x,y) for x,y,*_ in path]
        # Clip raster river paths to a dedicated layer so off-frame points cannot cross title.
        area=prop['UPLAND_SKM'];flow=prop['DIS_AV_CMS']
        width=5.6 if area>=85000 else 4.5 if flow>=300 else 3.2 if flow>=80 else 1.8
        color=RIVER if width>=3.2 else '#84a3a0'
        rd.line(pts(pp),fill=color,width=round(width*S),joint='curve')
        svg.append('<path data-geometry="river-centerline" d="M'+'L'.join(f'{x:.3f},{y:.3f}' for x,y in pp)+f'" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>')
im.paste(rl.crop(clip),clip[:2],rl.crop(clip));d=ImageDraw.Draw(im)
svg.append('</g>')
# Geographic names are intentionally sparse; the research labels carry the hierarchy.
geo_labels=[(1890,1170,'Lower Mesopotamia',49,MUTED),
 (1640,2600,'Euphrates',42,RIVER),(1730,1720,'Tigris',42,RIVER),
 (3040,1070,'Zagros Mountains',42,MUTED),(1350,3210,'Arabian Desert',42,MUTED)]
for feat in json.loads((DATA/'marsh-labels.geojson').read_text())['features']:
    x,y=project(*feat['geometry']['coordinates'])
    # Marsh symbols indicate named centres, not reconstructed boundaries.
    for dx in [-11,0,11]:line([(x+dx-3,y+7),(x+dx,y-8),(x+dx+3,y+3)],RIVER,1.6)
geo_labels += [(3220,4260,'Persian Gulf',57,RIVER),
 (2450,2840,'Shatt al-Arab',36,RIVER),(2610,2410,'Hawizeh',34,RIVER),
 (2405,2590,'Central marshes',34,RIVER),(2360,2790,'Hammar',34,RIVER)]
# Draw leaders before text. The two side corridors keep leaders out of labels.
tracks={}
for side in ['left','right']:
    for direction in ['up','down']:
        group=[]
        for label in L['labels']:
            x,y=project(*C[label['cityId']]['coordinates'])
            if label['side']==side and ((label['y']+27<y)==(direction=='up')):group.append((y,label))
        group.sort(key=lambda item:item[0])
        for j,(_,label) in enumerate(group):
            if side=='left':tx=1155+16*(len(group)-1-j) if direction=='up' else 1155+18*j
            else:tx=2770+16*j if direction=='up' else 2890-18*j
            tracks[label['cityId']]=tx
for i,label in enumerate(L['labels']):
    x,y=project(*C[label['cityId']]['coordinates']);ly=label['y']+27
    if label['side']=='left':
        end=label['x']+label['width']+14
    else:
        end=label['x']-24
    elbow=tracks[label['cityId']]
    path=[(x,y),(elbow,y),(elbow,ly),(end,ly)]
    col=RUST if label['mark'] in ['birth','inferred'] else GOLD if label['mark']=='conception' else '#8a9b8c'
    line(path,PAPER,8)
    original=' '.join(f'{a:.3f},{b:.3f}' for a,b in path)
    svg[-1]=svg[-1].replace('<polyline ',f'<polyline id="leader-halo-{label["cityId"]}" data-original="{original}" ')
    line(path,col,2.2,label['mark']=='inferred')
    svg[-1]=svg[-1].replace('<polyline ',f'<polyline id="leader-{label["cityId"]}" data-original="{original}" ')
    leaders.append(path)
for label in L['labels']:
    x,y=project(*C[label['cityId']]['coordinates']);marker(x,y,label['mark'])
for label in L['labels']:
    x,y,w=label['x'],label['y'],label['width'];start=y
    svg.append(f'<g id="label-{label["cityId"]}" data-city="{label["cityId"]}">')
    ns=label.get('nameSize',62)
    bottom=y+53+len(label['names'])*(ns+6)+2+len(wrap_rows(label['note'],w,42))*42*1.14
    panel=[x-15,y-12,x+w+15,bottom+8]
    padding=80
    pixel_box=tuple(round(a*S) for a in [panel[0]-padding,panel[1]-padding,panel[2]+padding,panel[3]+padding])
    mask=Image.new('L',(pixel_box[2]-pixel_box[0],pixel_box[3]-pixel_box[1]),0)
    ImageDraw.Draw(mask).rectangle((padding*S,padding*S,mask.width-padding*S,mask.height-padding*S),fill=210)
    mask=mask.filter(ImageFilter.GaussianBlur(24*S))
    im.paste(PAPER,pixel_box,mask);d=ImageDraw.Draw(im)
    svg.append(f'<rect x="{panel[0]}" y="{panel[1]}" width="{panel[2]-panel[0]}" height="{panel[3]-panel[1]}" fill="{PAPER}" fill-opacity=".824" filter="url(#labelwash)"/>')
    text(x,y,C[label['cityId']]['name'],43,fill=RUST if label['mark']=='birth' else MUTED)
    y+=53
    for row in label['names']:
        ns=label.get('nameSize',62)
        text(x,y,row,ns,'bold',RUST if '— birth' in row else GOLD if '— conception' in row else INK);y+=ns+6
    y=wrapped(x,y+2,label['note'],w,42,fill=INK)
    label['actualBottom']=y
    if y>4340:raise ValueError('Label extends into footer: '+label['cityId'])
    svg.append('</g>')
def intersects_rect(a,b,rect):
    x1,y1,x2,y2=rect
    # Liang–Barsky clipping: a positive clipped interval intersects the rectangle.
    low,high=0.,1.;dx=b[0]-a[0];dy=b[1]-a[1]
    for pp,qq in [(-dx,a[0]-x1),(dx,x2-a[0]),(-dy,a[1]-y1),(dy,y2-a[1])]:
        if abs(pp)<1e-12:
            if qq<0:return False
        elif pp<0:low=max(low,qq/pp)
        else:high=min(high,qq/pp)
        if low>high:return False
    return True
geo_qa=[]
for x,y,s,size,col in geo_labels:
    width=d.textlength(s,font=font(size))/S
    chosen=None
    for dy in [0,-40,40,-80,80,-120,120]:
        for dx in [0,-40,40,-80,80]:
            xx,yy=x+dx,y+dy;box=[xx-8,yy-8,xx+width+8,yy+size*1.1+8]
            if yy<1040 or yy+size>4340:continue
            if any(not (box[2]<t['box'][0] or box[0]>t['box'][2] or box[3]<t['box'][1] or box[1]>t['box'][3]) for t in boxes):continue
            if any(intersects_rect(a,b,box) for path in leaders for a,b in zip(path[:-1],path[1:])):continue
            chosen=(xx,yy);break
        if chosen:break
    if not chosen:raise ValueError('No collision-free geographic label position for '+s)
    text(*chosen,s,size,fill=col);geo_qa.append({'text':s,'position':chosen,'leaderCollisions':0})
# Scale, north, and geography explanation use the open lower central map.
sx,sy=1460,4170;bar=480/((111.32*math.cos(math.radians(31)))/100)
line([(sx,sy),(sx+bar,sy)],INK,4)
for xx in [sx,sx+bar/2,sx+bar]:line([(xx,sy-9),(xx,sy+9)],INK,3)
text(sx,sy+20,'0',32,fill=MUTED);text(sx+bar-42,sy+20,'100 km',32,fill=MUTED)
line([(2700,4150),(2700,4050)],INK,3);poly([(2700,4033),(2692,4057),(2708,4057)],INK);text(2685,3990,'N',34,fill=INK)
svg.append('<g id="scenario-key">')
poly([(1335,3600),(1374,3600),(1374,3634),(1335,3634)],'#abd0d0',RIVER,1.5)
text(1395,3590,'+4 m elevation scenario',47,'bold',RIVER)
wrapped(1335,3660,'Gulf-connected terrain ≤4 m EGM2008. DeltaDTM: 30 m cells. Modern terrain has changed through sedimentation and subsidence; this is not a dated ancient shoreline.',1320,40,fill=MUTED)
wrapped(1335,3900,'Terrain and ecological colours describe broad landscapes. Ancient river courses and marsh extents varied.',1320,35,fill=MUTED)
svg.append('</g>')
line([(165,4450),(3835,4450)],'#a9b5a6',2)
text(165,4485,'Sources',42,'bold')
columns=[165,1420,2675]
for i,source in enumerate(L['sources']):
    col=i//3;row=i%3
    wrapped(columns[col],4552+row*104,f'[{source["number"]}] '+source['short'],1160,33,fill=MUTED,leading=1.05)
text(165,4870,'Geography: GSHHG full-resolution coast · HydroRIVERS · Pleiades · Ramsar · RESOLVE 2017 · Mapzen / USGS relief.',31,fill=MUTED)
text(165,4920,'+4 m test: DeltaDTM 1.1.1, EGM2008 · Pronk et al., Scientific Data 11 (2024), 273. Methods and limits in the companion.',31,fill=MUTED)
svg.append('</svg>')
im=im.resize((W,H),Image.Resampling.LANCZOS)
im.save(OUT/'mesopotamian-gods.png',optimize=True,dpi=(300,300))
im.resize((1600,2000),Image.Resampling.LANCZOS).save(OUT/'poster-preview.jpg',quality=92)
(OUT/'mesopotamian-gods.svg').write_text('\n'.join(svg),'utf-8')
(ROOT/'layout-verification.json').write_text(json.dumps({'labels':L['labels'],'textBoxes':boxes,'leaders':leaders,'geographicLabels':geo_qa},ensure_ascii=False,indent=2),'utf-8')
print('Rendered 4000 × 5000 PNG, preview and editable SVG.')
