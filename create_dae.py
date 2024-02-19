import collada
from typing import List, Tuple
from collada import source, geometry, scene
import numpy
from dae_class import DAE, LG, Material

def _add_normals(coords, flag=False) -> numpy.ndarray:
    if flag == True:
        iterate = len(coords)
    else:
        iterate = 1
    start_num = 0
    polygons = []
    for _ in range(iterate):
        polygons.append(numpy.array([start_num,
                                    0,  
                                    start_num+1,
                                    0, 
                                    start_num+2,
                                    0, 
                                    start_num,
                                    0, 
                                    start_num+2,
                                    0, 
                                    start_num+3,
                                    0]))
        start_num += 4
    result = numpy.array(polygons)

    return result

def _define_normals(coords: List[Tuple]) -> numpy.ndarray:
    vector_ab = numpy.array(list(coords[1])) - numpy.array(list(coords[0]))
    vector_cd = numpy.array(list(coords[2])) - numpy.array(list(coords[0]))
    normal = numpy.cross(vector_ab, vector_cd)
    normal = normal / numpy.linalg.norm(normal)
    
    return normal

def _common_holes(windows, doors) -> List[List[Tuple[int, int, int]]]:
    if windows[0][0][0] == windows[0][2][0]:
        result = sorted(windows + doors, key=lambda v: v[0][1])
    else:
        result = sorted(windows + doors, key=lambda v: v[0][0])
    
    return result

def _devide_wall(id, wall, holes, length, polygons_vert, index) -> List[List[Tuple[int, int, int]]]:
    #left part
    polygons_vert.append([wall[0], 
                          wall[1], 
                          (holes[0][0][0], holes[0][0][1], wall[1][2]), 
                          (holes[0][0][0], holes[0][0][1], wall[0][2])])
    
    #bottom part
    polygons_vert.append([(holes[0][0][0], holes[0][0][1], wall[0][2]), 
                          (holes[0][0]), 
                          (holes[0][3]), 
                          (holes[0][2][0], holes[0][2][1], wall[0][2])])
    
    #upper part
    polygons_vert.append([(holes[0][1]), 
                          (holes[0][0][0], holes[0][0][1], wall[1][2]), 
                          (holes[0][2][0], holes[0][2][1], wall[1][2]), 
                          (holes[0][2])])
    index += 1
    if index < length:
        wall = [(holes[0][2][0], holes[0][2][1], wall[0][2]), 
                (holes[0][2][0], holes[0][2][1], wall[1][2]), 
                wall[2], 
                wall[3]]
        holes.pop(0)
        _devide_wall(id, wall, holes, length, polygons_vert, index)
    else:
        #right part
        polygons_vert.append([(holes[0][2][0], holes[0][2][1], wall[0][2]), 
                              (holes[0][2][0], holes[0][2][1], wall[1][2]), 
                              wall[2], 
                              wall[3]])
       
    return polygons_vert

def _create_scene(dae, lg, geom_list, mtrl, name, extras):
    node_list = []
    node_list = _create_geom(geom_list, lg, node_list, dae, mtrl, extras)
    nodes = scene.Node(f'{name}', children=node_list)
    return nodes

def _create_geom(geometries, lg, node_list, dae, mtrl, extras):
    window_ids_box = []
    door_ids_box = []
    for element in geometries:
        holes = None
        if element.name == 'wall':
            window_intrsct = lg.Windows_ids.get(element.id)
            door_intrsct = lg.Doors_ids.get(element.id)
            holes = (_common_holes(window_intrsct, door_intrsct) 
                     if window_intrsct and door_intrsct 
                     else window_intrsct or door_intrsct)

        if holes:
            polygons_coords = tuple(_devide_wall(element.id,
                                                 element.vector, 
                                                 holes,
                                                 len(holes),
                                                 polygons_vert = [], 
                                                 index = 0))

            vert_floats = numpy.concatenate(polygons_coords, axis=0).flatten()

            polygons = _add_normals(polygons_coords, flag=True)

        elif element.name == "floor":
            vert_floats = numpy.array(element.vector, dtype=numpy.float32).flatten()
            start_num = 0
            polygons = []
            for _ in range(len(element.vector)):
                polygons.append(numpy.array([start_num, 0]))
                start_num += 1
            polygons = numpy.array(polygons)
        else:
            vert_floats = numpy.array(element.vector, dtype=numpy.float32).flatten()

            polygons = _add_normals(element.vector)
   
        if element.name == 'window': 
            window_index = 0
            flag = True
            while flag:
                id = element.id + '_w' + str(window_index)
                if id in window_ids_box:
                    window_index += 1
                else:
                    window_ids_box.append(id)
                    flag = False
        elif element.name == 'door':
            door_index = 0
            flag = True
            while flag:
                id = element.id + '_d' + str(door_index)
                if id in door_ids_box:
                    door_index += 1
                else:
                    door_ids_box.append(id)
                    flag = False
        else:
            id = element.id

        vert_src = source.FloatSource(f"{id}", vert_floats, ('X', 'Y', 'Z'))

        normal = _define_normals(element.vector)
        normal_floats = numpy.array(normal, dtype=numpy.float32).flatten()
        normal_src = source.FloatSource(f"normal_{id}", normal_floats, ('X', 'Y', 'Z'))

        geom = geometry.Geometry(dae.mesh, f"{id}", f"{element.name}", [vert_src, normal_src])

        input_list = source.InputList()
        input_list.addInput(0, 'VERTEX', f"#{id}")
        input_list.addInput(1, 'NORMAL', f"#normal_{id}")

        triangles = geom.createTriangleSet(polygons, input_list, "materialref")

        geom.primitives.append(triangles)

        for extra_name in extras:
            extra_value = getattr(element, extra_name)
            extra_data = numpy.array(extra_value, dtype=numpy.string_)
            extra_src = source.NameSource(f'{extra_name}_{id}', extra_data, (f'{extra_name}',))
            geom.sourceById[f'{extra_name}_{id}'] = extra_src
  
        dae.mesh.geometries.append(geom)
        matnode = scene.MaterialNode("materialref", mtrl.user_material, inputs=[])
        geomnode = scene.GeometryNode(geom, [matnode])
        node = scene.Node(f"{id}", children=[geomnode])
        node_list.append(node)

    return node_list

def create_dae(levels, path, DAE_name):
    #create dae object
    dae = DAE()

    #creating all objects (walls/slabs/doors/windows)
    lg = LG(levels)

    #creating materials
    #green
    wall_mtrl = Material('wall_effect', 
                         'wall_material',
                         (0.0, 1.0, 0.0, 1.0),
                         (0.0, 1.0, 0.0, 1.0),
                         dae)
    #red
    floor_mtrl = Material('floor_effect', 
                          'floor_material',
                          (1.0, 0.0, 0.0, 1.0),
                          (1.0, 0.0, 0.0, 1.0),
                          dae)
    #blue
    window_mtrl = Material('window_effect', 
                           'window_material',
                           (0.0, 0.0, 1.0, 1.0),
                           (0.0, 0.0, 1.0, 1.0),
                           dae)
    #yellow
    door_mtrl = Material('door_effect', 
                           'door_material',
                           (1.0, 1.0, 0.0, 1.0),
                           (1.0, 1.0, 0.0, 1.0),
                           dae)
    

    # creating nodes for each category
    node_list = []

    node_list.append(_create_scene(dae, lg, lg.Walls, wall_mtrl, name='Wall_nodes', extras = ['type', 'thickness']))
    
    node_list.append(_create_scene(dae, lg, lg.Floor, floor_mtrl, name='Floor_nodes', extras = ['type', 'thickness']))

    node_list.append(_create_scene(dae, lg, lg.Windows, window_mtrl, name='Window_nodes', extras = ['type']))

    node_list.append(_create_scene(dae, lg, lg.Doors, door_mtrl, name='Door_nodes', extras = ['type']))

    
    #create scene, write and save
    myscene = scene.Scene("myscene", node_list)
    dae.mesh.scenes.append(myscene)
    dae.mesh.scene = myscene
    dae.mesh.write(path + DAE_name)
