import folium
import polyline
import requests


def get_route(points, start_id, finish_id):
    pickup_lat, pickup_lon = points.loc[start_id]
    dropoff_lat, dropoff_lon = points.loc[finish_id]

    loc = "{},{};{},{}".format(pickup_lon, pickup_lat, dropoff_lon, dropoff_lat)
    url = "http://localhost:5000/route/v1/driving/"
    r = requests.get(url + loc)
    if r.status_code != 200:
        return {}

    res = r.json()
    routes = polyline.decode(res["routes"][0]["geometry"])
    start_point = [
        res["waypoints"][0]["location"][1],
        res["waypoints"][0]["location"][0],
    ]
    end_point = [res["waypoints"][1]["location"][1], res["waypoints"][1]["location"][0]]
    distance = res["routes"][0]["distance"]

    out = {
        "route": routes,
        "start_point": start_point,
        "end_point": end_point,
        "distance": distance,
    }

    return out


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
