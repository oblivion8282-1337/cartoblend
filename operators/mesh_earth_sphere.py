import bpy
from bpy.types import Operator
from bpy.props import IntProperty

from math import cos, sin, radians, sqrt
from mathutils import Vector
import numpy as np

import logging
log = logging.getLogger(__name__)


def lonlat2xyz(R, lon, lat):
	lon, lat = radians(lon), radians(lat)
	x = R * cos(lat) * cos(lon)
	y = R * cos(lat) * sin(lon)
	z = R *sin(lat)
	return Vector((x, y, z))


class OBJECT_OT_earth_sphere(Operator):
	bl_idname = "earth.sphere"
	bl_label = "lonlat to sphere"
	bl_description = "Transform longitude/latitude data to a sphere like earth globe"
	bl_options = {"REGISTER", "UNDO"}

	radius: IntProperty(name = "Radius", default=100, description="Sphere radius", min=1)

	def execute(self, context):
		scn = bpy.context.scene
		objs = bpy.context.selected_objects

		if not objs:
			self.report({'INFO'}, "No selected object")
			return {'CANCELLED'}

		for obj in objs:
			if obj.type != 'MESH':
				log.warning("Object {} is not a mesh".format(obj.name))
				continue

			w, h, thick = obj.dimensions
			if w > 360:
				log.warning("Longitude of object {} exceed 360°".format(obj.name))
				continue
			if h > 180:
				log.warning("Latitude of object {} exceed 180°".format(obj.name))
				continue

			mesh = obj.data
			m = np.array(obj.matrix_world)
			mi = np.array(obj.matrix_world.inverted())
			n = len(mesh.vertices)
			# Pull all local coords as a flat numpy buffer.
			coords = np.empty(n * 3, dtype=np.float32)
			mesh.vertices.foreach_get('co', coords)
			coords = coords.reshape(n, 3)
			# Build homogeneous coords and transform to world space.
			ones = np.ones((n, 1), dtype=np.float32)
			homog = np.concatenate([coords, ones], axis=1)
			world = homog @ m.T
			lon = np.radians(world[:, 0])
			lat = np.radians(world[:, 1])
			cos_lat = np.cos(lat)
			x = self.radius * cos_lat * np.cos(lon)
			y = self.radius * cos_lat * np.sin(lon)
			z = self.radius * np.sin(lat)
			# Back to local space.
			world_new = np.stack([x, y, z, np.ones(n, dtype=x.dtype)], axis=1)
			local_new = (world_new @ mi.T)[:, :3]
			mesh.vertices.foreach_set('co', local_new.astype(np.float32).ravel())
			mesh.update()

		return {'FINISHED'}

EARTH_RADIUS = 6378137 #meters
def getZDelta(d):
	'''delta value for adjusting z across earth curvature
	http://webhelp.infovista.com/Planet/62/Subsystems/Raster/Content/help/analysis/viewshedanalysis.html'''
	return sqrt(EARTH_RADIUS**2 + d**2) - EARTH_RADIUS


class OBJECT_OT_earth_curvature(Operator):
	bl_idname = "earth.curvature"
	bl_label = "Earth curvature correction"
	bl_description = "Apply earth curvature correction for viewsheed analysis"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		scn = bpy.context.scene
		obj = bpy.context.view_layer.objects.active

		if not obj:
			self.report({'INFO'}, "No active object")
			return {'CANCELLED'}

		if obj.type != 'MESH':
			self.report({'INFO'}, "Selection isn't a mesh")
			return {'CANCELLED'}

		mesh = obj.data
		viewpt = scn.cursor.location
		n = len(mesh.vertices)
		coords = np.empty(n * 3, dtype=np.float32)
		mesh.vertices.foreach_get('co', coords)
		coords = coords.reshape(n, 3)
		dx = coords[:, 0] - viewpt.x
		dy = coords[:, 1] - viewpt.y
		d = np.sqrt(dx * dx + dy * dy)
		coords[:, 2] = coords[:, 2] - (np.sqrt(EARTH_RADIUS * EARTH_RADIUS + d * d) - EARTH_RADIUS)
		mesh.vertices.foreach_set('co', coords.ravel())
		mesh.update()

		return {'FINISHED'}


classes = [
	OBJECT_OT_earth_sphere,
	OBJECT_OT_earth_curvature
]

def register():
	for cls in classes:
		try:
			bpy.utils.register_class(cls)
		except ValueError as e:
			log.warning('{} is already registered, now unregister and retry... '.format(cls))
			bpy.utils.unregister_class(cls)
			bpy.utils.register_class(cls)

def unregister():
	for cls in classes:
		bpy.utils.unregister_class(cls)
