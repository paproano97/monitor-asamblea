import json
import os
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

URL = "https://www.asambleanacional.gob.ec/es/noticias/boletines-de-prensa"
STATE_FILE = "estado_boletines.json"

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MonitorBoletines/1.0)"
}

def obtener_boletines():
    r = requests.get(URL, headers=HEADERS, timeout=30)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    resultados = []

    for h in soup.select("h5 a"):
        titulo = h.get_text(" ", strip=True)
        href = h.get("href", "").strip()

        if not titulo or not href:
            continue

        if titulo.lower() == "leer más":
            continue

        link = urljoin(URL, href)

        item = {
            "titulo": titulo,
            "link": link
        }

        if item not in resultados:
            resultados.append(item)

    return resultados

def cargar_estado():
    if not os.path.exists(STATE_FILE):
        return []
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_estado(data):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def detectar_nuevos(anterior, actual):
    prev = {(x["titulo"], x["link"]) for x in anterior}
    return [x for x in actual if (x["titulo"], x["link"]) not in prev]

def enviar_telegram(mensaje):
    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje
    }
    r = requests.post(api_url, data=payload, timeout=30)
    r.raise_for_status()

def main():
    actual = obtener_boletines()
    anterior = cargar_estado()

if not anterior:
    guardar_estado(actual)
    enviar_telegram("✅ Monitor activo: todo está funcionando correctamente.")
    return

    nuevos = detectar_nuevos(anterior, actual)

    if nuevos:
        for item in nuevos:
            mensaje = (
                "Nuevo boletín detectado\n\n"
                f"Título: {item['titulo']}\n"
                f"Link: {item['link']}"
            )
            enviar_telegram(mensaje)

    guardar_estado(actual)

if __name__ == "__main__":
    main()
