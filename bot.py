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

    # 🔵 Detectar M3U PRO
if texto.startswith("http") and "m3u" in texto:
    try:
        url = texto.strip()

        # Extraer datos del link
        from urllib.parse import urlparse, parse_qs

        parsed = urlparse(url)
        query = parse_qs(parsed.query)

        servidor = parsed.hostname
        puerto = parsed.port if parsed.port else "80"
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

    except:
        await update.message.reply_text("❌ Error al analizar M3U")

    return

# -------- MAIN -------- #

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(botones))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check))

print("BOT IPTV PRO ACTIVO...")
app.run_polling()