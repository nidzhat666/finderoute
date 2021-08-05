import time, re, sqlite3, math, random, json
from math import sin, cos, sqrt, atan2, radians, acos, asin, floor
from io import StringIO

"""This modules documentation."""
AIRAC_PATH = 'AIRAC2014/'
"""Turns out the comment is rendered as a docstring if we put it underneath."""

con = sqlite3.connect('little_navmap_navigraph.sqlite', check_same_thread=False)
cur = con.cursor()


class Error(Exception):
    pass


class AirportNotFound(Error):

    def __init__(self, apt):
        self.apt = apt

    def __str__(self):
        return f"Airport {self.apt} not found"


class ValueTooLargeError(Error):
    pass


class Graph(object):
    """Commenting members of a class."""

    def __init__(self, adjacency_list=dict(), edge_weights=dict()):
        self.__adjacency_list = adjacency_list.copy()
        self.__edge_weights = edge_weights.copy()

    def add_edge(self, u, v, w):
        """ Add a new edge u -> v to graph with edge weight w. """
        self.__edge_weights[u, v] = w
        # print(airway)
        if u not in self.__adjacency_list:
            self.__adjacency_list[u] = set()
        self.__adjacency_list[u].add(v)

    def get_node(self, u):
        """This modules documentation."""
        return self.__adjacency_list.get(u)

    def get_edge_weight(self, u, v):
        """ Get edge weight of edge between u and v. """
        return self.__edge_weights[u, v]

    def get_adjacent_nodes(self, u):
        """ Get nodes adjacent to u. """
        return self.__adjacency_list.get(u, set())

    def get_number_of_nodes(self):
        """ Return the total number of nodes in graph. """
        return len(self.__adjacency_list)

    def get_nodes(self):
        """ Return all nodes in this graph. """
        return self.__adjacency_list.keys()

    def __str__(self):
        """This modules documentation."""
        io = StringIO()
        N = self.get_number_of_nodes()
        print("Directed, acyclic graph with %d nodes" % N, file=io)
        for u in self.get_nodes():
            adj = self.get_adjacent_nodes(u)
            print("Node %s: connected to %d nodes" % (u, len(adj)), file=io)
        return io.getvalue()


def generate_random_graph(nvertices, edge_density, min_weight, max_weight):
    """ Generate random graph with `nvertices`. """
    G = Graph()
    for u in range(nvertices):
        nadj = int(nvertices * edge_density)
        while len(G.get_adjacent_nodes(u)) < nadj:
            v = random.randrange(nvertices)
            if u == v:
                continue
            w = random.randint(min_weight, max_weight)
            G.add_edge(u, v, w)
    return G


class AbstractDijkstraSPF(object):
    """ Dijkstra's shortest path algorithm, abstract class. """

    def __init__(self, G, s):
        """ Calculate shortest path from s to other nodes in G. """
        self.__dist = dist = dict()
        self.__prev = prev = dict()
        visited = set()
        queue = set()

        dist[s] = 0
        prev[s] = s
        queue.add(s)

        while queue:
            u = min(queue, key=dist.get)
            for v in self.get_adjacent_nodes(G, u):
                if v in visited:
                    continue
                alt = self.get_distance(u) + self.get_edge_weight(G, u, v)
                if alt < self.get_distance(v):
                    dist[v] = alt
                    prev[v] = u
                    queue.add(v)
            queue.remove(u)
            visited.add(u)

    @staticmethod
    def get_adjacent_nodes(G, u):
        raise NotImplementedError()

    @staticmethod
    def get_edge_weight(G, u, v):
        raise NotImplementedError()

    def get_distance(self, u):
        """ Return the length of shortest path from s to u. """
        return self.__dist.get(u, math.inf)

    def get_path(self, v):
        """ Return the shortest path to v. """
        path = [v]
        while self.__prev[v] != v:
            v = self.__prev[v]
            # print(self.__prev[v]+"->"+v)
            path.append(v)
        return path[::-1]


class DijkstraSPF(AbstractDijkstraSPF):

    @staticmethod
    def get_adjacent_nodes(G, u):
        return G.get_adjacent_nodes(u)

    @staticmethod
    def get_edge_weight(G, u, v):
        return G.get_edge_weight(u, v)


def rad(x):
    PI = 3.1415926535898
    return x * PI / 180.0


def dist_calculate(lat1, lon1, lat2, lon2):
    EARTH_RADIUS = 3440.0348679829
    radLat1 = rad(lat1)
    radLat2 = rad(lat2)
    a = radLat1 - radLat2
    b = rad(lon1) - rad(lon2)
    s = 2 * asin(sqrt(pow(sin(a / 2), 2) +
                      cos(radLat1) * cos(radLat2) * pow(sin(b / 2), 2)))
    s = s * EARTH_RADIUS
    return s


def float_conv(val):
    print('before -> ' + str(val))
    val = float(val)
    if val > 0:
        print(floor(val))
        return floor(val)
    else:
        print(int(val))
        return int(val)


class RF:
    __from = "BPK,51.749722,-0.106667"
    __to = "ERLEV,40.730278,49.241944"
    origin_airport = {}
    dest_airport = {}
    SID = None
    STAR = None

    airways = {}

    def get_from(self):
        return self.__from

    def get_to(self):
        return self.__to

    def __init__(self):
        self.graph_build()

    def origin_dest_apt(self, origin, dest):
        origin = origin.upper()
        dest = dest.upper()
        exec = """
        SELECT
            x.ident,
            x.airport_id,
            x.name,
            x.laty,
            x.lonx
        FROM
            airport x
        WHERE
            x.ident = "{}"
        """
        try:
            origin = [i for i in [i for i in cur.execute(exec.format(origin)).fetchone()]]
        except:
            raise AirportNotFound(origin)
        try:
            dest = [i for i in [i for i in cur.execute(exec.format(dest)).fetchone()]]
        except:
            raise AirportNotFound(dest)
        self.__from = tuple(origin)
        self.__to = tuple(dest)

    def sid(self, origin):
        exec = f"""
        SELECT
            y.fix_ident
        FROM
            approach x
            INNER JOIN approach_leg y ON y.approach_id = x.approach_id
        WHERE
            x.airport_ident = "{origin.upper()}"
            AND (y.arinc_descr_code like "%EE%" or y.arinc_descr_code like "EY")
            AND x.suffix = "D"
            and(x.type = "GPS");
        """
        sids = []
        sids1 = []
        res = cur.execute(exec).fetchall()
        for i in res:
            if i[0] not in sids1:
                sids1.append(i[0])
                a = cur.execute(
                    f"select x.waypoint_id, x.ident, x.laty, x.lonx from waypoint x where x.ident = \"{i[0]}\"").fetchone()
                sids.append(a)
        for i in sids:
            self.graph.add_edge(self.__from, (i[1], i[0], i[2], i[3]),
                                dist_calculate(i[2], i[3], self.__from[-2], self.__from[-1]))

    def star(self, dest):
        exec = f"""
        SELECT
            y.fix_ident
        FROM
            approach x
            INNER JOIN approach_leg y ON y.approach_id = x.approach_id
        WHERE
            x.airport_ident = "{dest.upper()}"
            AND y.type = "IF"
            AND x.suffix = "A"
            and(x.type = "GPS");
        """
        star = []
        star1 = []
        res = cur.execute(exec).fetchall()
        for i in res:
            if i[0] not in star1:
                star1.append(i[0])
                a = cur.execute(
                    f"select x.waypoint_id, x.ident, x.laty, x.lonx from waypoint x where x.ident = \"{i[0]}\"").fetchone()
                star.append(a)
        for i in star:
            self.graph.add_edge((i[1], i[0], i[2], i[3]), self.__to,
                                dist_calculate(i[2], i[3], self.__to[-2], self.__to[-1]))

    def input_info(self, origin, dest):
        self.origin_dest_apt(origin, dest)
        self.sid(origin)
        self.star(dest)
        # self.sid(origin)

    def graph_build(self):
        self.graph = Graph()
        exec = """
        SELECT
            x.airway_name,
            x.direction,
            y.ident as "from",
            y.laty,
            y.lonx,
            z.ident as "to",
            z.laty,
            z.lonx,
            x.maximum_altitude,
            y.waypoint_id,
            z.waypoint_id
        FROM
            airway x
            INNER JOIN waypoint y ON x.from_waypoint_id = y.waypoint_id
            INNER JOIN waypoint z ON x.to_waypoint_id = z.waypoint_id
        """
        for row in cur.execute(exec):
            row = list(row)
            if row[-3] > 20000:
                self.graph.add_edge((row[2], row[-2], row[3], row[4]), (row[5], row[-1], row[6], row[7]),
                                    dist_calculate(row[3], row[4], row[6], row[7]))
                self.airways[(row[2], row[-2], row[3], row[4]), (row[5], row[-1], row[6], row[7])] = row[0]
                # print((row[2],row[-2],row[3], row[4]), (row[5],row[-1],row[6], row[7]))
                # if row[1] == "N":
                self.graph.add_edge((row[5], row[-1], row[6], row[7]), (row[2], row[-2], row[3], row[4]),
                                    dist_calculate(row[3], row[4], row[6], row[7]))
                self.airways[(row[5], row[-1], row[6], row[7]), (row[2], row[-2], row[3], row[4])] = row[0]

    def find_path(self):
        self.dijkstra = DijkstraSPF(self.graph, self.__from)
        self.path = self.dijkstra.get_path(self.__to)
        return self.path

    def get_distance(self):
        return self.dijkstra.get_distance(self.__to)

    def filter_route(self):
        self.filtered_path = []
        path = list(zip(self.path, self.path[1:]))
        airway = ''
        for i in path[1:-1]:
            aws = self.airways[i]
            if airway != aws:
                if self.filtered_path:
                    self.filtered_path[-1] = i[0][0]
                else:
                    self.filtered_path.append(i[0][0])
                self.filtered_path.append(aws)
                self.filtered_path.append(i[1][0])
                airway = aws
            else:
                self.filtered_path[-1] = i[1][0]
        return self.filtered_path

    def get_route_json(self):
        return json.dumps(self.path)
