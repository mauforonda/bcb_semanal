#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime as dt
import os
from pathlib import Path
from slugify import slugify
import argparse
import json  # For storing last run timestamp


def listar_pagina(session, pagina, tipo):
    def parse_fecha(nodos):
        regex = r"(\w+)(?:, )(\d{2})(?: )(\w+)(?:, )(\d{4})"
        meses_lista = [
            "enero",
            "febrero",
            "marzo",
            "abril",
            "mayo",
            "junio",
            "julio",
            "agosto",
            "septiembre",
            "octubre",
            "noviembre",
            "diciembre",
        ]
        meses = {mes: i + 1 for i, mes in enumerate(meses_lista)}
        for nodo in nodos:
            match = re.search(regex, nodo.get_text())
            if match:
                try:
                    year = int(match.group(4))
                    month = meses[match.group(3).lower()]
                    day = int(match.group(2))
                    return dt(year, month, day)
                except Exception as e:
                    print(f"Failed parsing regex match: {e}")

    def parse_adjunto(nodos):
        adjuntos = []
        for nodo in nodos:
            enlace = nodo["href"]
            formato = enlace.split(".")[-1]
            adjuntos.append({"enlace": enlace, "formato": formato})
        return adjuntos

    url = "https://www.bcb.gob.bo"
    params = {
        "q": "estad-sticas-semanales",
        "field_titulo_es_value": tipo,
        "page": str(pagina),
    }
    r = session.get(url, params=params)
    html = BeautifulSoup(r.text, "html.parser")
    reportes, errores = [], []
    listado = html.select(".view-content>div")
    if listado:
        for reporte in listado:
            try:
                fecha = parse_fecha(reporte.select(".bcb_date"))
                adjuntos = parse_adjunto(reporte.select(".bcb_adjunto a"))
                reportes.append({"publicacion": fecha, "adjuntos": adjuntos})
            except Exception as e:
                errores.append({"tipo": tipo, "pagina": pagina, "reporte": reporte})
    return reportes, errores


def listar_reportes(session, mode, last_run=None):
    reportes = []
    errores = []
    for tipo in ["Información Estadística Semanal"]:
        pagina = 0
        while True:
            print(f"{tipo}: página {pagina} ({len(errores)} errores)")
            reportes_pagina, errores_pagina = listar_pagina(session, pagina, tipo)
            errores.extend(errores_pagina)
            if not reportes_pagina:
                break
            # Sort reports by date (newest first) for mode 2 early stopping
            reportes_pagina.sort(key=lambda r: r['publicacion'], reverse=True)
            for reporte in reportes_pagina:
                if mode == 'incremental' and last_run and reporte['publicacion'] <= last_run:
                    # Stop fetching if we've reached reports older than last run
                    return reportes, errores
                reportes.append({**{"tipo": tipo}, **reporte})
            pagina += 1
    return reportes, errores


def descargar_adjunto(session, folder, reporte, formatos, check_existing=True):
    print(f"Procesando reporte {reporte['publicacion'].strftime('%Y-%m-%d')}")
    folder_path = Path(folder)
    os.makedirs(folder_path, exist_ok=True)
    urls = [a["enlace"] for a in reporte["adjuntos"] if a["formato"] in formatos]
    if urls:
        url = urls[0]
        formato = url.split(".")[-1]
        filename = f"{slugify(reporte['tipo'])}_{reporte['publicacion'].strftime('%Y-%m-%d')}.{formato}"
        file_path = folder_path / filename
        if check_existing and file_path.exists():
            print(f"Saltando: {filename} ya existe")
            return
        r = session.get(url)
        with open(file_path, "wb") as f:
            f.write(r.content)
        print(f"Guardado: {str(file_path)}")


def get_last_run():
    last_run_file = Path("last_run.txt")
    if last_run_file.exists():
        with open(last_run_file, 'r') as f:
            data = json.load(f)
            return dt.fromisoformat(data['timestamp'])
    return None


def save_last_run(timestamp):
    with open("last_run.txt", 'w') as f:
        json.dump({'timestamp': timestamp.isoformat()}, f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Descargar reportes del BCB")
    parser.add_argument('--mode', choices=['full', 'incremental'], default='full',
                        help='Modo: full (descarga faltantes) o incremental (desde última ejecución)')
    parser.add_argument('--folder', default='temporal', help='Directorio de descargas')
    args = parser.parse_args()

    session = requests.Session()
    last_run = get_last_run() if args.mode == 'incremental' else None
    reportes, errores = listar_reportes(session, args.mode, last_run)
    
    # Filter for mode 1: only download missing
    check_existing = (args.mode == 'full')
    
    for reporte in reportes:
        descargar_adjunto(session, args.folder, reporte, ["xls", "xlsx"], check_existing)
    
    # Update last run timestamp for incremental mode
    if args.mode == 'incremental':
        save_last_run(dt.now())
    
    if errores:
        print(f"Errores encontrados: {len(errores)}")
