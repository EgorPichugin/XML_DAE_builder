import xml.etree.ElementTree as ET
import xml.dom.minidom as xmldm
import shapely

def build_xml(levels_data):
    # root
    model = ET.Element('MODEL')
    levels = ET.SubElement(model, 'LEVELS')
    for level_data in levels_data:
        level = ET.SubElement(levels, 'LEVEL')

        # properties
        level_name = ET.SubElement(level, 'NAME')
        level_name.text = level_data['properties']['level_name']

        level_zero = ET.SubElement(level, 'ZERO')
        level_zero.text = _tuple2wkt_point(level_data['properties']['zero'])

        level_elevation = ET.SubElement(level, 'ELEVATION')
        level_elevation.text = str(level_data['properties']['level_elevation'])

        level_height = ET.SubElement(level, 'HEIGHT')
        level_height.text = str(level_data['properties']['level_height'])

        # floors
        floors = ET.SubElement(level, 'FLOORS')

        for fl in level_data['floor']:
            floor = ET.SubElement(floors, 'FLOOR')
            floor_id = ET.SubElement(floor, 'ID')
            floor_id.text = fl['id']
            floor_type = ET.SubElement(floor, 'TYPE')
            floor_type.text = fl['type']
            floor_thickness = ET.SubElement(floor, 'THICKNESS')
            floor_thickness.text = str(fl['thickness'])
            floor_polygon = ET.SubElement(floor, 'POLYGON')
            floor_polygon.text = str(shapely.wkt.loads(fl['polygon']))

        # walls
        walls = ET.SubElement(level, 'WALLS')

        walls_data = level_data['walls']
        doors_data = level_data['doors']
        windows_data = level_data['windows']

        for wl in walls_data:

            wall_doors = []
            for dr in doors_data:
                if dr['parent_id'] == wl['id']:
                    wall_doors.append(dr)

            wall_wins = []
            for wn in windows_data:
                if wn['parent_id'] == wl['id']:
                    wall_wins.append(wn)

            wall = ET.SubElement(walls, 'WALL')
            wall_id = ET.SubElement(wall, 'ID')
            wall_id.text = wl['id']
            wall_type = ET.SubElement(wall, 'TYPE')
            wall_type.text = wl['type']
            wall_thickness = ET.SubElement(wall, 'THICKNESS')
            wall_thickness.text = str(wl['thickness'])
            wall_vector = ET.SubElement(wall, 'VECTOR')
            wall_vector.text = _vector2wkt_linestr(wl['vector'])

            if wall_doors:
                doors = ET.SubElement(wall, 'DOORS')
                for dr in wall_doors:
                    door = ET.SubElement(doors, 'DOOR')
                    door_type = ET.SubElement(door, 'TYPE')
                    door_type.text = dr['type']
                    door_side = ET.SubElement(door, 'SIDE')
                    door_side.text = str(dr['side'])
                    door_vector = ET.SubElement(door, 'VECTOR')
                    door_vector.text = _vector2wkt_linestr(dr['vector'])

            if wall_wins:
                wins = ET.SubElement(wall, 'WINDOWS')
                for wn in wall_wins:
                    win = ET.SubElement(wins, 'WINDOW')
                    win_type = ET.SubElement(win, 'TYPE')
                    win_type.text = wn['type']
                    win_vector = ET.SubElement(win, 'VECTOR')
                    win_vector.text = _vector2wkt_linestr(wn['vector'])

    xml_str = ET.tostring(model, encoding='unicode', method='xml')
    return xml_str


def _tuple2wkt_point(tpl: tuple):
    p = shapely.Point(tpl)
    return p.wkt

def _vector2wkt_linestr(lst: list):
    l = shapely.LineString(lst)
    return l.wkt

# def _vector2wkt_polygon(lst: list):
#     p = shapely.Polygon(lst)
#     return p.wkt