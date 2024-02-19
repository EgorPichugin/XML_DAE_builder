import collada
from collada import asset, Collada, material
from shapely.wkt import loads
from shapely import Polygon
from tripy import earclip
from typing import Dict, List, Tuple

class DAE:
    def __init__(self) -> None:
        self.mesh = Collada()
        self.asset_info = collada.asset.Asset(title='DAE constructor',
                                              revision = 'v0.1',
                                              unitname = 'meter',
                                              unitmeter = 1.0,
                                              upaxis = asset.UP_AXIS.Z_UP,
                                              contributors = [asset.Contributor(author='EnterAR',
                                                                                authoring_tool='EnterAR')])
        self.mesh.assetInfo = self.asset_info

class LG(DAE):
    def __init__(self, levels) -> None:
        self.levels = levels
        self.name = 'library_geometries'
        self.Walls = []
        self.Floor = []
        self.Windows = []

        '''self.Windows_ids {'parent_id' : [
                                            [(x1, y1, z1),..., (x4, y4, z4)], 
                                            [(x1, y1, z1),...,(x4, y4, z4)]
                                           ]
                            }'''
        self.Windows_ids = {}
        self.Doors = []

        '''self.Doors_ids {'parent_id' : [
                                            [(x1, y1, z1),..., (x4, y4, z4)], 
                                            [(x1, y1, z1),...,(x4, y4, z4)]
                                         ]
                            }'''
        self.Doors_ids = {}
        self._parse_geometry()     
    
    def _parse_geometry(self):
        for level in self.levels:
            for lvl_value in level.values():
                height = lvl_value['properties']['level_height']
                elevation = lvl_value['properties']['level_elevation']

                top_point = elevation + height
                z_points = [elevation, top_point]
                zero = lvl_value['properties']['zero']

                #walls
                for wall in lvl_value['walls']:
                    self.Walls.append(Wall(wall, z_points))

                #floors
                for floor in lvl_value['floor']:
                    self.Floor.append(Floor(floor, elevation)) 

                #windows
                window_points = [elevation + 800, elevation + 3600]
                for window in lvl_value['windows']:
                    window_obj = Window(window, window_points)
                    self.Windows.append(window_obj)

                    if self.Windows_ids.get(window_obj.id) is None:
                        vector_list = []
                        vector_list.append(window_obj.vector)
                        self.Windows_ids[window_obj.id] = vector_list

                    elif self.Windows_ids.get(window_obj.id):
                        self.Windows_ids[window_obj.id].append(window_obj.vector)

                #doors
                door_points = [elevation, elevation + 2100]
                for door in lvl_value['doors']:
                    door_obj = Door(door, door_points)
                    self.Doors.append(door_obj)
                    sorted_vector = door_obj.vector

                    if sorted_vector[0][0] > sorted_vector[2][0] or \
                        (sorted_vector[0][0] == sorted_vector[2][0] and sorted_vector[0][1] > sorted_vector[2][1]):
                        sorted_vector.reverse()

                    if self.Doors_ids.get(door_obj.id) is None:
                        vector_list = []
                        vector_list.append(sorted_vector)
                        self.Doors_ids[door_obj.id] = vector_list

                    elif self.Doors_ids.get(door_obj.id):
                        self.Doors_ids[door_obj.id].append(sorted_vector)

class Wall(LG):
    def __init__(self, wall, z_points) -> None:
        self.name = 'wall'
        self.wall = wall
        self.id = self.wall['id']
        self.type = self.wall['type']
        self.thickness = self.wall['thickness']
        self.z_points = z_points
        self.vertices = self._get_vertices(self.wall, self.z_points)

    def _get_vertices(self, wall, z_points) -> Dict:
        vector = wall['vector']
        polygon = [(x, y, z) for (x, y) in vector for z in z_points]
        polygon[2], polygon[3] = polygon[3], polygon[2]
        wall['vector'] = polygon
        self.vector = polygon

        return wall

class Floor(LG):
    def __init__(self, floor, height) -> None:
        self.name = 'floor'
        self.floor = floor
        self.coords = self.floor['polygon']
        self.id = self.floor['id']
        self.type = self.floor['type']
        self.thickness = self.floor['thickness']
        self.height = height
        self.vertices = self._get_vertices(self.coords, self.height)

    def _get_vertices(self, floor: str, height) -> List[Tuple[int, int, int]]:
        #transfer str to Polygon class object
        poly_floor = loads(floor)

        #create list[Tuple(int,int)]
        exterior_coords = [(x, y) for (x, y) in poly_floor.exterior.coords]
        # print(f"extrior_coords type: {exterior_coords}")
        
        #tmp
        # holes = []
        # for i in poly_floor.interiors:
        #     coordinates = list(i.coords)
        #     exterior_coords += coordinates
        # print(exterior_coords)
        #tmp
        # pgn = Polygon(exterior_coords, holes)
        # print(pgn)

        #reshape into triangle forms list[Tuple(tuple(int, int), tuple(int, int))]
        # [((x1, y1), (x2, y2), (x3, y3)),..., ((xn-2, yn-2), (xn-1, yn-1), (xn, yn))]
        trngld_list = earclip(exterior_coords) 

        #reshape to list[Tuple(int, int)]
        # [(x1, y1), (x2, y2), (x3, y3),..., (xn, yn)]
        poly_coords = [item for sublist in trngld_list for item in sublist]
        # print(poly_coords)

        #add z point
        # [(x1, y1, z1), (x2, y2, z1), (x3, y3, z1),..., (xn, yn, z1)]
        polygon = [(x, y, height) for (x, y) in poly_coords]
        self.vector = polygon
        print(polygon)

        return polygon

class Door(LG):
    def __init__(self, door, door_points) -> None:
        self.name = 'door'
        self.door = door
        self.id = self.door['parent_id']
        self.type = self.door['type']
        self.door_points = door_points
        self.vertices = self._get_vertices(self.door, self.door_points)

    def _get_vertices(self, door, door_points) -> List[Tuple[int, int, int]]:
        vector = door['vector']
        polygon = [(x, y, z) for (x, y) in vector for z in door_points]
        polygon[2], polygon[3] = polygon[3], polygon[2]
        door['vector'] = polygon
        self.vector = polygon

        return door

class Window(LG):
    def __init__(self, window, window_points) -> None:
        self.name = 'window'
        self.window = window
        self.id = self.window['parent_id']
        self.type = self.window['type']
        self.window_points = window_points
        self.vertices = self._get_vertices(self.window, self.window_points)

    def _get_vertices(self, window, window_points) -> List[Tuple[int, int, int]]:
        vector = window['vector']
        polygon = [(x, y, z) for (x, y) in vector for z in window_points]
        polygon[2], polygon[3] = polygon[3], polygon[2]
        window['vector'] = polygon
        self.vector = polygon

        return window

class Material(LG):
    def __init__(self,
                 effect_name,
                 material_name,
                 user_diffuse,
                 user_transparent,
                 dae) -> None:
        self.effect_name = effect_name
        self.material_name = material_name
        self.user_effect = material.Effect(effect_name,
                                           [],
                                           "phong",
                                           double_sided=True,
                                           diffuse=user_diffuse,
                                           transparent=user_transparent)

        self.user_material = material.Material(material_name,
                                               material_name,
                                                self.user_effect)
        self._add_material(dae, self.user_effect, self.user_material)

    def _add_material(self, dae, effect, material) -> None:
        dae.mesh.effects.append(effect)
        dae.mesh.materials.append(material)
