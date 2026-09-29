import io

import pandas as pd
import requests
import yfinance as yf

ARCHIVO_SALIDA = "top10_semanal.csv"
DIAS = 7  # ventana de variación en días calendario


def obtener_tickers_sp500():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    html = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30).text
    tabla = pd.read_html(io.StringIO(html))[0]
    # Yahoo usa "-" en lugar de "." (ej. BRK.B -> BRK-B)
    return tabla["Symbol"].str.replace(".", "-", regex=False).tolist()


def calcular_variaciones(tickers):
    cierres = yf.download(
        tickers, period="1mo", interval="1d", auto_adjust=True, progress=False
    )["Close"].dropna(how="all")

    fecha_final = cierres.index[-1]
    fecha_base = cierres.index[cierres.index <= fecha_final - pd.Timedelta(days=DIAS)][-1]

    precio_final = cierres.loc[fecha_final]
    precio_base = cierres.loc[fecha_base]
    variacion = (precio_final / precio_base - 1) * 100
    return precio_final, variacion.dropna().sort_values(ascending=False)


def main():
    print("Obteniendo lista de empresas...")
    tickers = obtener_tickers_sp500()

    print("Descargando precios...")
    precios, variaciones = calcular_variaciones(tickers)
    top10 = variaciones.head(10)

    print("Consultando datos fundamentales del top 10...")
    filas = []
    for ticker, var in top10.items():
        info = yf.Ticker(ticker).info
        margen = info.get("profitMargins")
        filas.append({
            "Empresa": info.get("shortName", ticker),
            "Precio actual": round(float(precios[ticker]), 2),
            "Variación semanal (%)": round(float(var), 2),
            "P/E": info.get("trailingPE"),
            "Profit margin (%)": round(margen * 100, 2) if margen is not None else None,
        })

    df = pd.DataFrame(filas)
    # utf-8-sig para que Excel lea bien los acentos
    df.to_csv(ARCHIVO_SALIDA, index=False, encoding="utf-8-sig")
    print(f"\nListo: {ARCHIVO_SALIDA}\n")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()

