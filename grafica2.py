import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import networkx as nx

coordenadas = {idx + 1: (fila['Longitude'], fila['Latitude']) for idx, fila in ubicaciones.iterrows()}

grafo_general = nx.DiGraph()
grafo_general.add_nodes_from(coordenadas.keys())

paleta_colores = cm.get_cmap('tab10', len(V))

for idx, vehiculo in enumerate(V):
    color_hex = mcolors.to_hex(paleta_colores(idx))
    recorrido = [1]
    actual = 1
    while True:
        siguiente = None
        for destino in N:
            if destino != actual and modelo.x[actual, destino, vehiculo].value == 1:
                siguiente = destino
                recorrido.append(destino)
                actual = destino
                break
        if siguiente is None or actual == 1:
            break

    if len(recorrido) > 1:
        recorrido.append(1)
        for i in range(len(recorrido) - 1):
            grafo_general.add_edge(recorrido[i], recorrido[i+1], color=color_hex, vehiculo=vehiculo)

posiciones = {n: coordenadas[n] for n in grafo_general.nodes}

plt.figure(figsize=(14, 10))
nx.draw_networkx_nodes(grafo_general, posiciones, node_color='skyblue', node_size=500)
nx.draw_networkx_labels(grafo_general, posiciones, labels={n: ("PTO" if n == 1 else f"MUN{n:02d}") for n in grafo_general.nodes})

for i, j, atributos in grafo_general.edges(data=True):
    nx.draw_networkx_edges(
        grafo_general, posiciones,
        edgelist=[(i, j)],
        edge_color=atributos['color'],
        width=2,
        arrows=True,
        arrowsize=20
    )

for idx, vehiculo in enumerate(V):
    plt.plot([], [], color=mcolors.to_hex(paleta_colores(idx)), label=f'Vehículo {vehiculo}')
plt.legend(loc='lower left')

plt.title("Rutas de todos los vehículos (CVRP)")
plt.axis('off')
plt.tight_layout()
plt.show()
print("Rutas de todos los vehículos (CVRP)")