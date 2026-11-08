"""Übersicht über den Dateiinhalt:

Implementiert die Disjoint-Set-Datenstruktur (Union-Find) mit `SetNode` und `Praktikumsgruppen`.
Ermöglicht das Zusammenfassen von Benutzern in Praktikumsgruppen (Gruppenbildung,
Union, Find mit Pfadkomprimierung).
"""

# Status: FINAL, dgaida2, 15.10.2024

# Definiert die Klassen Praktikumsgruppen und SetNode, implementiert als Menge von disjunkten Mengen (Praktikum 3) oder als Dictionary (Praktikum 1 und 2)
#
from typing import Any, List, Optional, Union, Dict


class SetNode:
    """Klasse zur Repräsentation eines Knotens in einer Disjoint-Set-Struktur (Union-Find).

    Attributes:
        _parent (SetNode): Zeiger auf den Eltern-Knoten (self bei Wurzeln).
        _weight (int): Anzahl der Knoten im Teilbaum.
    """

    # TODO for students: die Klasse user.User erbt von SetNode. diese Klasse wird eigentlich erst in Praktikum 3 benötigt.
    #     für Praktikum 1 und 2 müsste User nicht von dieser Klasse erben

    # *** CONSTRUCTORS ***
    def __init__(self) -> None:
        """Initialisiert einen SetNode als eigene Wurzel mit Gewicht 1.

        Args:
            None

        Raises:
            None
        """
        # TODO for students (Praktikum 1): ergänzen Sie hier die private Membervariable _praktikumsgruppe
        self._praktikumsgruppe: Optional[int] = None  # Nummer der Praktikumsgruppe, None = noch keiner Gruppe zugeordnet
        # Optional bedeutet. dass da entweder int oder None liegen kann
        # TODO: werden nur für Praktikum 3 benötigt
        self._parent: SetNode = self   # parent Knoten des SetNode Objekts. self bedeutet, dass der Knoten ein Wurzelknoten ist
        self._weight: int = 1      # Gewicht (Anzahl Knoten) des (Teil-)Baumes, der in dem SetNode Objekt verwurzelt ist
        # Alternative: Rank-based Quick Union
        # self._rank = 0

    # *** PUBLIC SET methods ***
    def set_parent(self, parent: "SetNode") -> None:
        self._parent = parent
    def set_weight(self, weight: int) -> None:
        self._weight = weight
    def parent(self) -> "SetNode":
        return self._parent
    def weight(self) -> int:
        return self._weight

    # TODO: implementieren Sie in Praktikum 3 die benötigten Methoden

    # *** PUBLIC methods to return class properties ***

    # TODO: implementieren Sie in Praktikum 3 die benötigten Methoden

class Praktikumsgruppen(dict):
    """Klasse zur Repräsentation einer Sammlung disjunkter Mengen (Praktikumsgruppen).

    In Praktikum 1 und 2: Dictionary containing all students. Die Klasse user.Users erbt von dieser Klasse.
    In Praktikum 3: Class representing a collection of disjoint sets for grouping users into practical groups.

    Methods:
        find(node): Finds the root of the set containing the node, with path compression.
        find_byid(user_id, return_id=False): Finds the root of the set containing the user by ID.
        union(user_id1, user_id2): Unions the sets containing the two users.
        create_groups(user_ids, groupnumbers): Creates groups from the provided user IDs and group numbers.
        get_groupmembers(user_id): Gets the members of the group containing the user.
        print_ds(): Prints the disjoint set structure.

    Attributes:
        None (erbt von dict).
    """

    # *** CONSTRUCTORS ***
    def __init__(self) -> None:
        """Initialisiert eine neue Praktikumsgruppen-Instanz.

        Args:
            None

        Raises:
            None
        """
        super().__init__()

    # *** PUBLIC methods ***

    # TODO in Praktikum 3: implement find(node), find_byid(user_id, return_id=False) and 
    #  union(user_id1, user_id2)
    def find(self, node: SetNode) -> SetNode:
        root = node
        while root.parent() is not root:
            root = root.parent()
        current = node
        while current is not root:
            next_node = current.parent()  # запомнить, кто выше
            current.set_parent(root)  # перевесить прямо на корень
            current = next_node  # перейти к тому, кто был выше
        return root


    def find_byid(self, user_id: str, return_id: bool = False) -> Union[Any, str]:
        node = self[user_id]
        root = self.find(node)
        if return_id:
            return root.id()
        return root

    def union(self, user_id1: str, user_id2: str) -> None:
        root1 = self.find_byid(user_id1)
        root2 = self.find_byid(user_id2)
        if root1 is root2:
            return
        if root1.weight() < root2.weight():
            root1.set_parent(root2)
            root2.set_weight(root1.weight() + root2.weight())
        else:
            root2.set_parent(root1)
            root1.set_weight(root1.weight() + root2.weight())


    def create_groups(self, user_ids: List[str], groupnumbers: List[int]) -> None:
        first_of_group: Dict[int, str] = {}
        for user_id, groupnumber in zip(user_ids, groupnumbers):
            if groupnumber not in first_of_group:
                first_of_group[groupnumber] = user_id  # erster dieser Gruppe
            else:
                self.union(first_of_group[groupnumber], user_id)

                # *** PUBLIC GET methods ***

    def get_groupmembers(self, user_id: str) -> List[str]:
        root = self.find(self[user_id])
        members = []
        for other_id, other_user in self.items():
            if self.find(other_user) is root:
                members.append(other_id)
        return members

    def print_ds(self) -> None:
        """Gibt die Disjoint-Set-Struktur aus.

        Funktioniert erst, wenn Sie in Praktikum 3 die Methode parent() in SetNode implementiert haben.

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        for user_id, user in self.items():
            print(user_id, self[user_id].parent().id())

    # *** PUBLIC STATIC methods ***

    # *** PRIVATE methods ***

    # *** PUBLIC methods to return class properties ***

    # *** PRIVATE variables ***
