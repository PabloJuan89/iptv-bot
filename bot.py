import requests
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = "8559219862:AAHERppsEHKsWkFFayYG5Zta8R-ISd8TXHU"

# -------- FUNCIONES -------- #

def fecha_bonita(timestamp):
    try:
        return datetime.fromtimestamp(int(timestamp)).strftime('%d/%m/%Y')
    except:
        return "N/A"

def limpiar_servidor(url):
    return url.replace("http://", "").replace("https://", "")

# -------- START -------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    botones = [[InlineKeyboardButton("📡 Verificar IPTV", callback_data="check")]]
    teclado = InlineKeyboardMarkup(botones)

    await update.message.reply_text(
        "📺 BOT CHECKER IPTV PRO\n\nPresiona el botón 👇",
        reply_markup=teclado
    )

# -------- BOTONES -------- #

async def botones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "Envía datos Xtream:\n\n"
        "servidor: http://example.com\n"
        "puerto: 8080\n"
        "usuario: user\n"
        "contraseña: pass\n\n"
        "O envía un link M3U"
    )

# -------- CHECK -------- #

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()

    # =========================
    # 🔵 MODO M3U
    # =========================
    if texto.startswith("http") and "m3u" in texto:
        try:
            parsed = urlparse(texto)
            query = parse_qs(parsed.query)

            servidor = parsed.hostname or "N/A"
            puerto = parsed.port or "80"
            usuario = query.get("username", ["N/A"])[0]
            contraseña = query.get("password", ["N/A"])[0]

            respuesta = f"""
INFORMACION DE LA CUENTA
──────────────────────────
servidor:           {servidor}
puerto:             {puerto}
usuario:            {usuario}
contraseña:         {contraseña}
estado:             N/A
tipo_linea:         M3U
fecha_inicio:       N/A
expiracion:         N/A
conex_permitidas:   N/A
conex_activas:      N/A
hora_servidor:      N/A
──────────────────────────
"""

            await update.message.reply_text(respuesta)
            return

        except:
            await update.message.reply_text("❌ Error al analizar M3U")
            return

    # =========================
    # 🔴 MODO XTREAM
    # =========================
    try:
        lineas = texto.split("\n")
        datos = {}

        for linea in lineas:
            if ":" in linea:
                clave, valor = linea.split(":", 1)
                datos[clave.strip().lower()] = valor.strip()

        servidor = datos.get("servidor")
        puerto = datos.get("puerto")
        usuario = datos.get("usuario")
        contraseña = datos.get("contraseña")

        if not all([servidor, puerto, usuario, contraseña]):
            await update.message.reply_text("❌ Datos incompletos")
            return

        url = f"{servidor}:{puerto}/player_api.php?username={usuario}&password={contraseña}"

        r = requests.get(url, timeout=10)

        if r.status_code != 200:
            await update.message.reply_text("❌ Servidor no responde")
            return

        data = r.json()

        user = data.get("user_info", {})
        server = data.get("server_info", {})

        estado = user.get("status", "N/A")

        tipo_linea = "Premium"
        if user.get("is_trial") == "1":
            tipo_linea = "Trial"

        respuesta = f"""
INFORMACION DE LA CUENTA
──────────────────────────
servidor:           {limpiar_servidor(servidor)}
puerto:             {puerto}
usuario:            {usuario}
contraseña:         {contraseña}
estado:             {estado}
tipo_linea:         {tipo_linea}
fecha_inicio:       {fecha_bonita(user.get('created_at'))}
expiracion:         {fecha_bonita(user.get('exp_date'))}
conex_permitidas:   {user.get('max_connections')}
conex_activas:      {user.get('active_cons')}
hora_servidor:      {server.get('time_now')}
──────────────────────────
"""

        await update.message.reply_text(respuesta)

    except Exception as e:
        await update.message.reply_text("❌ Error en datos o formato")

# -------- MAIN -------- #

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(botones))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check))

print("BOT IPTV PRO ACTIVO...")
app.run_polling()