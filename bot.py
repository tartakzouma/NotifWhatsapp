import os
import requests
from datetime import datetime, timezone

CASA_API_BASE = os.getenv("CASA_API_BASE", "https://casablanca-bourse-api.onrender.com")
VAR_THRESHOLD_UP = float(os.getenv("VAR_THRESHOLD_UP") or "2.0")
VAR_THRESHOLD_DOWN = float(os.getenv("VAR_THRESHOLD_DOWN") or "-2.0")


WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
WHATSAPP_TO = os.getenv("WHATSAPP_TO")


def fetch_all_stocks():
    url = f"{CASA_API_BASE}/api/v1/companies"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.json()


def build_alerts(stocks):
    alerts = []

    for s in stocks:
        name = s.get("name", "Inconnu")
        symbol = s.get("symbol", "N/A")

        raw_change = s.get("change", 0)
        try:
            change = float(str(raw_change).replace("%", "").replace(",", "."))
        except ValueError:
            continue

        if change >= VAR_THRESHOLD_UP or change <= VAR_THRESHOLD_DOWN:
            alerts.append({"name": name, "symbol": symbol, "change": change})

    return alerts


def send_whatsapp_message(text: str):
    if not (WHATSAPP_TOKEN and WHATSAPP_PHONE_ID and WHATSAPP_TO):
        print("❌ Config WhatsApp manquante.")
        return

    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": WHATSAPP_TO,
        "type": "text",
        "text": {"body": text}
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=15)
    if resp.status_code >= 400:
        print("❌ Erreur WhatsApp:", resp.status_code, resp.text)
    else:
        print("✅ Alerte envoyée sur WhatsApp.")


def main():
    print("🔄 Lancement du bot BVC...")
    try:
        stocks = fetch_all_stocks()
    except Exception as e:
        print("❌ Erreur API BVC:", e)
        return

    alerts = build_alerts(stocks)
    if not alerts:
        print("ℹ️ Aucune alerte.")
        return

    now = datetime.now(timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M')
    msg_lines = [f"📈 Alertes Bourse de Casablanca\n🕒 {now}\n"]

    for a in alerts:
        icon = "🚀" if a["change"] > 0 else "📉"
        msg_lines.append(f"{icon} {a['symbol']} : {a['change']:.2f}%")

    send_whatsapp_message("\n".join(msg_lines))


if __name__ == "__main__":
    main()
