import subprocess
from contextlib import contextmanager
from pathlib import Path

import psutil


def close_connection():
    """
    Cierra proceso activo asociado a la conexión local.
    Busca el proceso asociado a la conexión 0.0.0.0:5000 y termina el proceso.
    """
    for connection in psutil.net_connections():
        if connection.laddr.port == 5000:
            pid = connection.pid
            if (pid is not None) and psutil.pid_exists(pid):
                p = psutil.Process(connection.pid)
                p.kill()
                p.wait()

                print("El puerto 5000 se cerró correctamente")

    return None


class Osrm(object):
    """
    Objeto que extrae la creación y
    """

    def __init__(
        self,
        profile: Path,
        pbf_path: Path,
        extraction_path: Path = Path.home() / "osrm_maps",
    ) -> None:
        profile_name = profile.stem
        path_dir = extraction_path / profile_name
        path_dir.mkdir(parents=True, exist_ok=True)  # Crea dir si no existe
        sy_pbf_path = path_dir / pbf_path.name
        if not sy_pbf_path.is_symlink():
            sy_pbf_path.symlink_to(pbf_path)
        self.osrm_map = sy_pbf_path.with_suffix("").with_suffix(".osrm")
        if not self.osrm_map.is_file():
            subprocess.call(f"osrm-extract {sy_pbf_path} -p {profile}", shell=True)
            # pbf_path tiene doble extensión .osm.pbf
            subprocess.call(f"osrm-partition {self.osrm_map}", shell=True)
            subprocess.call(f"osrm-customize {self.osrm_map}", shell=True)
        self.is_routing = False

    def route(self, table_size: int = 300):
        if self.is_routing:
            print("Actualmente se está ruteando")
        arg = (
            f"osrm-routed --max-table-size={table_size}"
            f" --algorithm=MLD {self.osrm_map}"
        )
        print(arg)
        self.process = subprocess.Popen(
            [arg],
            bufsize=1,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            shell=True,
        )
        for line in self.process.stdout:
            if "[info] running and waiting for requests" in line:
                break

    def route_stdout(self, table_size: int = 300):
        if self.is_routing:
            print("Actualmente se está ruteando")
        arg = (
            f"osrm-routed --max-table-size={table_size}"
            f" --algorithm=MLD {self.osrm_map}"
        )
        print(arg)
        self.process = subprocess.Popen(
            [arg],
            bufsize=1,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            shell=True,
        )
        return self.process.stdout

    def stop_route(self):
        self.process.kill()
        self.process.wait()
        close_connection()

    @contextmanager
    def routing(self, table_size: int = 300):
        self.route(table_size)
        try:
            yield self.process
        finally:
            self.stop_route()
