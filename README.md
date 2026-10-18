# Where were the Mesopotamian gods born?

A separate, source-led companion to the Greek gods atlas. **The main artifact is a 4000 × 5000 PNG poster.** The original Greek project was read only and was not changed.

- [View the poster and research companion](https://khayoon.github.io/mesopotamian-gods-atlas/)
- [Download the full-resolution PNG](https://khayoon.github.io/mesopotamian-gods-atlas/mesopotamian-gods.png)
- [Editable SVG](docs/mesopotamian-gods.svg)
- [Research data](docs/data/research.json) and [site coordinates](docs/data/cities.json)
- [Geographic provenance](GEO-PROVENANCE.md) and [credits](CREDITS.md)

## What the image means

The poster retains the requested birthplace question, but answers it through a differentiated geography. Most pins are **cult seats or patronage associations**, not births. Its 22 city labels cover 41 deity identities, with names/aliases counted once even when a god has multiple cities. The companion contains 90 researched identity records, including lesser southern deities and unlocated/cosmic figures. This is a substantial selected catalogue, not an exhaustive god list or a claim to have searched every unpublished tablet.

Four categories are actually used on the poster:

- **Cult seat / patronage**: a documented temple, divine residence or local patronage association. This does not establish biological or mythological birth.
- **Explicit city birth**: Nanshe at Eridu and Ninazu at Ur. The larger city labels also name local cult deities, but the birth figures are explicitly named in rust-coloured type.
- **Conception**: Nanna at Nippur in *Enlil and Ninlil*. The text narrates insemination and the city setting, not an independently located delivery.
- **Inferred shrine birth**: *Utu B* places Utu's birth in E-nun-ana; identifying that temple with Sippar uses *The Temple Hymns*. This is an explicit cross-text inference, not a place name directly stated in the birth passage.

Marduk's Apsu birth remains cosmic, rather than being silently pinned to Babylon or Eridu. Eresh, Kesh, Karkara, Kuara and several minor sanctuary sites are unpinned where independent geography is uncertain. Dilmun is a changing Gulf region. The disputed geography of the later *Enki and Ninhursaga* birth episodes is preserved, including Dina Katz's argument for southern Sumerian marshes. No arbitrary Bahrain birth cluster was created.

## Periods, names and competing traditions

Sumerian and Akkadian are languages, and Babylonian traditions developed over a long time. The image is a cross-period literary and cultic geography, not a synchronized pantheon. ETCSL compositions are often known through Old Babylonian witnesses; manuscript date and composition date are distinguished where possible. Later royal inscriptions and scholarly identifications are individually dated in the data.

Conventional bilingual correspondences (Enki/Ea, Utu/Shamash, Nanna/Sin, Inanna/Ishtar) are not counted as extra gods. Historically separate local identities such as Gula, Ninkarrak, Ninisina, Bau and Nanaya have their own records with syncretism cautions. Ninurta and Ningirsu are kept as named local cult identities, not assumed universally identical. The homonymous Ninsikila roles in the Dilmun opening and the healing-birth episode are explicitly distinguished; the count is a catalogue convention, not proof of an invariant ancient ontology.

Each origin and cult claim has a work, passage reference where available, accessible source URL, period qualification, and a claim type. No origin coordinate is inferred merely from a deity's cult city. City coordinates are representative archaeological site points, not exact birth/event or temple coordinates. Genealogy alone does not establish geography. Some records provide only kinship or cult evidence, and state that limit.

## Reproduce and edit

The project is buildless. Serve the `docs` directory to use the companion:

```sh
python -m http.server 8766 --directory docs
```

Open `http://localhost:8766/`. Search the catalogue by name, alias, city or text; filter explicit city births, cosmic/unlocated origins, and cult places. The composition workbench moves SVG label groups and their individual curved leaders while keeping pins fixed, exports a 4000 × 5000 PNG or font-embedded SVG, and saves label offsets. Browser edits are temporary and do not modify the published poster or source catalogue. Inspect edited exports for collisions. The former terrain/flood composition and its visibility control remain at `exploration/`.

The reviewed poster can be regenerated with Python 3 and Pillow from the included geographic assets:

```sh
python -m pip install -r requirements.txt
python scripts/render-poster.py
```

Edit `docs/data/poster-layout.json` to change wording, individual caption positions, curve controls or endpoints, then rerun. The SVG retains editable text and exact geographic paths. Gentium Plus and Source Sans 3 font files are bundled; installing them helps desktop SVG editors preserve typography. The browser export embeds both families. The quiet default uses prominent serif deity names, sans-serif place labels, brief qualifiers and a compact source strip; its 22 labels still cover all 41 previously mapped identities.

`scripts/build-data.py PATH_TO_PLEIADES_places.csv` merges the two evidence working files and imports the selected site coordinates from the [Pleiades GIS release](https://atlantides.org/downloads/pleiades/gis/). The merged, ready-to-use data are already included; regeneration is optional. `scripts/build-geography.py` reproduces the original full-resolution regional shoreline and retained WDBII source extract; see its provenance document and the manifest for hashes and retained vertex counts.

To rebuild the revised relief, clean river centrelines and native-cell coastal elevation scenario, install the additional packages in `requirements.txt` and run:

```sh
python scripts/build-landscape.py
python scripts/build-flood.py
python scripts/render-poster.py
python scripts/validate.py
```

The two geographic builders cache downloads in ignored `work/terrain/` directories; `--cache PATH` can select another location. They need network access and substantial RAM. The flood builder retrieves selected original DeltaDTM TIFF members with validated HTTP range requests, not the entire 17 GB Asia archive. The ready-made native mask, polygons and manifests are already included, so rebuilding these layers is optional.

## Geographic accuracy and checks

The default poster uses a north-up Mercator projection centered on the lower Mesopotamian river corridor. The 50 km scale bar is calibrated at 32° N. Most of the modern Gulf lies southeast of this closer frame. GSHHG full-resolution coastal vertices and HydroRIVERS centrelines are retained without additional simplification; inland lake and reservoir outlines are omitted. These are modern-reference modelled channels, not reconstructed ancient waterways. Political borders, relief, ecological washes and flood layers are absent from the default poster.

The separate [terrain and flood study](docs/exploration/index.html) keeps the original equirectangular frame, Mapzen / USGS relief, RESOLVE ecological wash, Ramsar marsh anchors and optional **+4 m EGM2008 elevation scenario**. Corrected DeltaDTM 1.1.1 was classified at native one-arcsecond spacing (about 30 m), before display reprojection. Only valid low ground connected to the Gulf is flooded. This is not a dated ancient shoreline; EGM2008 is not local mean sea level. Native GeoTIFF, exact-cell GeoJSON, threshold comparisons and source hashes remain available. Full methods, crop limitations and licensing are in [GEO-PROVENANCE.md](GEO-PROVENANCE.md).

The exported PNG and a browser PNG export were visually inspected. Layout checks cover label bounds and geographic-name/leader collisions. Catalogue checks cover unique IDs, referenced city IDs, exact passages/URLs on each evidence claim, and null coordinates for unlocated places. These checks support an illustrated research aid; they do not substitute for a critical edition or specialist review of every deity.

GitHub Pages serves `docs/` from `main`.
