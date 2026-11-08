"""Übersicht über den Dateiinhalt:

Die Klasse Users verwaltet alle Benutzer des Online-Marktplatzes.
Sie erbt von `Praktikumsgruppen` und liest Benutzer- sowie Freundschaftsdaten
aus den CSV-Dateien (`user.csv`, `friends.csv`) ein. Sie stellt Methoden zur
Passwortüberprüfung, Freundschaftsempfehlung, Abstands- und Verbindungsberechnung bereit.
"""

# Status: FINAL, dgaida2, 15.10.2024

# definiert die Klasse Users.
# Users ist eine Menge von disjunkten Mengen (nur für drittes Praktikum) von der Klasse User,
# damit man Users in Praktikumsgruppen einsortieren kann. Für das erste und zweite Praktikum ist die Klasse
# Praktikumsgruppe lediglich ein Dictionary
# in der Klasse werden die csv-Dateien user.csv und friends.csv gelesen.

from typing import Any, Dict, List, Optional, Tuple, Union
import ast
import csv
import marketplace.user
import marketplace.praktikumsgruppen
import math
import os
from collections import deque
import networkx as nx


class Users(marketplace.praktikumsgruppen.Praktikumsgruppen):
    """Klasse zur Verwaltung aller registrierten Benutzer und ihrer Freundschaften.

    Attributes:
        _groupnumbers (List[int]): Liste der Gruppennummern der eingelesenen Benutzer.
    """
    GRAPH_FILE = "nrw_drive.graphml"
    ROAD_FILTER = '["highway"~"motorway|trunk|primary|secondary"]'

    # *** CONSTRUCTORS ***
    def __init__(self, csvfile: str, *args: Any) -> None:
        """Initialisiert das Users-Objekt und liest Daten aus CSV-Dateien ein.

        Args:
            csvfile (str): Pfad zur Benutzer-CSV-Datei (z. B. 'user.csv').
            *args (Any): Variable Argumente.

        Raises:
            FileNotFoundError: Falls die CSV-Datei nicht gefunden wurde.
        """
        super().__init__()

        self._map_graph = None  # Straßengraph, wird nur einmal geladen
        self._osmnx_failed = False  # True, falls osmnx/Download nicht klappt
        self._distance_cache: Dict[Tuple[str, str], float] = {}

        self._read_users_from_csvfile(csvfile)
        self._read_friends_csv('friends.csv')

        # erstelle Praktikumsgruppen als Menge disjunkter Mengen bzw. als dictionary (1. und 2. Praktikum)
        super().create_groups(list(self.keys()), self._groupnumbers)

    # *** PUBLIC SET methods ***

    # *** PUBLIC methods ***

    def add(self, user_id: str, password: str, name_family: str = "", name_first: str = "",
            gps_coord: Tuple[Optional[float], Optional[float]] = (None, None), address: str = "") -> None:
        """Adds the given user with user_id to the internal dictionary.

        Args:
            user_id (str): GM-ID / unique user identifier.
            password (str): Password of user.
            name_family (str, optional): Family name of user. Defaults to "".
            name_first (str, optional): First name of user. Defaults to "".
            gps_coord (tuple, optional): (latitude, longitude) coordinates. Defaults to (None, None).
            address (str, optional): Address string corresponding to GPS coordinates. Defaults to "".
        """
        self[user_id] = marketplace.user.User(user_id, password, name_family, name_first, gps_coord, address)

    def calc_distance_between_users(self, user_id1: str, user_id2: str) -> float:
        """Calculates distance between GPS coordinates of two users.

        Args:
            user_id1 (str): First user ID.
            user_id2 (str): Second user ID.

        Returns:
            float: Calculated distance between the two users.
        """
        # TODO for students: calculate distance between gps coordinates of user1 and user2 using a map and an
        #  algorithm that calculates the shortest distance on the map

        key = (min(user_id1, user_id2), max(user_id1, user_id2))
        if key in self._distance_cache:
            return self._distance_cache[key]

        lat1, lon1 = self[user_id1].gps_coords()
        lat2, lon2 = self[user_id2].gps_coords()
        if None in (lat1, lon1, lat2, lon2):
            return float("inf")

        distance = None
        if not self._osmnx_failed:
            try:
                import osmnx as ox
                graph = self._get_map_graph()
                origin = ox.distance.nearest_nodes(graph, lon1, lat1)  # X = Längengrad, Y = Breitengrad
                destination = ox.distance.nearest_nodes(graph, lon2, lat2)
                path = ox.routing.shortest_path(graph, origin, destination, weight="length")
                distance = float(nx.path_weight(graph, path, weight="length")) if path else float("inf")
            except Exception as e:
                print("osmnx nicht verfügbar, nutze Luftlinie:", e)
                self._osmnx_failed = True
        if distance is None:
            distance = self._beeline_distance(user_id1, user_id2)

        self._distance_cache[key] = distance
        return distance
        return float(distance)

    # *** PUBLIC GET methods ***

    def _get_map_graph(self):
        """Lädt den Straßengraphen einmal herunter, speichert ihn lokal und lädt ihn danach nur noch aus der Datei."""
        if self._map_graph is None:
            import osmnx as ox
            if os.path.exists(self.GRAPH_FILE):
                self._map_graph = ox.load_graphml(self.GRAPH_FILE)
            else:
                coords = [u.gps_coords() for u in self.values() if None not in u.gps_coords()]
                lats = [c[0] for c in coords]
                lons = [c[1] for c in coords]
                m = 0.1  # Rand in Grad
                bbox = (min(lons) - m, min(lats) - m, max(lons) + m, max(lats) + m)  # (West, Süd, Ost, Nord)
                print("Lade Straßengraphen, das kann einige Minuten dauern ...")
                self._map_graph = ox.graph.graph_from_bbox(bbox, network_type="drive",
                                                           custom_filter=self.ROAD_FILTER)
                ox.save_graphml(self._map_graph, self.GRAPH_FILE)
        return self._map_graph

    def _beeline_distance(self, user_id1: str, user_id2: str) -> float:
        """Luftlinie in Metern (Haversine-Formel)."""
        lat1, lon1 = self[user_id1].gps_coords()
        lat2, lon2 = self[user_id2].gps_coords()
        if None in (lat1, lon1, lat2, lon2):
            return float("inf")
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dp, dl = p2 - p1, math.radians(lon2 - lon1)
        a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        return 2 * 6371000 * math.asin(math.sqrt(a))


    def get_name_of_user(self, user_id: str) -> str:
        """Gibt den vollständigen Namen des Benutzers zurück.

        Args:
            user_id (str): Benutzer-ID.

        Returns:
            str: Name des Benutzers.

        Raises:
            KeyError: Falls die `user_id` nicht existiert.
        """
        node = self[user_id]
        return node.name()

    def num_users(self) -> int:
        """Gibt die Gesamtanzahl registrierter Benutzer zurück.

        Args:
            None

        Returns:
            int: Anzahl der Benutzer.

        Raises:
            None
        """
        return len(self.keys())

    def password_valid(self, user_id: str, password: str) -> bool:
        """Prüft, ob das Passwort für den angegebenen Benutzer gültig ist.

        Args:
            user_id (str): Benutzer-ID.
            password (str): Passwort.

        Returns:
            bool: `True`, wenn Passwort korrekt, sonst `False`.

        Raises:
            KeyError: Falls die `user_id` nicht existiert.
        """
        return self[user_id].password_valid(password)

    def get_user_pretty_print_for_list(self, user_id: str) -> str:
        """Erstellt eine formatierte Repräsentation eines Benutzers für Listboxen.

        Args:
            user_id (str): Benutzer-ID.

        Returns:
            str: Der formatierte Benutzer-String inkl. Praktikumsgruppen-Info.

        Raises:
            KeyError: Falls `user_id` nicht existiert.
        """
        return (self[user_id].pretty_print() + "\t in Praktikumsgruppe repräsentiert durch: " +
                str(self.find_byid(user_id, True)))

    def get_friends_andgroupmembers_pretty_print(self, user_id: str) -> List[str]:
        """Returns list of friends and group members for the given user_id that is shown on GUI.

        Args:
            user_id (str): usually the current user id

        Returns:
            List[str]: Liste formatierter Strings.

        Raises:
            KeyError: Falls `user_id` nicht existiert.
        """
        friends = self[user_id].friends()
        friend_names = [self.get_user_pretty_print_for_list(friend) for friend in friends]

        group_members = self.get_groupmembers(user_id)
        if group_members is None:
            return friend_names

        # entferne mich selbst aus der Gruppe, da ich ja weiß, dass ich (user_id) in der Gruppe bin
        if user_id in group_members:
            group_members.remove(user_id)

        group_members_pp = [self.get_user_pretty_print_for_list(member) for member in group_members]
        return friend_names + group_members_pp

    def get_mutual_friends(self, user_id: str) -> Dict[str, int]:
        """Ermittelt gemeinsame Freunde (Freunde von Freunden) und deren Häufigkeit.

        Args:
            user_id (str): usually the current user id

        Returns:
            Dict[str, int]: dictionary with friends of the friends of given user_id together with the information with how many friends of user_id these friends are friends with

        Raises:
            KeyError: Falls `user_id` nicht existiert.
        """
        friends = self[user_id].friends()
        mutual_friends_count: Dict[str, int] = {}

        for friend in friends:
            friend_friends = self[friend].friends()
            for mutual_friend in friend_friends:
                if mutual_friend != user_id and mutual_friend not in friends:
                    if mutual_friend in mutual_friends_count:
                        mutual_friends_count[mutual_friend] += 1
                    else:
                        mutual_friends_count[mutual_friend] = 1

        return mutual_friends_count

    def suggest_friends(self, user_id: str, num_common_friends: int = 2,
                        distance_threshold: float = 20000, pretty_print: bool = True) -> List[str]:
        """Suggests users to the given user_id that
        (1) are friends with at least num_common_friends friends of user_id or
        (2) that live nearby the given user_id (closer as distance_threshold) and are friends of friends of friends...
        (see are_users_connected())

        Args:
            user_id (str): usually the current user id
            num_common_friends (int): only suggest users that are at least friends with two of the user_ids friends
            distance_threshold (float): only suggest users that live closer to the given user_id as this threshold value
            pretty_print (bool): if True, then call pretty_print() on all suggested friends before returning them

        Returns:
            List[str]: list of suggested friends. the first part of the list should contain common friends, ordered so that users with maximum number of common friends appear first. the second part of the list should contain all users that live close by, again sorted, so that the direct neighbour comes first.

        Raises:
            KeyError: Falls `user_id` nicht existiert.
        """
        mutual_friends_count = self.get_mutual_friends(user_id)
        # TODO for students: Implement this method by filling the list suggested_friends

        common_friends = [uid for uid, count in mutual_friends_count.items() if count >= num_common_friends]
        common_friends.sort(key=lambda uid: mutual_friends_count[uid], reverse=True)

        # (2) Nutzer in der Nähe, die über das Freundesnetzwerk (bis 3. Grades) mit mir verbunden sind
        my_friends = self[user_id].friends()
        connected = self._users_within_degree(user_id, 3)
        nearby: List[Tuple[float, str]] = []
        for uid in connected:
            if uid == user_id or uid in my_friends or uid in common_friends:
                continue
            # Luftlinie <= Fahrstrecke: wer schon per Luftlinie zu weit weg ist, braucht keine teure osmnx-Berechnung
            if self._beeline_distance(user_id, uid) >= distance_threshold:
                continue
            distance = self.calc_distance_between_users(user_id, uid)
            if distance < distance_threshold:
                nearby.append((distance, uid))
        nearby.sort()  # nächster Nachbar zuerst

        suggested_friends = common_friends + [uid for _, uid in nearby]

        if pretty_print:
            suggested_friends = [self[friend].pretty_print() for friend in suggested_friends]

        return suggested_friends

    def are_users_connected(self, user_id1: str, user_id2: str, degree: int = 3) -> bool:
        """Prüft mittels Breitensuche, ob zwei Benutzer über Freundschaftskanten verbunden sind.

        Args:
            user_id1 (str): a user that we are searching a friend for
            user_id2 (str): another user, where we want to check whether it is somehow friends with user_id1 over some other shared friends
            degree (int): only look for possible friend connections up to this degree of friendship. Defaults to 3.

        Returns:
            bool: True, if user_id1 and user_id2 are friends over some edges up to the given degree, else False

        Raises:
            None
        """
        if user_id1 not in self or user_id2 not in self:
            return False

        # TODO for students: Implement this method

        return user_id2 in self._users_within_degree(user_id1, degree)

    # *** PUBLIC STATIC methods ***
    def _users_within_degree(self, user_id: str, degree: int) -> Dict[str, int]:
        """Breitensuche (BFS): alle Nutzer, die höchstens `degree` Freundschaftskanten entfernt sind.

        Returns:
            Dict[str, int]: user_id -> Freundschaftsgrad (0 = ich selbst, 1 = Freund, 2 = Freund eines Freundes, ...)
        """
        depth = {user_id: 0}
        queue = deque([user_id])
        while queue:
            current = queue.popleft()
            if depth[current] >= degree:
                continue
            for friend in self[current].friends():
                if friend in self and friend not in depth:
                    depth[friend] = depth[current] + 1
                    queue.append(friend)
        return depth
    # *** PRIVATE methods ***

    def _read_users_from_csvfile(self, csvfile: str) -> None:
        """
        Read the given csvfile that contains all students that want to do the Praktikum in this semester
        including their GM-ID, Names and number of their Praktikumsgruppe

        :param csvfile: csv file that has to be created at the beginning of the semester containing all students
        in this semester
        """
        with open(csvfile, newline='', encoding='utf-8-sig') as f:
            csvreader = csv.reader(f)
            # Skip header row
            next(csvreader)

            # private member variable containing the Praktikumsgruppe number of the students in the order that the
            # students are read from the csv file
            self._groupnumbers = []

            for row in csvreader:
                user_id, name_family, name_first, password, groupnum, gps_coords, address = row
                # macht aus String wieder das Tuple mit long und lat Koordinaten
                # (literal_eval statt eval, damit aus der CSV-Datei kein beliebiger Code ausgeführt werden kann)
                gps_coords_tuple = ast.literal_eval(gps_coords)
                self.add(user_id, password, name_family, name_first, gps_coords_tuple, address)
                self._groupnumbers.append(int(groupnum))

    def _read_friends_csv(self, file_path: str) -> None:
        """
        Funktion, um die friends.csv-Datei einzulesen und ein Dictionary zu erstellen
        :param file_path: path to friends.csv file
        """
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            csvreader = csv.reader(f)
            next(csvreader)  # Überspringe die Header-Zeile
            for row in csvreader:
                user_id = row[0]
                friends = row[1].split(', ')
                self[user_id].friends_add_list(friends)
                for friend in friends:  # gehe alle Freunde durch und füge user_id ebenfalls als Freund hinzu
                    self[friend].friends_add(user_id)

    # *** PUBLIC methods to return class properties ***

    # *** PRIVATE variables ***
