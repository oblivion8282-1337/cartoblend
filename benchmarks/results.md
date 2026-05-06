# Cartoblend vs Upstream BlenderGIS — Performance Benchmark

Standalone end-to-end benchmark — runs the modules that don't
need bpy. Each row compares the same input against the original
BlenderGIS code (`domlysz/BlenderGIS`) and the current fork.


| Workflow | Original | Fork | Speedup |
|---|---:|---:|---:|
| OSM XML parser (50k nodes / 5k ways) | 215.3 ms | 172.5 ms | **1.25×** |
| Tile cache streaming (pan workload, 2000 tiles) | 66.0 ms | 37.1 ms | **1.78×** |
| PNG decode pipeline (64 tiles, 256x256) | 35.9 ms | 9.8 ms | **3.66×** |
| DEM hole-filling (500x500, 30% NaN, 5 iter) | 4.29 s | 15.3 ms | **280.24×** |
| Voronoi point dedup (50k points, 30% dupes) | 35.2 ms | 16.9 ms | **2.08×** |

## Visual

```
OSM XML parser (50k nodes / 5k ways)    █                                1.25×
Tile cache streaming (pan workload, 20  ███                              1.78×
PNG decode pipeline (64 tiles, 256x256  ██████                           3.66×
DEM hole-filling (500x500, 30% NaN, 5   ██████████████████████████████ 280.24×
Voronoi point dedup (50k points, 30% d  ███                              2.08×
```

## Environment

- Python: `3.14.4`
- NumPy: `2.4.4`
- CPU cores: 16

## Methodology

Each benchmark runs 2-3 times; the fastest sample is reported
(noise-resistant lower bound). Inputs are deterministic
(seeded RNG) so results are reproducible.

**Not measured:** anything that needs Blender's `bpy` —
ASC/DEM mesh import, Map Viewer pan UX, Geometry Nodes
modifier setup. Those are also significantly faster but
require a live Blender session to time.