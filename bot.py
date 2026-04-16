import requests
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = "8559219862:AAHERppsEHKsWkFFayYG5Zta8R-ISd8TXHU"

# 🔐 límite simple
user_limit = {}

# -------- FUNCIONES -------- #

def fecha_bonita(timestamp):
    try:
        return datetime.fromtimestamp(int(timestamp)).strftime('%d/%m/%Y')
    except:
        return "N/A"

def detectar_protocolo(servidor, puerto):
    try:
        if requests.get(f"https://{servidor}:{puerto}", timeout=5, verify=False).status_code < 500:
            return "https"
    except:
        pass
    return "http"

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

        tipo = "Premium"
        if user.get("is_trial") == "1":
            tipo = "Trial"

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
    botones = [[InlineKeyboardButton("📡 Verificar IPTV", callback_data="check")]]
    await update.message.reply_text("📺 BOT IPTV PRO MAX++", reply_markup=InlineKeyboardMarkup(botones))

# -------- BOTONES -------- #

async def botones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "Envía:\n- Datos Xtream\n- Uno o varios links M3U"
    )

# -------- CHECK -------- #

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    # 🔐 límite simple
    user_limit[user_id] = user_limit.get(user_id, 0) + 1
    if user_limit[user_id] > 20:
        await update.message.reply_text("🚫 Límite alcanzado")
        return

    texto = update.message.text.strip().split("\n")

    resultados = []

    for linea in texto:
        linea = linea.strip()

        # 🔵 M3U
        if linea.startswith("http") and "m3u" in linea:
            try:
                parsed = urlparse(linea)
                query = parse_qs(parsed.query)

                servidor = parsed.hostname
                puerto = parsed.port or "80"
                usuario = query.get("username", [None])[0]
                contraseña = query.get("password", [None])[0]

                if usuario and contraseña:
                    resultados.append(obtener_datos(servidor, puerto, usuario, contraseña))
                else:
                    resultados.append("❌ M3U inválido")

            except:
                resultados.append("❌ Error M3U")

        # 🔴 XTREAM
        elif "servidor:" in linea:
            try:
                datos = {}
                for l in texto:
                    if ":" in l:
                        k, v = l.split(":", 1)
                        datos[k.strip().lower()] = v.strip()

                servidor = datos.get("servidor", "").replace("http://", "").replace("https://", "")
                puerto = datos.get("puerto")
                usuario = datos.get("usuario")
                contraseña = datos.get("contraseña")

                resultados.append(obtener_datos(servidor, puerto, usuario, contraseña))
                break

            except:
                resultados.append("❌ Error Xtream")

    if not resultados:
        await update.message.reply_text("⚠️ No se detectaron datos")
        return

    # 🔥 enviar resultados
    for r in resultados:
        await update.message.reply_text(r)

# -------- MAIN -------- #

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(botones))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check))

print("🔥 BOT IPTV PRO MAX++ ACTIVO 🔥")
app.run_polling()