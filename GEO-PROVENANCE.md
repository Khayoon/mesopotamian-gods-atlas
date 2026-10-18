# Geographic provenance

The basemap is **modern reference geography**, not a reconstruction of a single ancient period. Southern Iraq's river channels, wetlands, and the head of the Persian Gulf have changed. The position of an ancient city relative to a modern river or shore does not establish its ancient waterfront. No ancient shoreline, ancient channel, or period-specific marsh boundary is drawn or implied by these data.

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

`docs/data/coastline.geojson` includes every GSHHG land, lake, island-in-lake, and pond feature intersecting the frame, including small Persian Gulf islands. It contains **232 features and 34,294 output vertices**. There are 34,289 original vertices inside the frame; the small difference arises from clipping intersections and ring closures. Features retain their source ID, hierarchical level, container ID, and river-lake flag. Draw levels in order: land (1), water (2), land (3), water (4). The frame boundary closes clipped land polygons and must not be styled as an actual coastline.

## Rivers

`docs/data/rivers.geojson` comes from **`wdb_rivers_f.b`**, the full-resolution CIA World Data Bank II river lineaments bundled with the same original GSHHG archive. It has **215 features and 21,424 output vertices** in the frame. This includes the Tigris, Euphrates, Shatt al-Arab, tributaries, river-lakes, canals, and intermittent streams. The source does not supply river names; source IDs and classifications are preserved rather than inventing names in the data.

The WDBII lineage is older and less accurate than the WVS ocean coastline. These channels are a modern reference network compiled from older mapping, **not a current hydrographic survey** and **not ancient Sumerian or Babylonian waterways**. This limitation is explicitly stated in the GSHHG README. A wide river stored as a river-lake can appear as a closed outline. The extraction also retains 17 point/multipoint results from source line records that collapse geometrically; renderers should skip zero-dimensional river geometry. These are not added geographic claims.

River classes used by this extract are documented in [the official GMT `gshhg` manual](https://docs.generic-mapping-tools.org/6.5/supplements/gshhg/gshhg.html). Levels 0–4 are river-lakes and permanent rivers; 6–8 are intermittent rivers; 10–12 are canal classes. A renderer can omit minor channels for legibility, but should not change the original coastline geometry.

## Southern marshes

`docs/data/marsh-labels.geojson` contains **three factual label anchors**, using the published center coordinates of the Iraqi Ramsar Sites: Central Marshes (2241), Hammar Marsh (2242), and Hawizeh Marsh (1718). These anchors are suitable for placing regional labels. They are **not wetland outlines, exact ecological centroids, or ancient extents**. No inferred marsh polygon is included. The Central and Hammar sites were designated in 2014 and Hawizeh in 2007; the labels refer to modern named wetlands.

- [Central Marshes, Ramsar Site 2241](https://rsis.ramsar.org/ris/2241): 31°10′34″ N, 46°59′ E.
- [Hammar Marsh, Ramsar Site 2242](https://rsis.ramsar.org/ris/2242): 30°48′22″ N, 47°01′01″ E.
- [Hawizeh Marsh, Ramsar Site 1718](https://rsis.ramsar.org/ris/1718): 31°25′ N, 47°37′59″ E.

The official Ramsar site descriptions identify these three areas as the southern Mesopotamian marshland complex. Their histories include drainage and reflooding; modern extents should not be extrapolated into antiquity. Only individual published coordinate facts and newly authored notes are redistributed here, not the Ramsar site's downloadable boundary database, photographs, or text.

## Ancient-site points

The 25 candidate archaeological-site anchors in `docs/data/cities.json` were selected from the Pleiades GIS `places.csv` distribution downloaded on 18 October 2026. Only 22 appear as poster callouts. Each selected point retains its individual canonical Pleiades URL, gazetteer title and precision classification. The CSV member's SHA-256 and retrieval URL are in `docs/data/site-provenance.json`. These are representative points for archaeological sites or complexes, not exact temple, myth-event or birth coordinates. Older ORACC gazetteer snapshots sometimes differ; the selected current Pleiades distribution is used consistently here. Other named sites remain null where location or identification is insufficiently secure. Pleiades contributors' data are licensed CC BY 3.0.

The poster uses a local equirectangular projection with 480 pixels per longitude degree and 565 per latitude degree (approximately cos 31.8° longitude scaling), north up. The scale bar is approximate at 31° N. Scene clipping affects only the displayed frame; it does not further simplify the original coastal vertices.

## License and attribution

GSHHG 2.3.7 is distributed under the **GNU Lesser General Public License, version 3 or any earlier version**, as the release's LICENSE states. The derived GeoJSON retains that upstream license. The original license, LGPL text, and README are included in `docs/data/GSHHG-LICENSE.txt`, `GSHHG-COPYING.LESSERv3.txt`, and `GSHHG-README.txt`. The atlas's own license does not replace these upstream terms.

Suggested compact credit: **Modern reference coast: GSHHG 2.3.7, full resolution (Wessel & Smith); rivers: WDBII/GSHHG; marsh labels: Ramsar RSIS. Ancient shorelines and channels varied.**

Machine-readable extraction counts, input hashes, output hashes, and clipping parameters are in `docs/data/geography-manifest.json`. To regenerate, install Shapely and run `python scripts/build-geography.py --archive PATH_TO_gshhg-bin-2.3.7.zip`; omit `--archive` to fetch the official release. The original 118 MB global archive is intentionally not duplicated in the public repository.
