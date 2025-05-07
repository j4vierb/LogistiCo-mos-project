import matplotlib.pyplot as plt
import networkx as nx

coordenadas = {idx + 1: (fila['Longitude'], fila['Latitude']) for idx, fila in ubicaciones.iterrows()}

for vehiculo in V:
    grafo = nx.DiGraph()
    recorrido = [1]
    nodo_actual = 1

    while True:
        siguiente = None
        for destino in N:
            if destino != nodo_actual and modelo.x[nodo_actual, destino, vehiculo].value == 1:
                siguiente = destino
                recorrido.append(destino)
                nodo_actual = destino
                break
        if siguiente is None or nodo_actual == 1:
            break

    if len(recorrido) > 1:
        recorrido.append(1)
        grafo.add_nodes_from(recorrido)
        grafo.add_edges_from((recorrido[i], recorrido[i+1]) for i in range(len(recorrido) - 1))

        plt.figure(figsize=(10, 6))
        posicion = {n: coordenadas[n] for n in recorrido}
        etiquetas = {n: ("PTO" if n == 1 else f"MUN{n:02d}") for n in recorrido}

        nx.draw_networkx_nodes(grafo, posicion, node_color='skyblue', node_size=500)
        nx.draw_networkx_labels(grafo, posicion, labels=etiquetas)
        nx.draw_networkx_edges(grafo, posicion, arrowstyle='->', arrowsize=20)

        plt.title(f"Ruta del Vehículo {vehiculo}")
        plt.axis('off')
        plt.show()
        print(f"Ruta del Vehículo {vehiculo}: {' - '.join(map(str, recorrido))}")       
        