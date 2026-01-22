#!/usr/bin/env python3

import pandas as pd
from supabase import create_client
import os
from time import sleep

SB_URL = os.environ["SUPABASE_URL"]
SB_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]


def guardar_supabase(df, tabla, unicos):
    print(f"guardar {tabla}")
    chunk_size = 5000
    sleep_s = 0.2
    supabase = create_client(SB_URL, SB_KEY)
    n = len(df)
    print(f"existen {n} filas que guardar")
    df.fecha = df.fecha.dt.strftime("%Y-%m-%d")
    for i in range(0, n, chunk_size):
        print(f"{n if i + chunk_size > n else i + chunk_size} filas")
        chunk = df.iloc[i : i + chunk_size]
        supabase.table(tabla).upsert(
            chunk.to_dict(orient="records"),
            on_conflict=unicos,
        ).execute()
        sleep(sleep_s)


reservas = pd.read_parquet("reservas.parquet")
guardar_supabase(reservas, "bcb_reservas", "tipo,fecha")

reporte = pd.read_parquet("datos.parquet")
reporte.subvariable = reporte.subvariable.fillna("")
guardar_supabase(reporte, "bcb_semanal", "categoria,variable,subvariable,fecha")
