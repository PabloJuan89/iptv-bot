import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = "8559219862:AAHERppsEHKsWkFFayYG5Zta8R-ISd8TXHU"

# -------- FUNCIONES -------- #

def convertir_fecha(timestamp):
    try:
        return datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return "No disponible"

# -------- START -------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    botones = [[InlineKeyboardButton("📡 Verificar IPTV", callback_data="check")]]
    teclado = InlineKeyboardMarkup(botones)

    await update.message.reply_text(
        "📺 BOT CHECKER IPTV\n\nPresiona el botón 👇",
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

    # 🔵 Detectar M3U
    if texto.startswith("http") and "m3u" in texto:
        await update.message.reply_text(
            f"""
📡 INFORMACIÓN DE LA CUENTA
──────────────────────────
servidor: Detectado
tipo_linea: M3U
estado: Activo (si carga)
nota: No se pueden obtener más datos en M3U
"""
        )
        return

    # 🔴 Xtream Codes
    try:
        lineas = texto.split("\n")
        datos = {}

        for linea in lineas:
            clave, valor = linea.split(":", 1)
            datos[clave.strip().lower()] = valor.strip()

        servidor = datos.get("servidor")
        puerto = datos.get("puerto")
        usuario = datos.get("usuario")
        contraseña = datos.get("contraseña")

        url = f"{servidor}:{puerto}/player_api.php?username={usuario}&password={contraseña}"

        r = requests.get(url, timeout=10)

        if r.status_code != 200:
            await update.message.reply_text("❌ Servidor no responde")
            return

        data = r.json()

        user = data.get("user_info", {})
        server = data.get("server_info", {})

        estado = user.get("status", "Desconocido")

        tipo_linea = "Premium"
        if user.get("is_trial") == "1":
            tipo_linea = "Trial"

        respuesta = f"""
📡 INFORMACIÓN DE LA CUENTA
──────────────────────────
servidor: {servidor}
puerto: {puerto}
usuario: {usuario}
contraseña: {contraseña}
estado: {estado}
tipo_linea: {tipo_linea}
fecha_inicio: {convertir_fecha(user.get('created_at'))}
expiracion: {convertir_fecha(user.get('exp_date'))}
conex_permitidas: {user.get('max_connections')}
conex_activas: {user.get('active_cons')}
hora_servidor: {server.get('time_now')}
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