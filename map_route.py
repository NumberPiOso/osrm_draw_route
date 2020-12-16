import folium
import polyline
import requests
import numpy as np


def get_route(points):
    lats = points["Latitud"]
    lons = points["Longitud"]
    loc = ';'.join(f"{lon},{lat}" for lon, lat in zip(lons, lats))
    url = "https://router.project-osrm.org/route/v1/driving/"
    r = requests.get(url + loc)
    if r.status_code != 200:
        return {}
    res = r.json()
    routes = polyline.decode(res["routes"][0]["geometry"])
    info_route = {
        "route": routes,
        "stops": list(zip(lats, lons)),
    }
    return info_route


def get_map(info_route):
    m = folium.Map(
            location=np.mean(info_route["stops"], axis=0),
            zoom_start=13,
        )
    folium.PolyLine(info_route["route"], weight=8, color="blue", opacity=0.6).add_to(m)
    for stop in info_route["stops"]:
        folium.Marker(
                location=stop, icon=folium.Icon(icon="male", prefix="fa", color="blue")
            ).add_to(m)
    return m
