
import pandas as pd
from geopy.distance import geodesic
from pyomo.environ import *
from pyomo.opt import SolverFactory

df_clientes = pd.read_csv('Proyecto_Caso_Base.csv')
df_depositos = pd.read_csv('Proyecto_Caso_Base.csv')
df_vehiculos = pd.read_csv('Proyecto_Caso_Base.csv')

ubicaciones = pd.concat([
    df_depositos[['LocationID', 'Longitude', 'Latitude']],
    df_clientes[['LocationID', 'Longitude', 'Latitude']]
], ignore_index=True)
ubicaciones.to_csv('Proyecto_Caso_Base/locations.csv', index=False)

ubicaciones = pd.read_csv('Proyecto_Caso_Base.csv')

matriz_distancias = []
for _, fila_origen in ubicaciones.iterrows():
    coord_origen = (fila_origen['Latitude'], fila_origen['Longitude'])
    distancias_fila = [
        geodesic(coord_origen, (fila_dest['Latitude'], fila_dest['Longitude'])).kilometers
        for _, fila_dest in ubicaciones.iterrows()
    ]
    matriz_distancias.append(distancias_fila)

modelo = ConcreteModel()

num_localidades = len(ubicaciones)
num_vehiculos = len(df_vehiculos)

C = RangeSet(2, num_localidades)
V = RangeSet(1, num_vehiculos)
N = RangeSet(1, num_localidades)

demanda = {i+2: d for i, d in enumerate(df_clientes['Demand'])}
capacidad = {i+1: c for i, c in enumerate(df_vehiculos['Capacity'])}
autonomia = {i+1: a for i, a in enumerate(df_vehiculos['Range'])}

modelo.x = Var(N, N, V, domain=Binary)
modelo.u = Var(C, V, bounds=(1, num_localidades - 1), domain=Integers)

modelo.obj = Objective(
    expr=sum(matriz_distancias[i-1][j-1]*modelo.x[i,j,k]
             for i in N for j in N for k in V if i != j),
    sense=minimize
)

modelo.rest_veh_sin_ciclo = ConstraintList()
for k in V:
    modelo.rest_veh_sin_ciclo.add(modelo.x[1, 1, k] == 0)

modelo.rest_visita_unica = ConstraintList()
for j in C:
    modelo.rest_visita_unica.add(
        sum(modelo.x[i,j,k] for i in N if i != j for k in V) == 1
    )

modelo.rest_salida_puerto = ConstraintList()
for k in V:
    modelo.rest_salida_puerto.add(
        sum(modelo.x[1,j,k] for j in N if j != 1) == 1
    )

modelo.rest_entrada_puerto = ConstraintList()
for k in V:
    modelo.rest_entrada_puerto.add(
        sum(modelo.x[i,1,k] for i in N if i != 1) == 1
    )

modelo.rest_flujo = ConstraintList()
for k in V:
    for nodo in C:
        modelo.rest_flujo.add(
            sum(modelo.x[i,nodo,k] for i in N if i != nodo) == sum(modelo.x[nodo,j,k] for j in N if j != nodo)
        )

modelo.rest_mtz = ConstraintList()
for k in V:
    for i in C:
        for j in C:
            if i != j:
                modelo.rest_mtz.add(
                    modelo.u[i,k] - modelo.u[j,k] + num_localidades * modelo.x[i,j,k] <= num_localidades - 1
                )

modelo.rest_capacidad = ConstraintList()
for k in V:
    modelo.rest_capacidad.add(
        sum(demanda[i] * sum(modelo.x[i,j,k] for j in N if i != j) for i in C) <= capacidad[k]
    )

modelo.rest_autonomia = ConstraintList()
for k in V:
    modelo.rest_autonomia.add(
        sum(matriz_distancias[i-1][j-1] * modelo.x[i,j,k] for i in N for j in N if i != j) <= autonomia[k]
    )

solver = SolverFactory('glpk')
solver.options['tmlim'] = 30
resultados = solver.solve(modelo, tee=True)

def generar_resultados(modelo, matriz_distancias, demanda, capacidad, autonomia, N, C, V, velocidad=50, tarifa=5000, mantenimiento=700):
    costo_km = tarifa + mantenimiento
    columnas = ['VehicleId', 'LoadCap', 'FuelCap', 'RouteSequence', 'Municipalities', 'DemandSatisfied', 'InitialLoad', 'InitialFuel', 'Distance', 'Time', 'TotalCost']
    registros = []

    for k in V:
        recorrido = [1]
        actual = 1

        while True:
            siguiente = None
            for j in N:
                if j != actual and modelo.x[actual, j, k].value and modelo.x[actual, j, k].value > 0.5:
                    siguiente = j
                    recorrido.append(j)
                    actual = j
                    break
            if siguiente is None or actual == 1:
                break

        secuencia = " - ".join(["PTO"] + [f"MUN{str(n).zfill(2)}" for n in recorrido[1:-1]] + ["PTO"])
        clientes_recorridos = [n for n in recorrido if n in demanda]
        demandas = [demanda[n] for n in clientes_recorridos]
        demanda_str = "-".join(str(int(d)) if d.is_integer() else str(d) for d in demandas)
        distancia_total = sum(matriz_distancias[recorrido[i]-1][recorrido[i+1]-1] for i in range(len(recorrido)-1))
        tiempo = round((distancia_total / velocidad) * 60, 1)
        costo = round(distancia_total * costo_km)

        registros.append([
            f"CAM{str(k).zfill(3)}",
            capacidad[k],
            autonomia[k],
            secuencia,
            len(clientes_recorridos),
            demanda_str,
            sum(demandas),
            autonomia[k],
            round(distancia_total, 1),
            tiempo,
            costo
        ])

    df_res = pd.DataFrame(registros, columns=columnas)
    df_res.to_csv("Proyecto_Caso_Base.csv", index=False)
    return df_res

df_salida = generar_resultados(modelo, matriz_distancias, demanda, capacidad, autonomia, N, C, V)
print(f'Distancia total recorrida por todos los vehículos: {round(df_salida["Distance"].sum(), 2)} km')
