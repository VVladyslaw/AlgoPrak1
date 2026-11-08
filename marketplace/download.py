from marketplace.users import Users

users = Users("user.csv")
users._get_map_graph()
print("Fertig, Graph gespeichert in", Users.GRAPH_FILE)