# Derived from https://github.com/hrbaer/Blender-ASCII-Grid-Import

import re
import os
import string
import bpy
import math
import numpy as np

import logging
log = logging.getLogger(__name__)

from bpy_extras.io_utils import ImportHelper #helper class defines filename and invoke() function which calls the file selector
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty
from bpy.types import Operator

from ..core.proj import Reproj
from ..core.utils import XY
from ..geoscene import GeoScene, georefManagerLayout
from ..prefs import PredefCRS

from .utils import bpyGeoRaster as GeoRaster
from .utils import placeObj, adjust3Dview, showTextures, addTexture, getBBOX
from .utils import rasterExtentToMesh, geoRastUVmap, setDisplacer

PKG = __package__.rsplit('.', maxsplit=1)[0]  # bl_ext.user_default.cartoblend


class IMPORTGIS_OT_ascii_grid(Operator, ImportHelper):
    """Import ESRI ASCII grid file"""
    bl_idname = "importgis.asc_file"  # important since its how bpy.ops.importgis.asc is constructed (allows calling operator from python console or another script)
    #bl_idname rules: must contain one '.' (dot) charactere, no capital letters, no reserved words (like 'import')
    bl_description = 'Import ESRI ASCII grid with world file'
    bl_label = "Import ASCII Grid"
    bl_options = {"UNDO"}

    # ImportHelper class properties
    filter_glob: StringProperty(
        default="*.asc;*.grd",
        options={'HIDDEN'},
    )

    # Raster CRS definition
    def listPredefCRS(self, context):
        return PredefCRS.getEnumItems()
    fileCRS: EnumProperty(
        name = "CRS",
        description = "Choose a Coordinate Reference System",
        items = listPredefCRS,
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    importMode: EnumProperty(
        name = "Mode",
        description = "Select import mode",
        items = [
            ('MESH', 'Mesh', "Create triangulated regular network mesh"),
            ('CLOUD', 'Point cloud', "Create vertex point cloud"),
        ],
    )

    # Step makes point clouds with billions of points possible to read on consumer hardware
    step: IntProperty(
        name = "Step",
        description = "Only read every Nth point for massive point clouds",
        default = 1,
        min = 1
    )

    # Let the user decide whether to use the faster newline method
    # Alternatively, use self.total_newlines(filename) to see whether total >= nrows and automatically decide (at the cost of time spent counting lines)
    newlines: BoolProperty(
        name = "Newline-delimited rows",
        description = "Use this method if the file contains newline separated rows for faster import",
        default = True,
    )

    def draw(self, context):
        #Function used by blender to draw the panel.
        layout = self.layout
        layout.prop(self, 'importMode')
        layout.prop(self, 'step')
        layout.prop(self, 'newlines')

        row = layout.row(align=True)
        split = row.split(factor=0.35, align=True)
        split.label(text='CRS:')
        split.prop(self, "fileCRS", text='')
        row.operator("bgis.add_predef_crs", text='', icon='ADD')
        scn = bpy.context.scene
        geoscn = GeoScene(scn)
        if geoscn.isPartiallyGeoref:
            georefManagerLayout(self, context)


    def total_lines(self, filename):
        """
        Count newlines in file.
        512MB file ~3 seconds.
        """
        with open(filename, encoding='utf-8') as f:
            lines = 0
            for _ in f:
                lines += 1
            return lines

    def read_row_newlines(self, f, ncols):
        """
        Read a row by columns separated by newline.
        """
        return f.readline().split()

    def read_row_whitespace(self, f, ncols):
        """
        Read a row by columns separated by whitespace (including newlines).
        6x slower than readlines() method but faster than any other method I can come up with. See commit 4d337c4 for alternatives.
        """
        # choose a buffer that requires the least reads, but not too much memory (32MB max)
        # cols * 6 allows us 5 chars plus space, approximating values such as '12345', '-1234', '12.34', '-12.3'
        buf_size = min(1024 * 32, ncols * 6)
        row = []
        read_f = f.read
        while True:
            chunk = read_f(buf_size)

            # assuming we read a complete chunk, remove end of string up to last whitespace to avoid partial values
            # if the chunk is smaller than our buffer size, then we've read to the end of file and
            #   can skip truncating the chunk since we know the last value will be complete
            if len(chunk) == buf_size:
                for i in range(len(chunk) - 1, -1, -1):
                    if chunk[i].isspace():
                        f.seek(f.tell() - (len(chunk) - i))
                        chunk = chunk[:i]
                        break

            # either read was EOF or chunk was all whitespace
            if not chunk:
                return row  # eof without reaching ncols?

            # find each value separated by any whitespace char
            for m in re.finditer(r'([^\s]+)', chunk):
                row.append(m.group(0))
                if len(row) == ncols:
                    # completed a row within this chunk, rewind the position to start at the beginning of the next row
                    f.seek(f.tell() - (len(chunk) - m.end()))
                    return row

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        prefs = context.preferences.addons[PKG].preferences
        bpy.ops.object.select_all(action='DESELECT')
        #Get scene and some georef data
        scn = bpy.context.scene
        geoscn = GeoScene(scn)
        if geoscn.isBroken:
            self.report({'ERROR'}, "Scene georef is broken, please fix it beforehand")
            return {'CANCELLED'}
        dx, dy = 0, 0
        if geoscn.isGeoref:
            dx, dy = geoscn.getOriginPrj()
        scale = geoscn.scale #TODO
        if not geoscn.hasCRS:
            try:
                geoscn.crs = self.fileCRS
            except Exception as e:
                log.error("Cannot set scene crs", exc_info=True)
                self.report({'ERROR'}, "Cannot set scene crs, check logs for more infos")
                return {'CANCELLED'}

        #build reprojector objects
        if geoscn.crs != self.fileCRS:
            rprj = True
            rprjToRaster = Reproj(geoscn.crs, self.fileCRS)
            rprjToScene = Reproj(self.fileCRS, geoscn.crs)
        else:
            rprj = False
            rprjToRaster = None
            rprjToScene = None

        #Path
        filename = self.filepath
        name = os.path.splitext(os.path.basename(filename))[0]
        log.info('Importing {}...'.format(filename))

        with open(filename, 'r', encoding='utf-8') as f:
            meta_re = re.compile(r'^([^\s]+)\s+([^\s]+)$')  # 'abc  123'
            meta = {}
            for i in range(6):
                line = f.readline()
                m = meta_re.match(line)
                if m:
                    meta[m.group(1).lower()] = m.group(2)
            log.debug(meta)

            # step allows reduction during import, only taking every Nth point
            step = self.step
            try:
                nrows = int(meta['nrows'])
                ncols = int(meta['ncols'])
                cellsize = float(meta['cellsize'])
            except KeyError as e:
                log.error("Missing required header key: %s", e)
                self.report({'ERROR'}, "Missing required ASC header key: {}".format(e))
                return {'CANCELLED'}
            # NODATA_value is optional per ESRI spec; fall back to the conventional
            # sentinel so a header without the line still imports cleanly.
            try:
                nodata = float(meta.get('nodata_value', -9999))
            except (TypeError, ValueError):
                nodata = -9999.0

            # options are lower left cell corner, or lower left cell centre
            reprojection = {}
            offset = XY(0, 0)
            if 'xllcorner' in meta:
                llcorner = XY(float(meta['xllcorner']), float(meta['yllcorner']))
                reprojection['from'] = llcorner
            elif 'xllcenter' in meta:
                centre = XY(float(meta['xllcenter']), float(meta['yllcenter']))
                offset = XY(-cellsize / 2, -cellsize / 2)
                reprojection['from'] = centre
            else:
                log.error("ASC file missing xllcorner/xllcenter header")
                self.report({'ERROR'}, "ASC file is missing xllcorner or xllcenter header")
                return {'CANCELLED'}

            # now set the correct offset for the mesh
            if rprj:
                reprojection['to'] = XY(*rprjToScene.pt(*reprojection['from']))
                log.debug('{name} reprojected from {from} to {to}'.format(**reprojection, name=name))
            else:
                reprojection['to'] = reprojection['from']

            if not geoscn.isGeoref:
                # use the centre of the imported grid as scene origin (calculate only if grid file specified llcorner)
                centre = (reprojection['from'].x + offset.x + ((ncols / 2) * cellsize),
                          reprojection['from'].y + offset.y + ((nrows / 2) * cellsize))
                if rprj:
                    centre = rprjToScene.pt(*centre)
                geoscn.setOriginPrj(*centre)
                dx, dy = geoscn.getOriginPrj()

            # --- numpy-basierter Datenlader (ersetzt den doppelten for-Loop) ---
            # Lese die gesamte Daten-Matrix auf einmal; Header wurde bereits oben gelesen,
            # daher skiprows=0 (Datei-Cursor steht schon auf den Daten).
            try:
                arr = np.loadtxt(f, dtype=np.float32)
            except ValueError as e:
                log.error("Cannot parse ASC data as float array: %s", e)
                self.report({'ERROR'}, 'Cannot parse ASC grid data: {}'.format(e))
                return {'CANCELLED'}

            if arr.shape != (nrows, ncols):
                log.error('Data shape %s does not match header (%d, %d)', arr.shape, nrows, ncols)
                self.report({'ERROR'}, 'ASC data shape does not match header dimensions')
                return {'CANCELLED'}

            # Dezimierung via numpy-Slicing: ASC-Zeile 0 ist der nördlichste Streifen
            # (höchster y-Wert), daher Zeilen umkehren und dann sampeln.
            arr = arr[::-1, :]          # flip: Zeile 0 = Süden
            arr = arr[::step, ::step]   # Dezimierung

            sub_nrows, sub_ncols = arr.shape

            # Koordinatengitter (in Quell-CRS, Einheit: cellsize-Einheiten)
            col_idx = np.arange(sub_ncols, dtype=np.float32) * (cellsize * step) + offset.x
            row_idx = np.arange(sub_nrows, dtype=np.float32) * (cellsize * step) + offset.y
            xs, ys = np.meshgrid(col_idx, row_idx)  # (sub_nrows, sub_ncols)

            if rprj:
                # Vektorisierte Reprojektion aller Punkte auf einmal
                src_xs = xs.ravel() + reprojection['from'].x
                src_ys = ys.ravel() + reprojection['from'].y
                reproj_pts = rprjToScene.pts(list(zip(src_xs.tolist(), src_ys.tolist())))
                reproj_arr = np.array(reproj_pts, dtype=np.float32)
                xs_out = reproj_arr[:, 0] - reprojection['to'].x
                ys_out = reproj_arr[:, 1] - reprojection['to'].y
            else:
                xs_out = xs.ravel()
                ys_out = ys.ravel()

            zs = arr.ravel()

            if self.importMode == 'CLOUD':
                # Punkt-Wolke: NoData-Punkte komplett verwerfen
                mask = zs != nodata
                xs_out = xs_out[mask]
                ys_out = ys_out[mask]
                zs = zs[mask]
            else:
                # Mesh: NoData durch 0.0 ersetzen, Topologie bleibt intakt
                zs = np.where(zs == nodata, np.float32(0.0), zs)

            vertices = list(zip(xs_out.tolist(), ys_out.tolist(), zs.tolist()))
            index = 0
            faces = []

        if self.importMode == 'MESH':
            # sub_ncols/sub_nrows wurden durch numpy-Slicing bereits korrekt berechnet
            for r in range(0, sub_nrows - 1):
                for c in range(0, sub_ncols - 1):
                    v1 = index
                    v2 = v1 + sub_ncols
                    v3 = v2 + 1
                    v4 = v1 + 1
                    faces.append((v1, v2, v3, v4))
                    index += 1
                index += 1

        # Create mesh
        me = bpy.data.meshes.new(name)
        ob = bpy.data.objects.new(name, me)
        ob.location = (reprojection['to'].x - dx, reprojection['to'].y - dy, 0)

        # Link object to scene and make active
        scn = bpy.context.scene
        scn.collection.objects.link(ob)
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)

        me.from_pydata(vertices, [], faces)
        me.update()

        if prefs.adjust3Dview:
            bb = getBBOX.fromObj(ob)
            adjust3Dview(context, bb)

        return {'FINISHED'}

def register():
	try:
		bpy.utils.register_class(IMPORTGIS_OT_ascii_grid)
	except ValueError as e:
		log.warning('{} is already registered, now unregister and retry... '.format(IMPORTGIS_OT_ascii_grid))
		unregister()
		bpy.utils.register_class(IMPORTGIS_OT_ascii_grid)

def unregister():
	bpy.utils.unregister_class(IMPORTGIS_OT_ascii_grid)
