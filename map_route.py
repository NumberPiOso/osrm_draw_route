import itertools

import folium
import folium.plugins
import numpy as np
import pandas as pd
import polyline
import requests
from folium import Marker
from typing import List


def get_route(points: pd.DataFrame) -> dict:
    """
    Obtiene información de la ruta calculandola usando osrm.

    Args:
        points: Puntos por los cuales pasa la ruta. Contiene columnas "Latitud",
            "Longitud" e "id".

    Returns:
        dict: Información de la ruta.
            Diccionario con las llaves "route", "stops_coords" y "name_stops".
    """
    lats = points["Latitud"]
    lons = points["Longitud"]
    loc = ";".join(f"{lon},{lat}" for lon, lat in zip(lons, lats))
    url = "https://router.project-osrm.org/route/v1/driving/"
    r = requests.get(url + loc)
    if r.status_code != 200:
        return {}
    res = r.json()
    routes = polyline.decode(res["routes"][0]["geometry"])
    info_route = {
        "route": routes,
        "stops_coords": list(zip(lats, lons)),
        "name_stops": points["id"].to_list(),
    }
    return info_route


def map_route(info_route: dict, animated: bool = False) -> folium.Map:
    """
    Calcula el mapa interactivo.

    Args:
        info_route (dict): Contiene las llaves "stops_coords", "route" e "ids"
            - "route": List que contiene todos los puntos de la ruta, incluso los que no
                son paradas, generalmente es generada como Polyline.
            - "stops_coords": Lista que contiene las coordenadas latitud, longitud de
                cada PARADA.
            - "name_stops": Lista con nombre de cada PARADAS
        animated (bool): Verdadero si desea animar la polyline con plugin "Antpath".
            Por defecto es Falso.

    Returns:
        folium.Map: Mapa generado.
    """
    stops_coords = info_route["stops_coords"]
    route_poly = info_route["route"]
    name_stops = info_route["name_stops"]
    m = folium.Map(location=np.mean(stops_coords, axis=0), zoom_start=13,)
    # Dibujar linea ruta
    col = "blue"
    _add_polyline(m, route_poly, animated, col)
    # Dibuja puntos "Marcadores sobre el mapa"
    _add_route_stops(m, col, stops_coords, name_stops)
    return m


def mult_routes(multiple_infos: List[dict], colors: List, animated: bool) -> folium.Map:
    """
    Calcula el mapa interactivo para múltiples rutas.

    Args:
        info_routes (List[dict]): Lista con diccionarios, donde cada diccionario
            representa una ruta en el mapa.
            info_route (dict): Contiene las llaves "stops_coords", "route" e "ids"
                - "route": List que contiene todos los puntos de la ruta, incluso los que
                    no son paradas, generalmente es generada como Polyline.
                - "stops_coords": Lista que contiene las coordenadas latitud, longitud de
                    cada PARADA.
                - "name_stops": Lista con nombre de cada PARADAS
        animated (bool): Verdadero si desea animar la polyline con plugin "Antpath".
            Por defecto es Falso.

    Returns:
        folium.Map: Mapa generado.
    """
    # Generar mapa
    centroide_paradas = np.mean(
        np.concatenate([info["stops_coords"] for info in multiple_infos]), axis=0
    )
    m = folium.Map(location=centroide_paradas, zoom_start=13)
    # Dibujar rutas
    for i, info_route in enumerate(multiple_infos):
        # Define parametros
        stops_coords = info_route["stops_coords"]
        route_poly = info_route["route"]
        name_stops = info_route["name_stops"]
        color = colors[i]
        # Dibujar linea ruta
        _add_polyline(m, route_poly, animated, color)
        # Dibuja puntos "Marcadores sobre el mapa"
        _add_route_stops(m, color, stops_coords, name_stops)
    return m


def _add_polyline(m: folium.Map, route_poly: List, animated: bool, color: str) -> None:
    """Añade al mapa Ruta "route_poly"."""
    if animated:
        folium.plugins.AntPath(
            locations=route_poly, dash_array=[10, 100], color=color
        ).add_to(m)
    else:
        folium.PolyLine(route_poly, weight=8, color=color, opacity=0.6).add_to(m)


def _add_route_stops(
    m: folium.Map, color: str, stops_coords: List = [], name_stops: List = []
) -> None:
    """Añade al mapa icono de estaciones "stops_coords" con nombre "name_stops"."""

    # Dibuja puntos "Marcadores sobre el mapa"
    n_points = len(stops_coords)
    for i, (stop, stp_nm) in enumerate(zip(stops_coords, name_stops)):
        if i not in {0, n_points - 1}:
            icon = folium.Icon(icon="bus", prefix="fa", color=color)
        elif i == 0:
            icon = folium.Icon(icon="play", prefix="fa", color=color)
        elif i == n_points - 1:
            icon = folium.Icon(icon="stop", prefix="fa", color=color)
        Marker(location=stop, icon=icon, color=color, popup=stp_nm).add_to(m)


def add_grouped_users(m: folium.Map, grouped_users: pd.DataFrame) -> None:
    """
    Cambia mapa "m" para añadir usuarios agrupados.

    Args:
        m: Mapa sobre el cuál se desean añadir los usuarios.
        grouped_users: Tabla con la información de los usuarios agrupados. Contiene
            columnas "from_lat", "from_lon", "to_lat", "to_lon" y opcionalmente "id".
    """
    coords_cols = ["from_lat", "from_lon", "to_lat", "to_lon"]
    id_users = (
        grouped_users["id"] if "id" in grouped_users.columns else itertools.repeat(None)
    )
    for (_, from_lat, from_lon, to_lat, to_lon), id_u in zip(
        grouped_users[coords_cols].itertuples(), id_users
    ):
        line = [[from_lat, from_lon], [to_lat, to_lon]]
        folium.PolyLine(line, color="gray", line_weight=5, dash_array="8").add_to(m)
        icon = folium.Icon(icon="male", prefix="fa", color="blue")
        Marker(location=line[0], icon=icon, color="green", popup=id_u).add_to(m)
