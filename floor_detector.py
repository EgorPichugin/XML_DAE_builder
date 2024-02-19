import shapely
from shapely.ops import polygonize, unary_union
from graph import Graph

def add_floors(level):
    level['floors'] = _detect_floors(level)
    return level

def _create_polygons(walls):
    lines = []

    for v in walls:
        lines.append((v[0], v[1]))
    return polygonize(lines)

def _create_matrix(plgns):
    adj_mtrx = []
    gap = 50

    for i in range(len(plgns)):
        row = []
        for j in range(len(plgns)):
            if i == j:
                row.append(1)
                continue
            d = shapely.distance(plgns[i], plgns[j])
            if d < gap:
                row.append(1)
            else:
                row.append(0)
        adj_mtrx.append(row)
    return adj_mtrx
    
def _create_clusters(adj_mtrx, g):
    clusters = []

    for i in range(len(adj_mtrx)):
        visited = []
        if i in visited:
            continue
        neibors = g.BFS(i)
        is_new_cluster = True
        for n in neibors:
            visited.append(n)
            for i in range(len(clusters)):
                if n in clusters[i]:
                    clusters[i] = list(set(clusters[i] + neibors))
                    is_new_cluster = False
                    break
        if is_new_cluster:
            clusters.append(neibors)
    return clusters

def _unify_plgns(clusters, plgns):
    union_plgns = []

    for cl in clusters:
        pls = []
        for i in cl:
            pls.append(plgns[i])
        union_plgns.append(unary_union(pls))
    return union_plgns

def _check_geom(union_plgns):
    try:
        for geom in union_plgns:
            if geom.geom_type == 'MultiPolygon':
                for pl in geom.geoms:
                    union_plgns.append(pl)
                union_plgns.remove(geom)
    except Exception as ex:
        print(ex)

def _detect_floors(level):
    walls = [w['vector'] for w in level['walls']]
    plgns = _create_polygons(walls)
    adj_mtrx = _create_matrix(plgns)

    g = Graph()
    
    for i in range(len(adj_mtrx)):

        for j in range(len(adj_mtrx[i])):
            if adj_mtrx[i][j] == 1:
                g.addEdge(i, j)

    clusters = _create_clusters(adj_mtrx, g)
    union_plgns = _unify_plgns(clusters, plgns)
    _check_geom(union_plgns)

    pts = []
    for pl in union_plgns:
        xx, yy = pl.exterior.coords.xy
        pts.append(list(zip(xx, yy)))

    return pts
