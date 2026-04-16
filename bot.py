import requests
import asyncio
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = "8559219862:AAHERppsEHKsWkFFayYG5Zta8R-ISd8TXHU"

# 🔐 CONFIG
ADMIN_ID = 1044482533  # 🔥 CAMBIA ESTO
VIP_USERS = {ADMIN_ID}

# 🚫 anti spam
user_requests = {}

# -------- FUNCIONES -------- #

def fecha_bonita(ts):
    try:
        return datetime.fromtimestamp(int(ts)).strftime('%d/%m/%Y')
    except:
        return "N/A"

def detectar_protocolo(servidor, puerto):
    try:
        if requests.get(f"https://{servidor}:{puerto}", timeout=3, verify=False).status_code < 500:
            return "https"
    except:
        pass
    return "http"

async def obtener_datos_async(servidor, puerto, usuario, contraseña):
    try:
        protocolo = detectar_protocolo(servidor, puerto)
        url = f"{protocolo}://{servidor}:{puerto}/player_api.php?username={usuario}&password={contraseña}"

        r = requests.get(url, timeout=8, verify=False)
        data = r.json()

        if "user_info" not in data:
            return "❌ Cuenta inválida"

        user = data["user_info"]
        server = data.get("server_info", {})

        tipo = "Trial" if user.get("is_trial") == "1" else "Premium"

        return f"""
INFORMACION DE LA CUENTA
──────────────────────────
servidor:           {protocolo}://{servidor}
puerto:             {puerto}
usuario:            {usuario}
contraseña:         {contraseña}
estado:             {user.get('status')}
tipo_linea:         {tipo}
fecha_inicio:       {fecha_bonita(user.get('created_at'))}
expiracion:         {fecha_bonita(user.get('exp_date'))}
conex_permitidas:   {user.get('max_connections')}
conex_activas:      {user.get('active_cons')}
hora_servidor:      {server.get('time_now')}
──────────────────────────
"""
    except:
        return "❌ Error"

# -------- START -------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💀 BOT IPTV NIVEL DIOS")

# -------- ADMIN -------- #

async def add_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    try:
        uid = int(context.args[0])
        VIP_USERS.add(uid)
        await update.message.reply_text(f"✅ Usuario {uid} agregado VIP")
    except:
        await update.message.reply_text("❌ Uso: /addvip ID")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    await update.message.reply_text(f"📊 Usuarios activos: {len(user_requests)}")

# -------- CHECK -------- #

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    # 🔐 acceso VIP
    if user_id not in VIP_USERS:
        await update.message.reply_text("🚫 No autorizado")
        return

    # 🚫 anti spam
    now = datetime.now().timestamp()
    user_requests[user_id] = [t for t in user_requests.get(user_id, []) if now - t < 60]

    if len(user_requests[user_id]) > 10:
        await update.message.reply_text("⏳ Espera un momento")
        return

    user_requests[user_id].append(now)

    texto = update.message.text.strip().split("\n")
    tareas = []

    for linea in texto:
        if linea.startswith("http") and "m3u" in linea:
            try:
                parsed = urlparse(linea)
                query = parse_qs(parsed.query)

                servidor = parsed.hostname
                puerto = parsed.port or "80"
                usuario = query.get("username", [None])[0]
                contraseña = query.get("password", [None])[0]

                if usuario and contraseña:
                    tareas.append(obtener_datos_async(servidor, puerto, usuario, contraseña))
            except:
                pass

    if not tareas:
        await update.message.reply_text("⚠️ No se detectaron datos")
        return

    resultados = await asyncio.gather(*tareas)

    for r in resultados:
        await update.message.reply_text(r)

# -------- ARCHIVOS M3U -------- #

async def archivo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.document.get_file()
    ruta = "lista.m3u"
    await file.download_to_drive(ruta)

    with open(ruta, "r", errors="ignore") as f:
        lineas = f.readlines()

    tareas = []

    for l in lineas:
        if "http" in l and "m3u" in l:
            parsed = urlparse(l.strip())
            query = parse_qs(parsed.query)

            servidor = parsed.hostname
            puerto = parsed.port or "80"
            usuario = query.get("username", [None])[0]
            contraseña = query.get("password", [None])[0]

            if usuario and contraseña:
                tareas.append(obtener_datos_async(servidor, puerto, usuario, contraseña))

    resultados = await asyncio.gather(*tareas[:20])

    for r in resultados:
        await update.message.reply_text(r)

# -------- MAIN -------- #

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("addvip", add_vip))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(MessageHandler(filters.Document.ALL, archivo))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check))

print("💀 BOT NIVEL DIOS ACTIVO 💀")
app.run_polling()