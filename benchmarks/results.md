# Cartoblend Performance — Benchmark Report

Two complementary benchmarks document the speedup the fork delivers
relative to its upstream parent project, **BlenderGIS**
(`domlysz/BlenderGIS`).

---

## A. Live end-to-end pipeline (in Blender)

The **real** Map Viewer workflow: load a Munich centre bbox at zoom 14
(24 OSM Mapnik tiles) through `MapService.getImage()`. Best of 3 runs.

Compared revisions:
- **Initial fork** (`9d08732`) — first commit after fork, with only the
  minimal Blender 5.x compatibility patches needed to run at all.
  Performance-wise effectively still upstream BlenderGIS.
- **Current** (`dc305cb`) — head of `main` after the security and
  performance audit sweeps.

| Pipeline phase | Initial fork | Current | Speedup |
|---|---:|---:|---:|
| **Cold** (HTTP fetch + cache write + decode + mosaic build) | 824 ms | 154 ms | **5.35×** |
| **Warm** (cache read + decode + mosaic build, no network) | 17.1 ms | 7.6 ms | **2.25×** |
| **Warm 2nd run** (decode-cache hit + mosaic only) | 17.3 ms | 7.3 ms | **2.37×** |

```
Cold   (HTTP fetch + decode + mosaic)   █████████████████████████████  5.35×
Warm   (DB read + decode + mosaic)      ████████████                   2.25×
Warm²  (decode-cache hit + mosaic)      █████████████                  2.37×
```

What's compounding here: HTTP connection pool, parallel PNG decode
(`ThreadPoolExecutor`), enlarged decode LRU cache, center-out tile
ordering, cached SQLite connections, faster `paste()` fast-path,
synchronous=OFF on the cache DB.

To reproduce, see [`live_blender_bench.py`](live_blender_bench.py).

---

## B. Standalone module benchmark (no Blender needed)

Five modules that don't depend on `bpy`, run as a regular Python
script. Same workloads against both the upstream code and the fork.

| Workflow | Upstream | Fork | Speedup |
|---|---:|---:|---:|
| OSM XML parser (50k nodes / 5k ways) | 215 ms | 172 ms | **1.25×** |
| Tile cache streaming (pan workload, 2000 tiles) | 66 ms | 37 ms | **1.78×** |
| PNG decode pipeline (64 tiles, 256×256) | 36 ms | 10 ms | **3.66×** |
| DEM hole-filling (500×500, 30% NaN, 5 iter) | 4.29 s | 15 ms | **280×** |
| Voronoi point dedup (50k points, 30% dupes) | 35 ms | 17 ms | **2.08×** |

```
OSM XML parser (50k nodes / 5k ways)    █                                1.25×
Tile cache streaming (pan workload)     ███                              1.78×
PNG decode pipeline (64 tiles)          ██████                           3.66×
DEM hole-filling (500x500, 30% NaN)     ██████████████████████████████ 280.24×
Voronoi point dedup (50k points)        ███                              2.08×
```

To reproduce:
```bash
git clone --depth 1 https://github.com/domlysz/BlenderGIS.git /tmp/blendergis-orig
python3 benchmarks/run_benchmark.py
```

---

## Environment

- Python: `3.14.4`
- NumPy: `2.4.4`
- CPU cores: 16
- Blender: 5.2 Alpha
- Network: home WAN (cold runs measured after DNS/TCP warm-up to remove first-connection setup noise)

## Methodology

- Best of N runs (lower bound; noise-resistant against scheduler/IO/network jitter).
- Cold-cache runs wipe `<source>*.gpkg*` between iterations to force HTTP fetch.
- Warm runs reuse the populated cache.
- Same `MapService` API call (`getImage`) on both versions for the live bench.
- Standalone bench imports the two codebases as distinct Python modules
  in the same interpreter.

## Not measured

ASC/GeoTIFF DEM import, `exportAsMesh`, Map Viewer pan UX latency,
Geometry Nodes modifier setup, custom-providers UI panel — these are
also faster (per audit estimates 10–100× for some) but require a
live UI workflow that's harder to automate.
