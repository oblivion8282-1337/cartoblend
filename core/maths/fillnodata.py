# -*- coding:utf-8 -*-

# This file is part of CartoBlend

#  ***** GPL LICENSE BLOCK *****
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#  All rights reserved.
#  ***** GPL LICENSE BLOCK *****




########################################
# Inpainting function
# http://astrolitterbox.blogspot.fr/2012/03/healing-holes-in-arrays-in-python.html
# https://github.com/gasagna/openpiv-python/blob/master/openpiv/src/lib.pyx


import math
import numpy as np

DTYPEf = np.float32
#DTYPEi = np.int32


def replace_nans(array, max_iter, tolerance, kernel_size=1, method='localmean'):
	"""
	Replace NaN elements in an array using an iterative image inpainting algorithm.
	The algorithm is the following:
	1) For each element in the input array, replace it by a weighted average
	of the neighbouring elements which are not NaN themselves. The weights depends
	of the method type. If ``method=localmean`` weight are equal to 1/( (2*kernel_size+1)**2 -1 )
	2) Several iterations are needed if there are adjacent NaN elements.
	If this is the case, information is "spread" from the edges of the missing
	regions iteratively, until the variation is below a certain threshold.

	Parameters
	----------
	array : 2d np.ndarray
	an array containing NaN elements that have to be replaced

	max_iter : int
	the number of iterations

	kernel_size : int
	the size of the kernel, default is 1

	method : str
	the method used to replace invalid values. Valid options are 'localmean', 'idw'.

	Returns
	-------
	filled : 2d np.ndarray
	a copy of the input array, where NaN elements have been replaced.
	"""

	# Build kernel
	if method == 'localmean':
		kernel = np.ones((2*kernel_size+1, 2*kernel_size+1), dtype=DTYPEf)
	elif method == 'idw':
		kernel = np.array([[0, 0.5, 0.5, 0.5, 0],
				  [0.5, 0.75, 0.75, 0.75, 0.5],
				  [0.5, 0.75, 1, 0.75, 0.5],
				  [0.5, 0.75, 0.75, 0.5, 1],
				  [0, 0.5, 0.5, 0.5, 0]], dtype=DTYPEf)
	else:
		raise ValueError("method not valid. Should be one of 'localmean', 'idw'.")

	filled = array.astype(DTYPEf, copy=True)
	nan_mask_initial = np.isnan(filled)
	H, W = filled.shape
	ks = kernel_size

	# Iterate Jacobi-style: each pass uses the previous pass's snapshot to avoid
	# read-during-update artefacts. Information diffuses across NaN regions one
	# kernel-radius per iteration.
	prev_replaced = np.zeros_like(filled)
	for it in range(max_iter):
		valid = ~np.isnan(filled)
		vals = np.where(valid, filled, 0.0)

		weighted_sum = np.zeros_like(filled)
		weight_sum = np.zeros_like(filled)

		for I in range(2*ks+1):
			for J in range(2*ks+1):
				# Skip kernel center (the cell being filled).
				if I - ks == 0 and J - ks == 0:
					continue
				w = kernel[I, J]
				if w == 0:
					continue
				di = I - ks
				dj = J - ks
				# Slices that read from (i+di, j+dj) into (i, j) with bounds-clipping.
				src_i = slice(max(0, di), H + min(0, di))
				src_j = slice(max(0, dj), W + min(0, dj))
				dst_i = slice(max(0, -di), H + min(0, -di))
				dst_j = slice(max(0, -dj), W + min(0, -dj))
				weighted_sum[dst_i, dst_j] += w * vals[src_i, src_j]
				weight_sum[dst_i, dst_j] += w * valid[src_i, src_j]

		with np.errstate(invalid='ignore', divide='ignore'):
			new_vals = weighted_sum / weight_sum

		update_mask = nan_mask_initial & (weight_sum > 0)
		# Cells that have no valid neighbour stay NaN (may be reached next iter).
		filled = np.where(update_mask, new_vals, np.where(nan_mask_initial, np.nan, filled))

		# Convergence: MSE between this and previous pass over replaced cells.
		if it > 0:
			diff = filled[update_mask] - prev_replaced[update_mask]
			if diff.size and np.nanmean(diff * diff) < tolerance:
				break
		prev_replaced = filled.copy()

	return filled


def sincinterp(image, x,  y, kernel_size=3 ):
	r"""
	Re-sample an image at intermediate positions between pixels.
	This function uses a cardinal interpolation formula which limits
	the loss of information in the resampling process. It uses a limited
	number of neighbouring pixels.

	The new image :math:`im^+` at fractional locations :math:`x` and :math:`y` is computed as:
	.. math::
	im^+(x,y) = \sum_{i=-\mathtt{kernel\_size}}^{i=\mathtt{kernel\_size}} \sum_{j=-\mathtt{kernel\_size}}^{j=\mathtt{kernel\_size}} \mathtt{image}(i,j) sin[\pi(i-\mathtt{x})] sin[\pi(j-\mathtt{y})] / \pi(i-\mathtt{x}) / \pi(j-\mathtt{y})

	Parameters
	----------
	image : np.ndarray, dtype np.int32
	the image array.

	x : two dimensions np.ndarray of floats
	an array containing fractional pixel row
	positions at which to interpolate the image

	y : two dimensions np.ndarray of floats
	an array containing fractional pixel column
	positions at which to interpolate the image

	kernel_size : int
	interpolation is performed over a ``(2*kernel_size+1)*(2*kernel_size+1)``
	submatrix in the neighbourhood of each interpolation point.

	Returns
	-------
	im : np.ndarray, dtype np.float64
	the interpolated value of ``image`` at the points specified by ``x`` and ``y``
	"""

	# the output array
	r = np.zeros( [x.shape[0], x.shape[1]], dtype=DTYPEf)

	# fast pi
	pi = math.pi

	# for each point of the output array
	for I in range(x.shape[0]):
		for J in range(x.shape[1]):

			#loop over all neighbouring grid points
			for i in range( int(x[I,J])-kernel_size, int(x[I,J])+kernel_size+1 ):
				for j in range( int(y[I,J])-kernel_size, int(y[I,J])+kernel_size+1 ):
					# check that we are in the boundaries
					if i >= 0 and i <= image.shape[0] and j >= 0 and j <= image.shape[1]:
						if (i-x[I,J]) == 0.0 and (j-y[I,J]) == 0.0:
							r[I,J] = r[I,J] + image[i,j]
						elif (i-x[I,J]) == 0.0:
							r[I,J] = r[I,J] + image[i,j] * np.sin( pi*(j-y[I,J]) )/( pi*(j-y[I,J]) )
						elif (j-y[I,J]) == 0.0:
							r[I,J] = r[I,J] + image[i,j] * np.sin( pi*(i-x[I,J]) )/( pi*(i-x[I,J]) )
						else:
							r[I,J] = r[I,J] + image[i,j] * np.sin( pi*(i-x[I,J]) )*np.sin( pi*(j-y[I,J]) )/( pi*pi*(i-x[I,J])*(j-y[I,J]))
	return r
