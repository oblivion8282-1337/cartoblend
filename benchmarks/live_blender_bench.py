"""End-to-end Blender benchmark — measures the actual tile loading pipeline
through MapService.getImage() in a live Blender session.

Run inside Blender (e.g. via the MCP `execute_blender_code` tool, the
Scripting workspace, or `blender --python ...`):

    exec(open('benchmarks/live_blender_bench.py').read())
    print(result)

Three measurements per version:
  - Cold: HTTP fetch + cache write + decode + mosaic build
  - Warm: cache read + decode + mosaic build (no network)
  - Warm2: second warm run (decode cache hit + mosaic only)

Each is averaged across N_RUNS cold-cache iterations (Munich centre, 24
OSM Mapnik tiles at zoom 14).

To compare against another commit, swap the installed addon files,
reload the addon, and re-run this script. Numbers used in
`results.md` were collected by running this on:
  - 9d08732 (initial fork commit, ~ original BlenderGIS state)
  - dc305cb (current head)
"""
import math, os, glob, time, importlib

PKG = 'bl_ext.user_default.cartoblend'
ms_mod = importlib.import_module(PKG + '.core.basemaps.mapservice')
MapService = ms_mod.MapService

import bpy
addon = bpy.context.preferences.addons[PKG]
cacheFolder = addon.preferences.cacheFolder

def lonlat_to_wm(lon, lat):
    x = lon * 20037508.34 / 180.0
    y = math.log(math.tan((90.0 + lat) * math.pi / 360.0)) * 20037508.34 / math.pi
    return x, y

# Munich Marienplatz, 3x3 visible tiles at zoom 14 (covers ~24 internal tiles)
LON_C, LAT_C = 11.5755, 48.1374
HALF = 0.033
xmin, ymin = lonlat_to_wm(LON_C - HALF, LAT_C - HALF)
xmax, ymax = lonlat_to_wm(LON_C + HALF, LAT_C + HALF)
BBOX = (xmin, ymin, xmax, ymax)
ZOOM = 14
SRC, LAY = 'OSM', 'MAPNIK'
N_RUNS = 3

def wipe_cache():
    """Cache filename can be `OSM.gpkg` or `OSM_MAPNIK_WM.gpkg` depending on
    the version under test, so wipe broadly."""
    for pat in [f'{SRC}*.gpkg*', f'*{LAY}*.gpkg*']:
        for p in glob.glob(os.path.join(cacheFolder, pat)):
            try: os.remove(p)
            except OSError: pass

cold_runs, warm_runs, warm2_runs = [], [], []
for i in range(N_RUNS):
    wipe_cache()
    ms = MapService(SRC, cacheFolder)
    ms.start()

    t0 = time.perf_counter()
    ms.getImage(LAY, BBOX, ZOOM, toDstGrid=False)
    cold_runs.append(time.perf_counter() - t0)

    t0 = time.perf_counter()
    ms.getImage(LAY, BBOX, ZOOM, toDstGrid=False)
    warm_runs.append(time.perf_counter() - t0)

    t0 = time.perf_counter()
    ms.getImage(LAY, BBOX, ZOOM, toDstGrid=False)
    warm2_runs.append(time.perf_counter() - t0)

    ms.stop()

result = {
    'cold_runs_ms':  [round(x*1000, 1) for x in cold_runs],
    'warm_runs_ms':  [round(x*1000, 1) for x in warm_runs],
    'warm2_runs_ms': [round(x*1000, 1) for x in warm2_runs],
    'cold_min_ms':   round(min(cold_runs)*1000, 1),
    'warm_min_ms':   round(min(warm_runs)*1000, 1),
    'warm2_min_ms':  round(min(warm2_runs)*1000, 1),
}
print(result)
