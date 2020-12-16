import folium
import polyline
import requests


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


def get_map(route):

    m = folium.Map(
        location=[
            (route["start_point"][0] + route["end_point"][0]) / 2,
            (route["start_point"][1] + route["end_point"][1]) / 2,
        ],
        zoom_start=13,
    )

    folium.PolyLine(route["route"], weight=8, color="blue", opacity=0.6).add_to(m)

    folium.Marker(
        location=route["start_point"], icon=folium.Icon(icon="play", color="green")
    ).add_to(m)

    folium.Marker(
        location=route["end_point"], icon=folium.Icon(icon="stop", color="red")
    ).add_to(m)

    return m
