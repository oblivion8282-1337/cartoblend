

#Scale/normalize function : linear stretch from lowest value to highest value
#########################################
def scale(inVal, inMin, inMax, outMin, outMax):
	if inMax == inMin:
		# Degenerate input range (e.g. flat DEM, single-value reclass): map
		# everything to the lower bound of the output range.
		return outMin
	return (inVal - inMin) * (outMax - outMin) / (inMax - inMin) + outMin



def linearInterpo(x1, x2, y1, y2, x):
	#Linear interpolation = y1 + slope * tx
	dx = x2 - x1
	if dx == 0:
		# Coincident control points: no slope to interpolate; return y1.
		return y1
	dy = y2-y1
	slope = dy/dx
	tx = x - x1 #position from x1 (target x)
	return y1 + slope * tx
