import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = "8559219862:AAHERppsEHKsWkFFayYG5Zta8R-ISd8TXHU"

def convertir_fecha(timestamp):
    try:
        return datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return "No disponible"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    botones = [[InlineKeyboardButton("📡 Verificar IPTV", callback_data="check")]]
    teclado = InlineKeyboardMarkup(botones)

    await update.message.reply_text("🤖 BOT IPTV\nPresiona el botón 👇", reply_markup=teclado)

async def botones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "Envía así:\n\n"
        "servidor: http://example.com\n"
        "puerto: 8080\n"
        "usuario: user\n"
        "contraseña: pass"
    )

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        texto = update.message.text.split("\n")
        datos = {}

        for linea in texto:
            clave, valor = linea.split(":")
            datos[clave.strip().lower()] = valor.strip()

        url = f"{datos['servidor']}:{datos['puerto']}/player_api.php?username={datos['usuario']}&password={datos['contraseña']}"

        r = requests.get(url, timeout=10)
        data = r.json()

        user = data.get("user_info", {})
        server = data.get("server_info", {})

        respuesta = f"""
Estado: {user.get('status')}
Expira: {convertir_fecha(user.get('exp_date'))}
Conexiones: {user.get('active_cons')}/{user.get('max_connections')}
Hora servidor: {server.get('time_now')}
"""

        await update.message.reply_text(respuesta)

    except:
        await update.message.reply_text("Error en datos")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(botones))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check))

app.run_polling()
