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

# 🔥 DETECCIÓN REAL DE PROTOCOLO
def detectar_protocolo(servidor, puerto):
    try:
        url_https = f"https://{servidor}:{puerto}"
        r = requests.get(url_https, timeout=5, verify=False)
        if r.status_code < 500:
            return "https"
    except:
        pass

    return "http"

# -------- CONSULTA API -------- #

def obtener_datos(servidor, puerto, usuario, contraseña):
    try:
        protocolo = detectar_protocolo(servidor, puerto)

        url = f"{protocolo}://{servidor}:{puerto}/player_api.php?username={usuario}&password={contraseña}"
        r = requests.get(url, timeout=10, verify=False)

        if r.status_code != 200:
            return "❌ Servidor no responde"

        data = r.json()

        if "user_info" not in data:
            return "❌ Cuenta inválida"

        user = data.get("user_info", {})
        server = data.get("server_info", {})

        estado = user.get("status", "N/A")

        tipo_linea = "Premium"
        if user.get("is_trial") == "1":
            tipo_linea = "Trial"

        return f"""
INFORMACION DE LA CUENTA
──────────────────────────
servidor:           {protocolo}://{servidor}
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

    except:
        return "❌ Error consultando servidor"

# -------- START -------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    botones = [[InlineKeyboardButton("📡 Verificar IPTV", callback_data="check")]]
    teclado = InlineKeyboardMarkup(botones)

    await update.message.reply_text(
        "📺 BOT IPTV PRO\n\nEnvía:\n✔ Datos Xtream\n✔ Link M3U",
        reply_markup=teclado
    )

# -------- BOTONES -------- #

async def botones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "Formato Xtream:\n\n"
        "servidor: http://example.com\n"
        "puerto: 8080\n"
        "usuario: user\n"
        "contraseña: pass\n\n"
        "O envía un link M3U"
    )

# -------- CHECK -------- #

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()

    # 🔵 M3U → EXTRAER + CONSULTAR
    if texto.startswith("http") and "m3u" in texto:
        try:
            parsed = urlparse(texto)
            query = parse_qs(parsed.query)

            servidor = parsed.hostname
            puerto = parsed.port if parsed.port else "80"
            usuario = query.get("username", [None])[0]
            contraseña = query.get("password", [None])[0]

            if not usuario or not contraseña:
                await update.message.reply_text("❌ M3U inválido")
                return

            resultado = obtener_datos(servidor, puerto, usuario, contraseña)
            await update.message.reply_text(resultado)

        except:
            await update.message.reply_text("❌ Error procesando M3U")

        return

    # 🔴 XTREAM DIRECTO
    try:
        lineas = texto.split("\n")
        datos = {}

        for linea in lineas:
            if ":" in linea:
                clave, valor = linea.split(":", 1)
                datos[clave.strip().lower()] = valor.strip()

        servidor = datos.get("servidor", "").replace("http://", "").replace("https://", "")
        puerto = datos.get("puerto")
        usuario = datos.get("usuario")
        contraseña = datos.get("contraseña")

        if not all([servidor, puerto, usuario, contraseña]):
            await update.message.reply_text("❌ Datos incompletos")
            return

        resultado = obtener_datos(servidor, puerto, usuario, contraseña)
        await update.message.reply_text(resultado)

    except:
        await update.message.reply_text("❌ Error en formato")

# -------- MAIN -------- #

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(botones))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check))

print("🔥 BOT IPTV PRO MAX ACTIVO 🔥")
app.run_polling()