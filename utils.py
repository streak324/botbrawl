import pymunk

def create_pymunk_box(body: pymunk.Body, min: tuple[float,float], max: tuple[float,float], radus: float = 0):
	return pymunk.Poly(body, [min, (max[0], min[1]), max, (min[0], max[1])], radius=0)


def add_capsule_shape(body: pymunk.Body, offset: tuple[float,float], width: float, height: float) -> list[pymunk.Shape] :
	if width == height:
		return [pymunk.Circle(body, 0.5*width, offset)]
	if width > height:
		stretch_length = width - height
		c1 = pymunk.Circle(body, height*0.5, offset=(offset[0] - stretch_length*0.5, offset[1]))
		c2 = pymunk.Circle(body, height*0.5, offset=(offset[0] + stretch_length*0.5, offset[1]))
		box = create_pymunk_box(body, 
			(offset[0] - stretch_length*0.5, offset[1] - height*0.5), 
			(offset[0] + stretch_length*0.5, offset[1] + height*0.5))
		return [c1,c2,box]
	else:
		stretch_length = height - width
		c1 = pymunk.Circle(body, width*0.5, offset=(offset[0], offset[1] - stretch_length*0.5))
		c2 = pymunk.Circle(body, width*0.5, offset=(offset[0], offset[1] + stretch_length*0.5))
		box = create_pymunk_box(body, 
			(offset[0] - width*0.5, offset[1] - stretch_length*0.5), 
			(offset[0] + width*0.5, offset[1] + stretch_length*0.5))
		return [c1, c2, box]