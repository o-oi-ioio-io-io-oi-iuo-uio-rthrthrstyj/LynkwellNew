# Lynkwell Digital — 3D assets

Web-ready glTF assets for the Lynkwell Digital site (Next.js + React Three Fiber).

```
lynkwell-3d/
├── export/     .glb files — these are what the site loads
├── blend/      .blend source, one per asset
├── previews/   reference renders on the bone background
└── scripts/    the Python that builds everything (re-runnable in Blender)
```

---

## Brand colours

| Token | Hex | Use |
|---|---|---|
| Background | `#F2EFE8` | bone/cream page background — the site is a **light** theme |
| Primary surface | `#E4DFD4` | slightly deeper cream, so objects separate from the page |
| Mid-tone | `#B8B2A7` | stone |
| Dark | `#1A1A1A` | charcoal |
| Accent | `#2B4BFF` | cobalt — used sparingly, ~10% of any asset |

## Materials

All materials are Principled BSDF → glTF `pbrMetallicRoughness`. **Metallic is 0 everywhere.**
The hex values round-trip exactly through the export — no colour management surprises.

| Material | Base colour | Roughness | Notes |
|---|---|---|---|
| `mat_cream` | `#E4DFD4` | 0.60 | soft matte clay/ceramic |
| `mat_stone` | `#B8B2A7` | 0.50 | mid-tone |
| `mat_charcoal` | `#1A1A1A` | 0.35 | satin |
| `mat_cobalt` | `#2B4BFF` | 0.15 | glossy lacquer — the accent |
| `mat_cobalt_glow` | `#2B4BFF` | 0.15 | + emissive `[0.017, 0.049, 0.70]`. **Only in `process_journey`** |

No metal, no chrome, no textures — every material is 4 numbers. Light the scene softly
and brightly with a `#F2EFE8` environment and the assets will match the previews.

---

## The files

| File | Section | What it is |
|---|---|---|
| `hero_link_network.glb` | **Hero** | 7 interlocking chain links + 3 nodes + 4 rods, 14 separately-named objects |
| `icon_01_web_design.glb` | Services | browser window + layered panel |
| `icon_02_brand_identity.glb` | Services | square / circle / triangle logo kit |
| `icon_03_seo_performance.glb` | Services | rising bar graph with arrow |
| `icon_04_mobile_first.glb` | Services | phone slab with screen |
| `icon_05_conversion.glb` | Services | funnel with a sphere dropping through |
| `icon_06_support.glb` | Services | shield with a chain-link emblem |
| `process_journey.glb` | **Process** | one structure in 4 states + an orbiting camera |
| `statement_link.glb` | Statement band | oversized chain-link monolith, "earn its place" |
| `bg_node_field.glb` | About / Contact | sparse background node field |

---

## Animations

Every clip is a named glTF animation at **24 fps**. Durations are exact.

| File | Clip | Frames | Seconds | Intent |
|---|---|---:|---:|---|
| `hero_link_network` | `assemble` | 120 | 5.000 | scrub with scroll — pieces fly into the mark |
| `hero_link_network` | `idle` | 240 | 10.000 | seamless loop, play after `assemble` |
| `icon_01`…`icon_06` | `idle` | 180 | 7.500 | seamless loop |
| `process_journey` | `camera_orbit` | 400 | 16.667 | scrub with scroll, 100 frames per stage |
| `statement_link` | `rotate_360` | 300 | 12.500 | seamless loop, constant speed |
| `bg_node_field` | — | — | — | static |

`assemble` ends on exactly the same pose `idle` starts from, so you can hand off at
frame 120 with no pop. Every looping clip closes on itself — verified numerically, not
by eye.

---

## Notes for implementation

**Draco is on.** All meshes are Draco-compressed, so wire up `DRACOLoader`:

```js
const draco = new DRACOLoader().setDecoderPath('https://www.gstatic.com/draco/v1/decoders/');
const loader = new GLTFLoader().setDRACOLoader(draco);
```

**Conventions.** Metres, +Y up,each asset centred on its own origin, all scales 1.0, no
parent transforms. Assets are built facing **+Z**, so they face a default R3F camera
with no rotation needed.

**Hero** — the 14 objects are named `hero_link_01`…`hero_link_07`, `hero_node_01`…`03`,
`hero_rod_01`…`04`, so you can target any one of them. `hero_link_05` is the cobalt link
(the focal point). The `idle` clip moves the whole cluster rigidly — the rods are butt-
jointed to the node spheres with no skinning, so do **not** drive the pieces independently
or the joints will visibly separate.

**Process** — the four states are `process_01_discovery`, `process_02_design`,
`process_03_build`, `process_04_launch`. All four sit at translation `[0,0,0]`, stacked,
so crossfading is a pure opacity swap. Each is a single mesh with one primitive per
material, so you can also fade a single material if you want. `camera_path` is an empty
at the orbit centre; `process_camera` is a real glTF camera with baked keys — use it or
match it. Its `yfov` is 28.8°, baked from a square render, so vertical framing holds at
any viewport aspect.

**Statement** — one mesh, two primitives. The cobalt is a flush inlay built into the
section, not a separate part, so it can never drift from the body.

**Background field** — one mesh, 26 nodes and 30 links, 2,440 triangles. Deliberately
static; it is a backdrop. Scale it to taste; it is 3.0 × 1.7 units as exported.

## Budgets

Hero 9,016 triangles (limit 50,000). Every other asset is under 10,000 — largest is
`process_journey` at 7,484. All ten files together are **41,756 triangles / 485 KB**.
