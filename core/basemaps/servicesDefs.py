# -*- coding:utf-8 -*-

import math

####################################

#        Tiles maxtrix definitions

####################################

# Three ways to define a grid (inpired by http://mapproxy.org/docs/1.8.0/configuration.html#id6):
# - submit a list of resolutions > "resolutions": [32,16,8,4] (This parameters override the others)
# - submit just "resFactor", initial res is computed such as at zoom level zero, 1 tile covers whole bounding box
# - submit "resFactor" and "initRes"


# About Web Mercator
# Technically, the Mercator projection is defined for any latitude up to (but not including)
# 90 degrees, but it makes sense to cut it off sooner because it grows exponentially with
# increasing latitude. The logic behind this particular cutoff value, which is the one used
# by Google Maps, is that it makes the projection square. That is, the rectangle is equal in
# the X and Y directions. In this case the maximum latitude attained must correspond to y = w/2.
# y = 2*pi*R / 2 = pi*R --> y/R = pi
# lat = atan(sinh(y/R)) = atan(sinh(pi))
# wm_origin = (-20037508, 20037508) with 20037508 = GRS80.perimeter / 2

cutoff_lat = math.atan(math.sinh(math.pi)) * 180/math.pi #= 85.05112°


GRIDS = {


	"WM" : {
		"name" : 'Web Mercator',
		"description" : 'Global grid in web mercator projection',
		"CRS": 'EPSG:3857',
		"bbox": [-180, -cutoff_lat, 180, cutoff_lat], #w,s,e,n
		"bboxCRS": 'EPSG:4326',
		#"bbox": [-20037508, -20037508, 20037508, 20037508],
		#"bboxCRS": 3857,
		"tileSize": 256,
		"originLoc": "NW", #North West or South West
		"resFactor" : 2
	},


	"WGS84" : {
		"name" : 'WGS84',
		"description" : 'Global grid in wgs84 projection',
		"CRS": 'EPSG:4326',
		"bbox": [-180, -90, 180, 90], #w,s,e,n
		"bboxCRS": 'EPSG:4326',
		"tileSize": 256,
		"originLoc": "NW", #North West or South West
		"resFactor" : 2
	},

	#this one produce valid MBtiles files, because origin is bottom left
	"WM_SW" : {
		"name" : 'Web Mercator TMS',
		"description" : 'Global grid in web mercator projection, origin South West',
		"CRS": 'EPSG:3857',
		"bbox": [-180, -cutoff_lat, 180, cutoff_lat], #w,s,e,n
		"bboxCRS": 'EPSG:4326',
		#"bbox": [-20037508, -20037508, 20037508, 20037508],
		#"bboxCRS": 'EPSG:3857',
		"tileSize": 256,
		"originLoc": "SW", #North West or South West
		"resFactor" : 2
	},


	#####################
	#Custom grid example
	######################

	# >> France Lambert 93
	"LB93" : {
		"name" : 'Fr Lambert 93',
		"description" : 'Local grid in French Lambert 93 projection',
		"CRS": 'EPSG:2154',
		"bbox": [99200, 6049600, 1242500, 7110500], #w,s,e,n
		"bboxCRS": 'EPSG:2154',
		"tileSize": 256,
		"originLoc": "NW", #North West or South West
		"resFactor" : 2
	},

	# >> Another France Lambert 93 (submited list of resolution)
	"LB93_2" : {
		"name" : 'Fr Lambert 93 v2',
		"description" : 'Local grid in French Lambert 93 projection',
		"CRS": 'EPSG:2154',
		"bbox": [99200, 6049600, 1242500, 7110500], #w,s,e,n
		"bboxCRS": 'EPSG:2154',
		"tileSize": 256,
		"originLoc": "SW", #North West or South West
		"resolutions" : [4000, 2000, 1000, 500, 250, 100, 50, 25, 10, 5, 2, 1, 0.5, 0.25, 0.1] #15 levels
	},


	# >> France Lambert 93 used by CRAIG WMTS
	# WMTS resolution = ScaleDenominator * 0.00028
	# (0.28 mm = physical distance of a pixel (WMTS assumes a DPI 90.7)
	"LB93_CRAIG" : {
		"name" : 'Fr Lambert 93 CRAIG',
		"description" : 'Local grid in French Lambert 93 projection',
		"CRS": 'EPSG:2154',
		"bbox": [-357823.23, 6037001.46, 1313634.34, 7230727.37], #w,s,e,n
		"bboxCRS": 'EPSG:2154',
		"tileSize": 256,
		"originLoc": "NW",
		"initRes": 1354.666,
		"resFactor" : 2
	},

}


####################################

#        Sources definitions

####################################

#With TMS or WMTS, grid must match the one used by the service
#With WMS you can use any grid you want but the grid CRS must
#match one of those provided by the WMS service

#The grid associated to the source define the CRS
#A source can have multiple layers but have only one grid
#so to support multiple grid it's necessary to duplicate source definition

SOURCES = {


	###############
	# TMS examples
	###############


	"GOOGLE" : {
		"name" : 'Google',
		"description" : 'Google map',
		"service": 'TMS',
		"grid": 'WM',
		"quadTree": False,
		"layers" : {
			"SAT" : {"urlKey" : 's', "name" : 'Satellite', "description" : '', "format" : 'jpeg', "zmin" : 0, "zmax" : 22},
			"MAP" : {"urlKey" : 'm', "name" : 'Map', "description" : '', "format" : 'png', "zmin" : 0, "zmax" : 22}
		},
		"urlTemplate": "https://mt0.google.com/vt/lyrs={LAY}&x={X}&y={Y}&z={Z}",
		"referer": "https://www.google.com/maps"
	},


	"OSM" : {
		"name" : 'OSM',
		"description" : 'Open Street Map',
		"service": 'TMS',
		"grid": 'WM',
		"quadTree": False,
		"layers" : {
			"MAPNIK" : {"urlKey" : '', "name" : 'Mapnik', "description" : '', "format" : 'png', "zmin" : 0, "zmax" : 19}
		},
		"urlTemplate": "https://tile.openstreetmap.org/{Z}/{X}/{Y}.png",
		"referer": "" #https://www.openstreetmap.org will return 418 error
	},


	"BING" : {
		"name" : 'Bing',
		"description" : 'Microsoft Bing Map',
		"service": 'TMS',
		"grid": 'WM',
		"quadTree": True,
		"layers" : {
			"SAT" : {"urlKey" : 'A', "name" : 'Satellite', "description" : '', "format" : 'jpeg', "zmin" : 0, "zmax" : 22},
			"MAP" : {"urlKey" : 'G', "name" : 'Map', "description" : '', "format" : 'png', "zmin" : 0, "zmax" : 22}
		},
		"urlTemplate": "https://ak.dynamic.t0.tiles.virtualearth.net/comp/ch/{QUADKEY}?it={LAY}",
		"referer": "https://www.bing.com/maps"
	},


	"ESRI" : {
		"name" : 'Esri',
		"description" : 'Esri ArcGIS',
		"service": 'TMS',
		"grid": 'WM',
		"quadTree": False,
		"layers" : {
			"AERIAL" : {"urlKey" : 'World_Imagery', "name" : 'Aerial', "description" : '', "format" : 'jpeg', "zmin" : 0, "zmax" : 23},
			"NATGEO" : {"urlKey" : 'NatGeo_World_Map', "name" : 'National Geographic', "description" : '', "format" : 'jpeg', "zmin" : 0, "zmax" : 16},
			"USATOPO" : {"urlKey" : 'USA_Topo_Maps', "name" : 'USA Topo', "description" : '', "format" : 'jpeg', "zmin" : 0, "zmax" : 15},
			"PHYSICAL" : {"urlKey" : 'World_Physical_Map', "name" : 'Physical', "description" : '', "format" : 'jpeg', "zmin" : 0, "zmax" : 8},
			"RELIEF" : {"urlKey" : 'World_Shaded_Relief', "name" : 'Shaded Relief', "description" : '', "format" : 'jpeg', "zmin" : 0, "zmax" : 13},
			"STREET" : {"urlKey" : 'World_Street_Map', "name" : 'Street Map', "description" : '', "format" : 'jpeg', "zmin" : 0, "zmax" : 23},
			"TOPO" : {"urlKey" : 'World_Topo_Map', "name" : 'Topo with relief', "description" : '', "format" : 'jpeg', "zmin" : 0, "zmax" : 23},
			"TERRAINB" : {"urlKey" : 'World_Terrain_Base', "name" : 'Terrain Base', "description" : '', "format" : 'jpeg', "zmin" : 0, "zmax" : 13},
			"CANVASLIGHTB" : {"urlKey" : 'Canvas/World_Light_Gray_Base', "name" : 'Canvas Light Gray Base', "description" : '', "format" : 'jpeg', "zmin" : 0, "zmax" : 23},
			"CANVASDARKB" : {"urlKey" : 'Canvas/World_Dark_Gray_Base', "name" : 'Canvas Dark Gray Base', "description" : '', "format" : 'jpeg', "zmin" : 0, "zmax" : 23},
			"OCEANB" : {"urlKey" : 'Ocean/World_Ocean_Base', "name" : 'Ocean Base', "description" : '', "format" : 'jpeg', "zmin" : 0, "zmax" : 23}
		},
		"urlTemplate": "https://server.arcgisonline.com/ArcGIS/rest/services/{LAY}/MapServer/tile/{Z}/{Y}/{X}",
		"referer": "https://server.arcgisonline.com/arcgis/rest/services"
	},


	# EOX Sentinel-2 2016: CC BY 4.0 — free for commercial use (film, etc.)
	"EOX_S2_FREE" : {
		"name" : 'EOX Sentinel-2 (commercial OK)',
		"description" : 'Sentinel-2 cloudless 2016 by EOX — CC BY 4.0, free for commercial use',
		"service": 'TMS',
		"grid": 'WM',
		"quadTree": False,
		"layers" : {
			"S2_2016" : {"urlKey" : 's2cloudless_3857', "name" : '2016 (CC BY 4.0)', "description" : 'Sentinel-2 cloudless 2016 — commercial use OK with attribution', "format" : 'jpeg', "zmin" : 0, "zmax" : 17}
		},
		"urlTemplate": "https://tiles.maps.eox.at/wmts/1.0.0/{LAY}/default/g/{Z}/{Y}/{X}.jpg",
		"referer": "https://s2maps.eu"
	},


	# EOX Sentinel-2 2018-2024: CC BY-NC-SA 4.0 — NON-COMMERCIAL only
	"EOX_S2" : {
		"name" : 'EOX Sentinel-2 (non-commercial)',
		"description" : 'Sentinel-2 cloudless by EOX — CC BY-NC-SA 4.0, non-commercial only',
		"service": 'TMS',
		"grid": 'WM',
		"quadTree": False,
		"layers" : {
			"S2_2024" : {"urlKey" : 's2cloudless-2024_3857', "name" : '2024', "description" : 'Sentinel-2 cloudless 2024 (non-commercial)', "format" : 'jpeg', "zmin" : 0, "zmax" : 17},
			"S2_2023" : {"urlKey" : 's2cloudless-2023_3857', "name" : '2023', "description" : 'Sentinel-2 cloudless 2023 (non-commercial)', "format" : 'jpeg', "zmin" : 0, "zmax" : 17},
			"S2_2022" : {"urlKey" : 's2cloudless-2022_3857', "name" : '2022', "description" : 'Sentinel-2 cloudless 2022 (non-commercial)', "format" : 'jpeg', "zmin" : 0, "zmax" : 17},
			"S2_2021" : {"urlKey" : 's2cloudless-2021_3857', "name" : '2021', "description" : 'Sentinel-2 cloudless 2021 (non-commercial)', "format" : 'jpeg', "zmin" : 0, "zmax" : 17},
			"S2_2020" : {"urlKey" : 's2cloudless-2020_3857', "name" : '2020', "description" : 'Sentinel-2 cloudless 2020 (non-commercial)', "format" : 'jpeg', "zmin" : 0, "zmax" : 17},
			"S2_2019" : {"urlKey" : 's2cloudless-2019_3857', "name" : '2019', "description" : 'Sentinel-2 cloudless 2019 (non-commercial)', "format" : 'jpeg', "zmin" : 0, "zmax" : 17},
			"S2_2018" : {"urlKey" : 's2cloudless-2018_3857', "name" : '2018', "description" : 'Sentinel-2 cloudless 2018 (non-commercial)', "format" : 'jpeg', "zmin" : 0, "zmax" : 17}
		},
		"urlTemplate": "https://tiles.maps.eox.at/wmts/1.0.0/{LAY}/default/g/{Z}/{Y}/{X}.jpg",
		"referer": "https://s2maps.eu"
	},


	# Copernicus CDSE: Sentinel-2 via Process API — free for commercial use
	# Requires free registration at dataspace.copernicus.eu + OAuth2 credentials in preferences
	"CDSE_S2" : {
		"name" : 'Copernicus Sentinel-2 (commercial OK)',
		"description" : 'Sentinel-2 L2A via CDSE Process API — free for commercial use, updated every 2-3 days',
		"service": 'CDSE',
		"grid": 'WM',
		"quadTree": False,
		"layers" : {
			"TRUE_COLOR" : {"urlKey" : 'sentinel-2-l2a', "name" : 'True Color (latest)', "description" : 'Most recent low-cloud Sentinel-2 image — commercial use OK', "format" : 'jpeg', "zmin" : 7, "zmax" : 14},
			"MOSAIC_Q" : {"urlKey" : 'byoc-5460de54-082e-473a-b6ea-d5cbe3c17cca', "name" : 'Quarterly Cloudless Mosaic', "description" : 'Cloud-free quarterly composite — commercial use OK', "format" : 'jpeg', "zmin" : 7, "zmax" : 14}
		},
		"urlTemplate": "https://sh.dataspace.copernicus.eu/api/v1/process",
		"referer": "https://dataspace.copernicus.eu"
	},


	# NASA GIBS: public domain — free for any use including commercial
	"NASA_GIBS" : {
		"name" : 'NASA GIBS (commercial OK)',
		"description" : 'NASA Global Imagery Browse Services — public domain, free for all use',
		"service": 'TMS',
		"grid": 'WM',
		"quadTree": False,
		"layers" : {
			"MODIS_TERRA" : {"urlKey" : 'MODIS_Terra_CorrectedReflectance_TrueColor', "name" : 'MODIS Terra True Color', "description" : 'Daily satellite imagery (250m) — public domain', "format" : 'jpeg', "zmin" : 0, "zmax" : 9},
			"MODIS_AQUA" : {"urlKey" : 'MODIS_Aqua_CorrectedReflectance_TrueColor', "name" : 'MODIS Aqua True Color', "description" : 'Daily satellite imagery (250m) — public domain', "format" : 'jpeg', "zmin" : 0, "zmax" : 9},
			"VIIRS" : {"urlKey" : 'VIIRS_SNPP_CorrectedReflectance_TrueColor', "name" : 'VIIRS SNPP True Color', "description" : 'Daily satellite imagery (250m) — public domain', "format" : 'jpeg', "zmin" : 0, "zmax" : 9}
		},
		"urlTemplate": "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/{LAY}/default/2024-06-15/GoogleMapsCompatible_Level9/{Z}/{Y}/{X}.jpg",
		"referer": "https://earthdata.nasa.gov"
	},


	# Spanish PNOA: CC BY 4.0 — free for commercial use, 25cm resolution
	# Covers all of Spain including Canary Islands, no API key required
	"PNOA" : {
		"name" : 'Spain PNOA (commercial OK)',
		"description" : 'Spanish national orthophotos 25cm — CC BY 4.0, free for commercial use',
		"service": 'WMTS',
		"grid": 'WM',
		"matrix" : 'GoogleMapsCompatible',
		"layers" : {
			"ORTHO" : {"urlKey" : 'OI.OrthoimageCoverage', "name" : 'Orthophotos', "description" : 'PNOA aerial orthophotos 25cm + Sentinel-2 at low zoom — CC BY 4.0',
				"format" : 'jpeg', "style" : 'default', "zmin" : 0, "zmax" : 20}
		},
		"urlTemplate": {
			"BASE_URL" : 'https://www.ign.es/wmts/pnoa-ma?',
			"SERVICE" : 'WMTS',
			"VERSION" : '1.0.0',
			"REQUEST" : 'GetTile',
			"LAYER" : '{LAY}',
			"STYLE" : '{STYLE}',
			"FORMAT" : 'image/{FORMAT}',
			"TILEMATRIXSET" : '{MATRIX}',
			"TILEMATRIX" : '{Z}',
			"TILEROW" : '{Y}',
			"TILECOL" : '{X}'
			},
		"referer": "https://www.ign.es"
	},


	"CARTO_LIGHT" : {
		"name" : 'CartoDB Positron',
		"description" : 'Light map style — CC BY 3.0',
		"service": 'TMS',
		"grid": 'WM',
		"quadTree": False,
		"layers" : {
			"LABELS" : {"urlKey" : 'light_all', "name" : 'With Labels', "description" : 'Light style with labels', "format" : 'png', "zmin" : 0, "zmax" : 20},
			"NOLABELS" : {"urlKey" : 'light_nolabels', "name" : 'No Labels', "description" : 'Light style without labels', "format" : 'png', "zmin" : 0, "zmax" : 20}
		},
		"urlTemplate": "https://basemaps.cartocdn.com/{LAY}/{Z}/{X}/{Y}.png",
		"referer": "https://carto.com"
	},


	"CARTO_DARK" : {
		"name" : 'CartoDB Dark Matter',
		"description" : 'Dark map style — CC BY 3.0',
		"service": 'TMS',
		"grid": 'WM',
		"quadTree": False,
		"layers" : {
			"LABELS" : {"urlKey" : 'dark_all', "name" : 'With Labels', "description" : 'Dark style with labels', "format" : 'png', "zmin" : 0, "zmax" : 20},
			"NOLABELS" : {"urlKey" : 'dark_nolabels', "name" : 'No Labels', "description" : 'Dark style without labels', "format" : 'png', "zmin" : 0, "zmax" : 20}
		},
		"urlTemplate": "https://basemaps.cartocdn.com/{LAY}/{Z}/{X}/{Y}.png",
		"referer": "https://carto.com"
	},


	"CARTO_VOYAGER" : {
		"name" : 'CartoDB Voyager',
		"description" : 'Colorful modern map style — CC BY 3.0',
		"service": 'TMS',
		"grid": 'WM',
		"quadTree": False,
		"layers" : {
			"LABELS" : {"urlKey" : 'rastertiles/voyager', "name" : 'With Labels', "description" : 'Voyager style with labels', "format" : 'png', "zmin" : 0, "zmax" : 20},
			"NOLABELS" : {"urlKey" : 'rastertiles/voyager_nolabels', "name" : 'No Labels', "description" : 'Voyager style without labels', "format" : 'png', "zmin" : 0, "zmax" : 20}
		},
		"urlTemplate": "https://basemaps.cartocdn.com/{LAY}/{Z}/{X}/{Y}.png",
		"referer": "https://carto.com"
	},


	"MAPBOX" : {
		"name" : 'Mapbox',
		"description" : 'Mapbox — free tier 200k static tile requests/month (registration required)',
		"service": 'TMS',
		"grid": 'WM',
		"quadTree": False,
		"layers" : {
			"SATELLITE" : {"urlKey" : 'mapbox/satellite-v9', "name" : 'Satellite', "description" : 'Global satellite and aerial imagery', "format" : 'jpg', "zmin" : 0, "zmax" : 22},
			"SAT_STREETS" : {"urlKey" : 'mapbox/satellite-streets-v12', "name" : 'Satellite Streets', "description" : 'Satellite imagery with street labels', "format" : 'jpg', "zmin" : 0, "zmax" : 22},
			"STREETS" : {"urlKey" : 'mapbox/streets-v12', "name" : 'Streets', "description" : 'Classic street map', "format" : 'png', "zmin" : 0, "zmax" : 22},
			"OUTDOORS" : {"urlKey" : 'mapbox/outdoors-v12', "name" : 'Outdoors', "description" : 'Trails, contours, outdoor features', "format" : 'png', "zmin" : 0, "zmax" : 22},
			"LIGHT" : {"urlKey" : 'mapbox/light-v11', "name" : 'Light', "description" : 'Light basemap for overlays', "format" : 'png', "zmin" : 0, "zmax" : 22},
			"DARK" : {"urlKey" : 'mapbox/dark-v11', "name" : 'Dark', "description" : 'Dark basemap for overlays', "format" : 'png', "zmin" : 0, "zmax" : 22},
			"NAV_DAY" : {"urlKey" : 'mapbox/navigation-day-v1', "name" : 'Navigation Day', "description" : 'Navigation-optimised day style', "format" : 'png', "zmin" : 0, "zmax" : 22},
			"NAV_NIGHT" : {"urlKey" : 'mapbox/navigation-night-v1', "name" : 'Navigation Night', "description" : 'Navigation-optimised night style', "format" : 'png', "zmin" : 0, "zmax" : 22}
		},
		"urlTemplate": "https://api.mapbox.com/styles/v1/{LAY}/tiles/256/{Z}/{X}/{Y}?access_token={MAPBOX_TOKEN}",
		"referer": "https://www.mapbox.com"
	},


	"MAPTILER" : {
		"name" : 'MapTiler',
		"description" : 'MapTiler — free tier 100k map loads/month, no credit card (registration required)',
		"service": 'TMS',
		"grid": 'WM',
		"quadTree": False,
		"layers" : {
			"SATELLITE" : {"urlKey" : 'satellite-v2', "name" : 'Satellite', "description" : 'Global satellite imagery', "format" : 'jpg', "zmin" : 0, "zmax" : 20},
			"HYBRID" : {"urlKey" : 'hybrid', "name" : 'Satellite Hybrid', "description" : 'Satellite with labels and roads', "format" : 'jpg', "zmin" : 0, "zmax" : 20},
			"STREETS" : {"urlKey" : 'streets-v2', "name" : 'Streets', "description" : 'Classic street map', "format" : 'png', "zmin" : 0, "zmax" : 20},
			"BASIC" : {"urlKey" : 'basic-v2', "name" : 'Basic', "description" : 'Minimalist flat design', "format" : 'png', "zmin" : 0, "zmax" : 20},
			"BRIGHT" : {"urlKey" : 'bright-v2', "name" : 'Bright', "description" : 'High-contrast navigation style', "format" : 'png', "zmin" : 0, "zmax" : 20},
			"TOPO" : {"urlKey" : 'topo-v2', "name" : 'Topo', "description" : 'Topographic map with contours', "format" : 'png', "zmin" : 0, "zmax" : 20},
			"OUTDOOR" : {"urlKey" : 'outdoor-v2', "name" : 'Outdoor', "description" : 'Hiking, peaks, isolines', "format" : 'png', "zmin" : 0, "zmax" : 20},
			"WINTER" : {"urlKey" : 'winter-v2', "name" : 'Winter', "description" : 'Winter sports — ski slopes, lifts', "format" : 'png', "zmin" : 0, "zmax" : 20},
			"DATAVIZ_LIGHT" : {"urlKey" : 'dataviz', "name" : 'Dataviz Light', "description" : 'Data visualisation basemap', "format" : 'png', "zmin" : 0, "zmax" : 20},
			"DATAVIZ_DARK" : {"urlKey" : 'dataviz-dark', "name" : 'Dataviz Dark', "description" : 'Dark data visualisation basemap', "format" : 'png', "zmin" : 0, "zmax" : 20},
			"OCEAN" : {"urlKey" : 'ocean', "name" : 'Ocean', "description" : 'Bathymetry and ocean features', "format" : 'png', "zmin" : 0, "zmax" : 20},
			"BACKDROP" : {"urlKey" : 'backdrop', "name" : 'Backdrop', "description" : 'Minimal context with terrain — ideal for data overlays', "format" : 'png', "zmin" : 0, "zmax" : 20},
			"AQUARELLE" : {"urlKey" : 'aquarelle', "name" : 'Aquarelle', "description" : 'Artistic hand-drawn watercolor aesthetic', "format" : 'png', "zmin" : 0, "zmax" : 20}
		},
		"urlTemplate": "https://api.maptiler.com/maps/{LAY}/256/{Z}/{X}/{Y}.png?key={MAPTILER_KEY}",
		"referer": "https://www.maptiler.com"
	},


	"THUNDERFOREST" : {
		"name" : 'Thunderforest',
		"description" : 'Thunderforest — free hobby plan (registration required)',
		"service": 'TMS',
		"grid": 'WM',
		"quadTree": False,
		"layers" : {
			"OPENCYCLEMAP" : {"urlKey" : 'cycle', "name" : 'OpenCycleMap', "description" : 'Cycling-focused map with routes', "format" : 'png', "zmin" : 0, "zmax" : 22},
			"TRANSPORT" : {"urlKey" : 'transport', "name" : 'Transport', "description" : 'Public transport map', "format" : 'png', "zmin" : 0, "zmax" : 22},
			"TRANSPORT_DARK" : {"urlKey" : 'transport-dark', "name" : 'Transport Dark', "description" : 'Dark public transport map', "format" : 'png', "zmin" : 0, "zmax" : 22},
			"LANDSCAPE" : {"urlKey" : 'landscape', "name" : 'Landscape', "description" : 'Natural world features and terrain', "format" : 'png', "zmin" : 0, "zmax" : 22},
			"OUTDOORS" : {"urlKey" : 'outdoors', "name" : 'Outdoors', "description" : 'Hiking and outdoor activities', "format" : 'png', "zmin" : 0, "zmax" : 22},
			"ATLAS" : {"urlKey" : 'atlas', "name" : 'Atlas', "description" : 'Clear map for navigation and context', "format" : 'png', "zmin" : 0, "zmax" : 22},
			"PIONEER" : {"urlKey" : 'pioneer', "name" : 'Pioneer', "description" : 'Modern railways in vintage style', "format" : 'png', "zmin" : 0, "zmax" : 22},
			"MOBILE_ATLAS" : {"urlKey" : 'mobile-atlas', "name" : 'Mobile Atlas', "description" : 'High-contrast for difficult lighting', "format" : 'png', "zmin" : 0, "zmax" : 22},
			"NEIGHBOURHOOD" : {"urlKey" : 'neighbourhood', "name" : 'Neighbourhood', "description" : 'Clean neighbourhood-focused map', "format" : 'png', "zmin" : 0, "zmax" : 22},
			"SPINAL_MAP" : {"urlKey" : 'spinal-map', "name" : 'Spinal Map', "description" : 'This map goes up to 11', "format" : 'png', "zmin" : 0, "zmax" : 22}
		},
		"urlTemplate": "https://tile.thunderforest.com/{LAY}/{Z}/{X}/{Y}.png?apikey={THUNDERFOREST_KEY}",
		"referer": "https://www.thunderforest.com"
	},


	"STADIA" : {
		"name" : 'Stadia Maps',
		"description" : 'Stadia Maps — free tier 200k credits/month (registration required)',
		"service": 'TMS',
		"grid": 'WM',
		"quadTree": False,
		"layers" : {
			"SMOOTH" : {"urlKey" : 'alidade_smooth', "name" : 'Alidade Smooth', "description" : 'Light basemap for overlays', "format" : 'png', "zmin" : 0, "zmax" : 20},
			"SMOOTH_DARK" : {"urlKey" : 'alidade_smooth_dark', "name" : 'Alidade Smooth Dark', "description" : 'Dark basemap', "format" : 'png', "zmin" : 0, "zmax" : 20},
			"SATELLITE" : {"urlKey" : 'alidade_satellite', "name" : 'Satellite', "description" : 'Satellite imagery with labels (Standard plan required)', "format" : 'jpg', "zmin" : 0, "zmax" : 20},
			"OUTDOORS" : {"urlKey" : 'outdoors', "name" : 'Outdoors', "description" : 'Outdoor features — trails, ski slopes, parks', "format" : 'png', "zmin" : 0, "zmax" : 20},
			"OSM_BRIGHT" : {"urlKey" : 'osm_bright', "name" : 'OSM Bright', "description" : 'Clean OSM basemap', "format" : 'png', "zmin" : 0, "zmax" : 20},
			"TONER" : {"urlKey" : 'stamen_toner', "name" : 'Stamen Toner', "description" : 'High-contrast black and white', "format" : 'png', "zmin" : 0, "zmax" : 18},
			"TONER_LITE" : {"urlKey" : 'stamen_toner_lite', "name" : 'Stamen Toner Lite', "description" : 'Lighter B+W variant', "format" : 'png', "zmin" : 0, "zmax" : 18},
			"TONER_BG" : {"urlKey" : 'stamen_toner_background', "name" : 'Stamen Toner Background', "description" : 'Only water, landcover and lines — no labels', "format" : 'png', "zmin" : 0, "zmax" : 18},
			"TONER_LINES" : {"urlKey" : 'stamen_toner_lines', "name" : 'Stamen Toner Lines', "description" : 'Only roads and borders', "format" : 'png', "zmin" : 0, "zmax" : 18},
			"TONER_LABELS" : {"urlKey" : 'stamen_toner_labels', "name" : 'Stamen Toner Labels', "description" : 'Only labels overlay', "format" : 'png', "zmin" : 0, "zmax" : 18},
			"TERRAIN" : {"urlKey" : 'stamen_terrain', "name" : 'Stamen Terrain', "description" : 'Hill shading and natural vegetation', "format" : 'png', "zmin" : 0, "zmax" : 18},
			"TERRAIN_BG" : {"urlKey" : 'stamen_terrain_background', "name" : 'Stamen Terrain Background', "description" : 'Only terrain and landcover — no labels', "format" : 'png', "zmin" : 0, "zmax" : 18},
			"TERRAIN_LINES" : {"urlKey" : 'stamen_terrain_lines', "name" : 'Stamen Terrain Lines', "description" : 'Only roads and borders', "format" : 'png', "zmin" : 0, "zmax" : 18},
			"TERRAIN_LABELS" : {"urlKey" : 'stamen_terrain_labels', "name" : 'Stamen Terrain Labels', "description" : 'Only labels overlay', "format" : 'png', "zmin" : 0, "zmax" : 18},
			"WATERCOLOR" : {"urlKey" : 'stamen_watercolor', "name" : 'Stamen Watercolor', "description" : 'Hand-drawn watercolor style', "format" : 'jpg', "zmin" : 0, "zmax" : 16}
		},
		"urlTemplate": "https://tiles.stadiamaps.com/tiles/{LAY}/{Z}/{X}/{Y}.png?api_key={STADIA_API_KEY}",
		"referer": "https://stadiamaps.com"
	},


	"OPENTOPOMAP" : {
		"name" : 'OpenTopoMap',
		"description" : 'Topographic map with contour lines — CC BY-SA 3.0',
		"service": 'TMS',
		"grid": 'WM',
		"quadTree": False,
		"layers" : {
			"TOPO" : {"urlKey" : '', "name" : 'Topographic', "description" : 'Topographic map with elevation contours', "format" : 'png', "zmin" : 0, "zmax" : 17}
		},
		"urlTemplate": "https://tile.opentopomap.org/{Z}/{X}/{Y}.png",
		"referer": "https://opentopomap.org"
	},


	"OSM_HOT" : {
		"name" : 'Humanitarian OSM',
		"description" : 'Humanitarian style — ODbL',
		"service": 'TMS',
		"grid": 'WM',
		"quadTree": False,
		"layers" : {
			"HOT" : {"urlKey" : '', "name" : 'Humanitarian', "description" : 'Humanitarian/crisis style map', "format" : 'png', "zmin" : 0, "zmax" : 19}
		},
		"urlTemplate": "https://a.tile.openstreetmap.fr/hot/{Z}/{X}/{Y}.png",
		"referer": "https://www.hotosm.org"
	},


	"CYCLOSM" : {
		"name" : 'CyclOSM',
		"description" : 'Bicycle-focused map — ODbL',
		"service": 'TMS',
		"grid": 'WM',
		"quadTree": False,
		"layers" : {
			"CYCLE" : {"urlKey" : '', "name" : 'Cycling', "description" : 'Bicycle-focused map with routes and infrastructure', "format" : 'png', "zmin" : 0, "zmax" : 19}
		},
		"urlTemplate": "https://a.tile-cyclosm.openstreetmap.fr/cyclosm/{Z}/{X}/{Y}.png",
		"referer": "https://www.cyclosm.org"
	},


	"OPENRAILWAYMAP" : {
		"name" : 'OpenRailwayMap',
		"description" : 'Railway infrastructure overlay — CC BY-SA 2.0',
		"service": 'TMS',
		"grid": 'WM',
		"quadTree": False,
		"layers" : {
			"RAIL" : {"urlKey" : '', "name" : 'Railways', "description" : 'Railway infrastructure overlay', "format" : 'png', "zmin" : 0, "zmax" : 19}
		},
		"urlTemplate": "https://a.tiles.openrailwaymap.org/standard/{Z}/{X}/{Y}.png",
		"referer": "https://www.openrailwaymap.org"
	},


	"WIKIMEDIA" : {
		"name" : 'Wikimedia',
		"description" : 'Wikipedia-style map — CC BY-SA',
		"service": 'TMS',
		"grid": 'WM',
		"quadTree": False,
		"layers" : {
			"MAP" : {"urlKey" : '', "name" : 'Wikimedia', "description" : 'Wikipedia-style map', "format" : 'png', "zmin" : 0, "zmax" : 19}
		},
		"urlTemplate": "https://maps.wikimedia.org/osm-intl/{Z}/{X}/{Y}.png",
		"referer": "https://maps.wikimedia.org"
	},


	"GEOPORTAIL" : {
		"name" : 'Geoportail',
		"description" : 'Geoportail.fr',
		"service": 'WMTS',
		"grid": 'WM',
		"matrix" : 'PM',
		"layers" : {
			"ORTHO" : {"urlKey" : 'ORTHOIMAGERY.ORTHOPHOTOS', "name" : 'Orthophotos', "description" : '',
				"format" : 'jpeg', "style" : 'normal', "zmin" : 0, "zmax" : 22},
			"CAD" : {"urlKey" : 'CADASTRALPARCELS.PARCELS', "name" : 'Cadastre', "description" : '',
				"format" : 'png', "style" : 'bdparcellaire', "zmin" : 0, "zmax" : 22}
		},
		"urlTemplate": {
			"BASE_URL" : 'https://data.geopf.fr/wmts?',
			"SERVICE" : 'WMTS',
			"VERSION" : '1.0.0',
			"REQUEST" : 'GetTile',
			"LAYER" : '{LAY}',
			"STYLE" : '{STYLE}',
			"FORMAT" : 'image/{FORMAT}',
			"TILEMATRIXSET" : '{MATRIX}',
			"TILEMATRIX" : '{Z}',
			"TILEROW" : '{Y}',
			"TILECOL" : '{X}'
			},
		"referer": "http://www.geoportail.gouv.fr/accueil"
	},

	"GEOPORTAIL2" : {
		"name" : 'Geoportail ©scan',
		"description" : 'Geoportail.fr',
		"service": 'WMTS',
		"grid": 'WM',
		"matrix" : 'PM',
		"layers" : {
			"SCAN" : {"urlKey" : 'GEOGRAPHICALGRIDSYSTEMS.MAPS', "name" : 'Scan', "description" : '',
				"format" : 'jpeg', "style" : 'normal', "zmin" : 0, "zmax" : 22}
		},
		"urlTemplate": {
			"BASE_URL" : 'https://data.geopf.fr/private/wmts?',
			"SERVICE" : 'WMTS',
			"VERSION" : '1.0.0',
			"REQUEST" : 'GetTile',
			"LAYER" : '{LAY}',
			"STYLE" : '{STYLE}',
			"FORMAT" : 'image/{FORMAT}',
			"TILEMATRIXSET" : '{MATRIX}',
			"TILEMATRIX" : '{Z}',
			"TILEROW" : '{Y}',
			"TILECOL" : '{X}',
			"apikey" : "ign_scan_ws"
			},
		"referer": "http://www.geoportail.gouv.fr/accueil"
	}

}
"""
	#http://wms.craig.fr/ortho?SERVICE=WMS&REQUEST=GetCapabilities
	# example of valid location in Auvergne : lat 45.77 long 3.082
	"CRAIG_WMS" : {
		"name" : 'CRAIG WMS',
		"description" : "Centre Régional Auvergnat de l'Information Géographique",
		"service": 'WMS',
		"grid": 'LB93',
		"layers" : {
			"ORTHO" : {"urlKey" : 'auvergne', "name" : 'Auv25cm_2013', "description" : '', "format" : 'png', "style" : 'default', "zmin" : 0, "zmax" : 22}
		},
		"urlTemplate": {
			"BASE_URL" : 'http://wms.craig.fr/ortho?',
			"SERVICE" : 'WMS',
			"VERSION" : '1.3.0',
			"REQUEST" : 'GetMap',
			"CRS" : '{CRS}',
			"LAYERS" : '{LAY}',
			"FORMAT" : 'image/{FORMAT}',
			"STYLES" : '{STYLE}',
			"BBOX" : '{BBOX}', #xmin,ymin,xmax,ymax, in "SRS" projection
			"WIDTH" : '{WIDTH}',
			"HEIGHT" : '{HEIGHT}',
			"TRANSPARENT" : "False"
			},
		"referer": "http://www.craig.fr/"
	},


	###############
	# WMTS examples
	###############


	# http://tiles.craig.fr/ortho/service?service=WMTS&REQUEST=GetCapabilities
	# example of valid location in Auvergne : lat 45.77 long 3.082
	"CRAIG_WMTS93" : {
		"name" : 'CRAIG WMTS93',
		"description" : "Centre Régional Auvergnat de l'Information Géographique",
		"service": 'WMTS',
		"grid": 'LB93_CRAIG',
		"matrix" : 'lambert93',
		"layers" : {
			"ORTHO" : {"urlKey" : 'ortho_2013', "name" : 'Auv25cm_2013', "description" : '',
				"format" : 'jpeg', "style" : 'default', "zmin" : 0, "zmax" : 15}
		},
		"urlTemplate": {
			"BASE_URL" : 'http://tiles.craig.fr/ortho/service?',
			"SERVICE" : 'WMTS',
			"VERSION" : '1.0.0',
			"REQUEST" : 'GetTile',
			"LAYER" : '{LAY}',
			"STYLE" : '{STYLE}',
			"FORMAT" : 'image/{FORMAT}',
			"TILEMATRIXSET" : '{MATRIX}',
			"TILEMATRIX" : '{Z}',
			"TILEROW" : '{Y}',
			"TILECOL" : '{X}'
			},
		"referer": "http://www.craig.fr/"
	},



}
"""
