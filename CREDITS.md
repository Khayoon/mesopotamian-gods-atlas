# Credits and licenses

## Research

New research summaries, layout, rendering and companion code were prepared for this project on 18 October 2026. Ancient narratives are paraphrased; full copyrighted modern translations are not redistributed. Links lead to their editors and institutions. The short textual quotations in the poster are ancient temple names in translation.

- **The Electronic Text Corpus of Sumerian Literature (ETCSL), University of Oxford**: Jeremy Black, Graham Cunningham, Eleanor Robson, Gábor Zólyomi and the ETCSL team. The ancient compositions include *The Temple Hymns*, *Enlil and Ninlil*, *Enlil and Sud*, *Enki and Ninhursanga*, *Enki and Ninmah*, the Gudea Cylinders, deity hymns, and royal hymns. Exact work numbers and passages appear on each claim in `docs/data/research.json`. [ETCSL credits and copyright](https://etcsl.orinst.ox.ac.uk/edition2/credits.php).
- **ORACC: Ancient Mesopotamian Gods and Goddesses (AMGG)**, edited by the project team with individual specialist contributors, and its cited Assyriological literature. [Deity index](https://oracc.museum.upenn.edu/amgg/Listofdeities/index.html). Individual articles, authors and URLs are retained in the data when consulted.
- **ORACC ETCSRI, RIBo, RINAP, SAA and related corpora**: scholarly editions of royal inscriptions and primary texts. Catalogue identifiers, passage references and period metadata are retained per claim. [ORACC](https://oracc.museum.upenn.edu/). ORACC projects retain their own licensing and attribution requirements; newly written factual summaries here do not replace or relicense their translations.
- **W. G. Lambert**, translation of *Enuma Elish*, accessible through [ETANA's source record](https://etana.org/node/581/index.html); see also Lambert, *Babylonian Creation Myths* (Eisenbrauns, 2013) for a modern critical treatment. Tablet I's genealogy and Apsu birth are kept unlocated.
- **Dina Katz**, “Enki and Ninhursaga, Part One,” *Bibliotheca Orientalis* 64 (2007), especially pp. 569–572. [Accessible author copy](https://www.researchgate.net/profile/Dina-Katz-2/publication/315216135_Enki_and_Ninhursaga_Part_One/links/6384b80d554def61937e73a4/Enki-and-Ninhursaga-Part-One.pdf). Her argument that the opening Dilmun story and later southern-marsh story have different settings is represented as scholarly interpretation, not silently imposed as textual certainty.
- **Deena Ragavan**, “Cuneiform Texts and Fragments in the Harvard Art Museum / Arthur M. Sackler Museum,” *Cuneiform Digital Library Journal* 2010:1, §3.1.1, for Enmetena's foundation inscription involving Shul-utula. [CDLJ article](https://cdli.earth/articles/cdlj/2010-1.pdf). The object is Harvard 2000.274, from Bad-tibira; the named ruler is of Lagash. The map therefore labels a dynastic protective association, not an exclusive local cult or birthplace.

## Geography

- **Paul Wessel and Walter H. F. Smith, GSHHG 2.3.7**: original `gshhs_f.b` full-resolution coastlines and bundled WDBII rivers. No additional simplification. Derived regional GeoJSON retains the upstream LGPL terms. The source LICENSE, LGPLv3 text and README are bundled. Full attribution, exact input/output hashes and clipping details: [GEO-PROVENANCE.md](GEO-PROVENANCE.md).
- **Pleiades contributors**: archaeological-site representative points, from the [Pleiades GIS distribution](https://atlantides.org/downloads/pleiades/gis/). Each point includes its individual canonical Pleiades URL. Pleiades data are shared under [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/). Points were selected, renamed for readable ancient city labels, and reprojected; they are not exact temple or myth-event locations. Some current representative points differ from older ORACC gazetteer snapshots.
- **Ramsar Sites Information Service**: three published marsh-site coordinate facts and names. No Ramsar boundary database, imagery, or copyrighted site descriptions are redistributed. See provenance for the individual site citations.

## Typography and project licensing

**Gentium Plus**, SIL International, is used under the SIL Open Font License 1.1. Its regular and bold fonts and complete license are in `docs/vendor/`. No AI-generated pictorial assets are used.

The project's original code is released under MIT; the newly authored research summaries, composition and poster are licensed under CC BY 4.0. Upstream geography, fonts, source texts and third-party scholarship retain their own licenses. A license to this project's summaries does not grant rights to republish the linked modern translations.
