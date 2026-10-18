# Geographic provenance

**Current default poster:** quiet flat geography, individually positioned callouts, and a north-up Mercator projection (48,000 pixels per radian). Its scale bar is 50 km at 32° N. The closer frame emphasizes the archaeological river corridor; most of today's Gulf lies southeast of that frame. Site coordinates and source coastal/river vertices have not been moved or simplified. The former equirectangular terrain, ecology and +4 m composition is retained separately at `docs/exploration/`, including its original layout and flood visibility control. The sections below document both the shared source data and that optional study.

The basemap is **modern reference geography**, not a reconstruction of a single ancient period. Southern Iraq's river channels, wetlands, and the head of the Persian Gulf have changed. The position of an ancient city relative to a modern river or shore does not establish its ancient waterfront. The translucent **+4 m EGM2008 overlay is a modern-terrain elevation scenario**, not a dated ancient shoreline. Terrain and ecological colours distinguish broad landscapes; they do not reconstruct ancient vegetation or a period-specific wetland boundary.

## Original full-resolution shoreline

Source: Paul Wessel and Walter H. F. Smith, **Global Self-consistent Hierarchical High-resolution Geography (GSHHG), version 2.3.7**, 15 June 2017. The original binary distribution was used, specifically **`gshhs_f.b`** (`f` = full resolution). It is not the `h`, `i`, `l`, or `c` product. No additional coastline simplification, smoothing, resampling, or vertex reduction was applied.

- [Official GSHHG repository and documentation](https://github.com/GenericMappingTools/gshhg-gmt)
- [Official 2.3.7 binary archive](https://github.com/GenericMappingTools/gshhg-gmt/releases/download/2.3.7/gshhg-bin-2.3.7.zip)
- [Dataset record and citation](https://doi.org/10.5281/zenodo.7007502)
- [Wessel and Smith 1996, *A global, self-consistent, hierarchical, high-resolution shoreline database*](https://doi.org/10.1029/96JB00104)

The archive was reused from the Greek atlas's retained original download and read without modifying that project. Its contents identify version 2.3.7. The archive and member hashes below make the exact input identifiable.

| Input | Bytes | SHA-256 |
|---|---:|---|
| `gshhg-bin-2.3.7.zip` | 118,617,033 | `28600e8f7a08645aab43079326df6504212ec5ccb2b4bcf3b5f4f12ed60e82bc` |
| `gshhs_f.b` | 95,809,336 | `af9215d58ebc525b2d09654a89959829f09e6edc457f3666759cded37be4ecf6` |
| `wdb_rivers_f.b` | 21,377,616 | `d91eaa3b22f08535b93f3cb8afeff4e48a43ec33e8a3b798696147fc7e6d4a21` |

`scripts/build-geography.py` parses the original big-endian eleven-int headers and microdegree coordinate pairs. The extraction frame is **40–52° E, 25–35° N**, extended west of the visible poster so that a clipping edge cannot masquerade as a coastline within the composition. Coordinates are longitude, latitude on WGS 84 (EPSG:4326), consistent with the source's stated convention. It intersects each original polygon or line with that rectangle. Clipping adds only boundary intersection vertices. It does not generalize the interior vertices. No input geometry in this frame required a validity repair. A separate exact-coordinate comparison verified that **zero original in-frame vertices are missing** from either output dataset. A rendered geographic overview was inspected for wrapping artifacts and the positions of the Persian Gulf, its islands, and the river network.

`docs/data/coastline.geojson` includes every GSHHG land, lake, island-in-lake, and pond feature intersecting the frame, including small Persian Gulf islands. It contains **232 features and 34,294 output vertices**. There are 34,289 original vertices inside the frame; the small difference arises from clipping intersections and ring closures. Features retain their source ID, hierarchical level, container ID, and river-lake flag. The revised poster displays only level-1 ocean coast and offshore islands. Inland lake/reservoir outlines are omitted and their areas filled as land. The retained source extraction still includes all levels. The frame boundary closes clipped land polygons and must not be styled as an actual coastline.

## Rivers displayed in the revised poster

The revised poster uses **HydroRIVERS v1.0**, Europe and Middle East, from [HydroSHEDS](https://www.hydrosheds.org/products/hydrorivers). The network derives from 15-arcsecond HydroSHEDS grids (roughly 400–460 m here). It provides river centrelines rather than reservoir shore polygons. `docs/data/rivers-display.geojson` retains 1,040 regional reaches with upstream catchment ≥4,000 km² and modelled mean flow ≥6 m³/s. Major trunks use stronger, thicker strokes; minor tributaries are subdued. This width hierarchy is a symbol, not a measurement of channel width. Selection and rectangular clipping preserve the selected interior vertices without simplification or curve smoothing. Reach IDs, catchment areas, orders and flow estimates are retained. The input archive hash is in `landscape-manifest.json`.

Reference: Lehner, B. & Grill, G. (2013), “Global river hydrography and network routing: baseline data and new approaches to study the world's large river systems,” *Hydrological Processes* 27(15), 2171–2186, [doi:10.1002/hyp.9740](https://doi.org/10.1002/hyp.9740). HydroRIVERS uses the HydroSHEDS license, permitting scientific, educational and commercial use subject to its terms. This is **modern-reference modelled hydrography**, not an ancient-channel reconstruction or a current detailed survey. Local canals, historical avulsions and sub-grid channels are not comprehensively represented. Reservoir outlines and dam symbols are not displayed; modern modifications can still influence the underlying channel paths.

### Retained older source extract (not displayed)

`docs/data/rivers.geojson` comes from **`wdb_rivers_f.b`**, the full-resolution CIA World Data Bank II river lineaments bundled with the same original GSHHG archive. It has **215 features and 21,424 output vertices** in the frame. This includes the Tigris, Euphrates, Shatt al-Arab, tributaries, river-lakes, canals, and intermittent streams. The source does not supply river names; source IDs and classifications are preserved rather than inventing names in the data.

The WDBII lineage is older and less accurate than the WVS ocean coastline. These channels are a modern reference network compiled from older mapping, **not a current hydrographic survey** and **not ancient Sumerian or Babylonian waterways**. This limitation is explicitly stated in the GSHHG README. A wide river stored as a river-lake can appear as a closed outline. The extraction also retains 17 point/multipoint results from source line records that collapse geometrically; renderers should skip zero-dimensional river geometry. These are not added geographic claims.

River classes used by this extract are documented in [the official GMT `gshhg` manual](https://docs.generic-mapping-tools.org/6.5/supplements/gshhg/gshhg.html). Levels 0–4 are river-lakes and permanent rivers; 6–8 are intermittent rivers; 10–12 are canal classes. A renderer can omit minor channels for legibility, but should not change the original coastline geometry.

## Southern marshes

`docs/data/marsh-labels.geojson` contains **three factual label anchors**, using the published center coordinates of the Iraqi Ramsar Sites: Central Marshes (2241), Hammar Marsh (2242), and Hawizeh Marsh (1718). These anchors are suitable for placing regional labels. They are **not wetland outlines, exact ecological centroids, or ancient extents**. The separate ecological wash is described below. The Central and Hammar sites were designated in 2014 and Hawizeh in 2007; the labels refer to modern named wetlands.

- [Central Marshes, Ramsar Site 2241](https://rsis.ramsar.org/ris/2241): 31°10′34″ N, 46°59′ E.
- [Hammar Marsh, Ramsar Site 2242](https://rsis.ramsar.org/ris/2242): 30°48′22″ N, 47°01′01″ E.
- [Hawizeh Marsh, Ramsar Site 1718](https://rsis.ramsar.org/ris/1718): 31°25′ N, 47°37′59″ E.

The official Ramsar site descriptions identify these three areas as the southern Mesopotamian marshland complex. Their histories include drainage and reflooding; modern extents should not be extrapolated into antiquity. Only individual published coordinate facts and newly authored notes are redistributed here, not the Ramsar site's downloadable boundary database, photographs, or text.

## Terrain and ecological colour

`scripts/build-landscape.py` builds the background from [Mapzen / Tilezen Terrain Tiles](https://registry.opendata.aws/terrain-tiles/), accessed 18 October 2026, and [RESOLVE Ecoregions 2017](https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/Resolve_Ecoregions/FeatureServer/0). Terrarium tiles at zoom 9 have approximately 262 m ground spacing at 31° N. Their Web Mercator samples are bilinearly reprojected to the poster grid. The landscape raster is a **display layer only** and is never used to classify flooding. Northwest/northeast hillshade uses 2.5× vertical exaggeration to make the Zagros ridges legible; the elevation analysis itself is not exaggerated. Elevation tint starts above 170 m. Source tile URLs and hashes are retained in `docs/data/landscape-manifest.json`.

Global SRTM and GMTED2010 terrain data are courtesy of the U.S. Geological Survey; global ETOPO1 data are from NOAA/NCEI. These U.S. government source data are public domain in the United States. The regional tiles use the provider's global source stack; no claim of survey-grade terrain is made. See the provider's [format](https://github.com/tilezen/joerd/blob/master/docs/formats.md) and [attribution](https://github.com/tilezen/joerd/blob/master/docs/attribution.md) documentation.

The ochre western desert is a cartographic land colour. The soft green alluvial wash follows the envelope between major river centrelines, restricted to low terrain and tapered at its ends; it does not assert that the entire interfluve was permanently wet. The darker marsh wash follows RESOLVE ecological region **747, Tigris–Euphrates alluvial salt marsh**, softened only for drawing. Its unchanged vector source is retained in `ecoregions.geojson`. Ecological regions describe broad potential landscapes, not current land cover or dated ancient vegetation. RESOLVE data are CC BY 4.0; cite Dinerstein et al. (2017), “An Ecoregion-Based Approach to Protecting Half the Terrestrial Realm,” *BioScience* 67(6), 534–545, [doi:10.1093/biosci/bix014](https://doi.org/10.1093/biosci/bix014). The modern named marsh anchors are independently sourced above.

## +4 m EGM2008 coastal elevation scenario

The requested four-metre flood overlay cannot recover an ancient coastline precisely from modern elevations alone. The poster labels the calculation **“+4 m elevation scenario”** and explicitly states that it is not a dated ancient shoreline.

Source: Maarten Pronk, **DeltaDTM v1.1, official dataset version 4**, [doi:10.4121/21997565.v4](https://doi.org/10.4121/21997565.v4), CC BY 4.0. The official changelog identifies this corrected processing release as **1.1.1**, dated 10 December 2024; archive/member names retain `v1_1`. The [official README](https://data.4tu.nl/file/1da2e70f-6c4d-4b03-86bd-b53e789cc629/71c77b5f-b340-4fdb-a1b1-1d255b8ddb0f) specifies EGM2008 elevations and the v1.1 30 m coastal clipping ceiling. Method paper: Pronk et al. (2024), “DeltaDTM: A global coastal digital terrain model,” *Scientific Data* 11, 273, [doi:10.1038/s41597-024-03091-9](https://doi.org/10.1038/s41597-024-03091-9).

`scripts/build-flood.py` retrieves only the necessary original GeoTIFF ZIP members using byte ranges, validates CRC and SHA-256, and records the official readme/changelog and source-mask hashes. All 13 DTM tiles are placed on their original one-arcsecond grid: **15,660 × 10,800 cells**, actual bounds **45.500139–49.850139° E, 29.000139–32.000139° N**. Horizontal CRS is EPSG:4326; the source's documented vertical reference is EGM2008. **No conversion to local mean sea level is applied.** Nominal spacing is about 27 × 31 m here; this spacing does not imply matching elevation or shoreline accuracy.

Classification is performed **before any display reprojection**, using valid land elevations ≤4 m EGM2008 and four-neighbour connectivity to modern Gulf water. Ocean seeds are outside the original full-resolution GSHHG level-1 land polygons; inland lakes are filled as land and do not seed flooding. Missing or clipped elevation is a barrier, never a zero-height assumption. No coastline simplification is applied. Polygonization follows exact native cell edges. The GeoJSON shows **additional flooded modern land**, superimposed on the modern sea; the GeoTIFF distinguishes modern sea (1), added flooded land (2), dry land (0), and unavailable land (255).

Checks found **12,128,802 additional flooded cells, approximately 9,983.3 km²**, with no flooded cell above 4 m or on missing elevation. All 580 polygons are valid. There are no flooded-land contacts on the west, north or south model edges. The eastern crop intersects a small Iranian coastal fringe at 49.850139° E, 30.162222–30.248889° N (308 cells, about 9.6 km of edge); this is a regional crop, not a closed Gulf-wide contour. The downloadable 3 m and 5 m threshold scenarios are **sensitivity comparisons**, not statistical confidence limits.

The model does not account for ancient sediment deposition, erosion, compaction, subsidence, tectonics, sea-level history, ancient channels, tides or hydrodynamic flow. Modern embankments and sub-cell waterways can affect the connectivity result. GSHHG and DeltaDTM may disagree at the modern coast. The published global elevation error is not a local error bound, and no local ground-truth validation was performed. For why an ancient reconstruction requires more than modern relief, see Lambeck (1996), *Earth and Planetary Science Letters* 142, 43–57, [doi:10.1016/0012-821X(96)00069-6](https://doi.org/10.1016/0012-821X(96)00069-6).

Reproducibility assets: `flood-manifest.json`, `flood-4m-native.tif`, and unsimplified `flood-{3,4,5}m.geojson` in `docs/data/`. Original global archives and the selected source TIFF cache are not duplicated in the public repository. The script and manifest retain their download URLs and hashes.

## Ancient-site points

The 25 candidate archaeological-site anchors in `docs/data/cities.json` were selected from the Pleiades GIS `places.csv` distribution downloaded on 18 October 2026. Only 22 appear as poster callouts. Each selected point retains its individual canonical Pleiades URL, gazetteer title and precision classification. The CSV member's SHA-256 and retrieval URL are in `docs/data/site-provenance.json`. These are representative points for archaeological sites or complexes, not exact temple, myth-event or birth coordinates. Older ORACC gazetteer snapshots sometimes differ; the selected current Pleiades distribution is used consistently here. Other named sites remain null where location or identification is insufficiently secure. Pleiades contributors' data are licensed CC BY 3.0.

The optional terrain study retains the former local equirectangular projection with 480 pixels per longitude degree and 565 per latitude degree (approximately cos 31.8° longitude scaling), north up. Its scale bar is approximate at 31° N. The default poster now uses the north-up Mercator projection described above. Scene clipping affects only each displayed frame; it does not further simplify original coastal vertices.

## License and attribution

GSHHG 2.3.7 is distributed under the **GNU Lesser General Public License, version 3 or any earlier version**, as the release's LICENSE states. The derived GeoJSON retains that upstream license. The original license, LGPL text, and README are included in `docs/data/GSHHG-LICENSE.txt`, `GSHHG-COPYING.LESSERv3.txt`, and `GSHHG-README.txt`. The atlas's own license does not replace these upstream terms.

Suggested compact credit: **GSHHG 2.3.7 full-resolution coast (Wessel & Smith); HydroRIVERS (Lehner & Grill); Pleiades; Ramsar; RESOLVE 2017; Mapzen / USGS terrain; DeltaDTM 1.1.1 (Pronk). Modern reference geography and a +4 m EGM2008 test; ancient shorelines and channels varied.**

Machine-readable extraction counts, input hashes, output hashes, and clipping parameters are in `docs/data/geography-manifest.json`. To regenerate, install Shapely and run `python scripts/build-geography.py --archive PATH_TO_gshhg-bin-2.3.7.zip`; omit `--archive` to fetch the official release. The original 118 MB global archive is intentionally not duplicated in the public repository.
