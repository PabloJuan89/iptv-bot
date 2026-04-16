import requests
import asyncio
import sqlite3
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8559219862:AAHERppsEHKsWkFFayYG5Zta8R-ISd8TXHU"
ADMIN_ID = 1044482533  # 🔥 TU ID

# -------- BASE DE DATOS -------- #

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    is_vip INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    fecha TEXT
)
""")

conn.commit()

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

async def obtener_datos(servidor, puerto, usuario, contraseña):
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

# -------- USUARIOS -------- #

def es_vip(user_id):
    cursor.execute("SELECT is_vip FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    return row and row[0] == 1

def registrar_usuario(user_id):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

# -------- COMANDOS -------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    registrar_usuario(user_id)

    await update.message.reply_text("🏢 BOT IPTV EMPRESA\nSolicita acceso VIP")

async def addvip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    uid = int(context.args[0])
    cursor.execute("UPDATE users SET is_vip=1 WHERE user_id=?", (uid,))
    conn.commit()

    await update.message.reply_text(f"✅ {uid} ahora es VIP")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM logs")
    checks = cursor.fetchone()[0]

    await update.message.reply_text(f"📊 Usuarios: {users}\nChecks: {checks}")

# -------- CHECK -------- #

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if not es_vip(user_id):
        await update.message.reply_text("🚫 Solo VIP")
        return

    texto = update.message.text.split("\n")
    tareas = []

    for linea in texto:
        if linea.startswith("http") and "m3u" in linea:
            parsed = urlparse(linea)
            query = parse_qs(parsed.query)

            servidor = parsed.hostname
            puerto = parsed.port or "80"
            usuario = query.get("username", [None])[0]
            contraseña = query.get("password", [None])[0]

            if usuario and contraseña:
                tareas.append(obtener_datos(servidor, puerto, usuario, contraseña))

    if not tareas:
        await update.message.reply_text("⚠️ No válido")
        return

    resultados = await asyncio.gather(*tareas)

    for r in resultados:
        await update.message.reply_text(r)

    cursor.execute("INSERT INTO logs (user_id, fecha) VALUES (?, ?)", (user_id, str(datetime.now())))
    conn.commit()

# -------- MAIN -------- #

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("addvip", addvip))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check))

print("🏢 BOT EMPRESA ACTIVO")
app.run_polling()