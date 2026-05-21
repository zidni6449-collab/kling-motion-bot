import logging
import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8363405427:AAFt_QEW0eYnjsXTBd4Kf1jfFzFyP0Jn1LU"
ADMIN_ID = 6222097444
DANA_NUMBER = "085726956029"
HARGA_VIDEO = 1500
NAMA_BOT = "Kling Motion AI"
QR_URL = "https://i.ibb.co/B5hTzvGm/photo-6086659757784633356-y.jpg"
ORDERS_FILE = "orders.json"

# User states stored in memory
user_states = {}

def load_orders():
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_orders(orders):
    with open(ORDERS_FILE, "w") as f:
        json.dump(orders, f, indent=2)

def next_order_id(orders):
    if not orders:
        return 1
    return max(int(k) for k in orders.keys()) + 1

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("🚀 Start"), KeyboardButton("💰 Pricing"), KeyboardButton("👤 Akun")]],
        resize_keyboard=True, is_persistent=True
    )

def get_main_menu_inline():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 Order Video", callback_data="order")],
        [InlineKeyboardButton("📋 Pesanan Saya", callback_data="pesanan")],
        [InlineKeyboardButton("❓ Cara Order", callback_data="cara")],
        [InlineKeyboardButton("📞 Hubungi Admin", url="https://t.me/sedang_mengetik_sekarang")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(user.id)
    user_states[uid] = {"step": "menu"}
    text = (
        f"🎬 *Selamat datang di {NAMA_BOT}!*\n\n"
        f"Halo {user.first_name}! 👋\n\n"
        f"Teknologi *Kling Motion Control* terbaru.\n\n"
        f"💰 Harga: *Rp {HARGA_VIDEO:,}/video*\n\n"
        f"Pilih menu:"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_main_keyboard())
    await update.message.reply_text("👇 Menu utama:", reply_markup=get_main_menu_inline())

async def pricing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💰 *Daftar Harga*\n\n"
        "🎬 1 video = *Rp 1.500*\n"
        "🎬 3 video = *Rp 4.500*\n"
        "🎬 5 video = *Rp 7.500*\n"
        "🎬 10 video = *Rp 15.000*\n\n"
        "Teknologi Kling Motion Control\n"
        "Proses cepat dan hasil berkualitas!\n\n"
        "Mau order? Klik tombol di bawah!"
    )
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🎬 Order Sekarang", callback_data="order")]])
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)

async def akun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    orders = load_orders()
    user_orders = {k: v for k, v in orders.items() if v["user_id"] == str(user.id)}
    total_order = len(user_orders)
    total_video = sum(int(o["qty"]) for o in user_orders.values())
    total_bayar = sum(int(o["total"]) for o in user_orders.values())
    selesai = len([o for o in user_orders.values() if o["status"] == "selesai"])
    text = (
        f"👤 *Informasi Akun*\n\n"
        f"Nama: *{user.first_name}*\n"
        f"Username: @{user.username or 'N/A'}\n\n"
        f"📊 *Statistik Order*\n"
        f"Total Order: *{total_order}*\n"
        f"Total Video: *{total_video}*\n"
        f"Order Selesai: *{selesai}*\n"
        f"Total Belanja: *Rp {total_bayar:,}*"
    )
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("📋 Lihat Pesanan", callback_data="pesanan")]])
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    uid = str(query.from_user.id)

    if data == "order":
        user_states[uid] = {"step": "pilih_qty"}
        text = (
            "🎬 *Order Video Baru*\n\n"
            f"💰 Harga: *Rp {HARGA_VIDEO:,}/video*\n\n"
            "Mau order berapa video?"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("1 video - Rp 1.500", callback_data="qty_1")],
            [InlineKeyboardButton("3 video - Rp 4.500", callback_data="qty_3")],
            [InlineKeyboardButton("5 video - Rp 7.500", callback_data="qty_5")],
            [InlineKeyboardButton("10 video - Rp 15.000", callback_data="qty_10")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="back_menu")],
        ])
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)

    elif data.startswith("qty_"):
        qty = int(data.split("_")[1])
        total = qty * HARGA_VIDEO
        user_states[uid] = {"step": "upload_foto", "qty": qty, "total": total}
        text = (
            f"✅ *{qty} video dipilih*\n\n"
            f"Total: *Rp {total:,}*\n\n"
            "📸 Sekarang kirim *foto/gambar* yang mau dijadikan video:"
        )
        await query.edit_message_text(text, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Batal", callback_data="back_menu")]]))

    elif data == "skip_audio":
        state = user_states.get(uid, {})
        qty = state.get("qty", 1)
        total = state.get("total", HARGA_VIDEO)
        user_states[uid]["step"] = "tunggu_bayar"
        text = (
            f"💳 *Pembayaran*\n\n"
            f"Order: *{qty} video*\n"
            f"Total: *Rp {total:,}*\n\n"
            f"Scan QR DANA atau transfer ke:\n"
            f"📱 *{DANA_NUMBER}*\n\n"
            f"Setelah transfer, kirim *screenshot bukti bayar* ke sini! 📸"
        )
        await query.edit_message_text(text, parse_mode="Markdown")
        await context.bot.send_photo(chat_id=query.message.chat_id, photo=QR_URL, caption="📱 Scan QR DANA ini untuk bayar!")

    elif data == "pesanan":
        uid2 = str(query.from_user.id)
        orders = load_orders()
        user_orders = {k: v for k, v in orders.items() if v["user_id"] == uid2}
        if not user_orders:
            text = "📋 *Pesanan Saya*\n\nKamu belum punya pesanan.\nAyo order sekarang! 🎬"
        else:
            text = "📋 *Pesanan Saya*\n\n"
            for oid, o in sorted(user_orders.items(), key=lambda x: int(x[0]), reverse=True)[:10]:
                emoji = {"pending": "⏳", "dibayar": "💳", "proses": "🔄", "selesai": "✅", "batal": "❌"}.get(o["status"], "❓")
                text += f"{emoji} *Order #{oid}* | {o['qty']} video | Rp {o['total']:,}\n"
                text += f"   Status: {o['status'].upper()} | {o['tanggal']}\n\n"
        await query.edit_message_text(text, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="back_menu")]]))

    elif data == "cara":
        text = (
            "❓ *Cara Order*\n\n"
            "1️⃣ Klik *Order Video*\n"
            "2️⃣ Pilih jumlah video\n"
            "3️⃣ Kirim *foto* yang mau dijadikan video\n"
            "4️⃣ Kirim *referensi video/audio* (opsional)\n"
            "5️⃣ Transfer ke DANA atau scan QR\n"
            "6️⃣ Kirim *bukti bayar*\n"
            "7️⃣ Tunggu video selesai\n"
            "8️⃣ Video dikirim ke kamu! 🎬\n\n"
            f"💰 Harga: *Rp {HARGA_VIDEO:,}/video*\n"
            f"💳 DANA: *{DANA_NUMBER}*"
        )
        await query.edit_message_text(text, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="back_menu")]]))

    elif data == "back_menu":
        user_states[uid] = {"step": "menu"}
        text = f"🎬 *{NAMA_BOT}*\n\n💰 Harga: *Rp {HARGA_VIDEO:,}/video*\n\nPilih menu:"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_main_menu_inline())

    elif data.startswith("admin_proses_"):
        order_id = data.replace("admin_proses_", "")
        orders = load_orders()
        if order_id in orders:
            orders[order_id]["status"] = "proses"
            save_orders(orders)
            await context.bot.send_message(chat_id=int(orders[order_id]["user_id"]),
                text=f"🔄 *Order #{order_id} Sedang Diproses!*\n\nVideo kamu sedang dibuat, mohon tunggu! 🎬", parse_mode="Markdown")
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Selesai", callback_data=f"admin_selesai_{order_id}")],
                [InlineKeyboardButton("❌ Batal", callback_data=f"admin_batal_{order_id}")]
            ]))

    elif data.startswith("admin_selesai_"):
        order_id = data.replace("admin_selesai_", "")
        orders = load_orders()
        if order_id in orders:
            orders[order_id]["status"] = "selesai"
            save_orders(orders)
            await context.bot.send_message(chat_id=int(orders[order_id]["user_id"]),
                text=f"✅ *Order #{order_id} Selesai!*\n\nVideo kamu sudah selesai! 🎬", parse_mode="Markdown")
            await query.edit_message_reply_markup(reply_markup=None)

    elif data.startswith("admin_batal_"):
        order_id = data.replace("admin_batal_", "")
        orders = load_orders()
        if order_id in orders:
            orders[order_id]["status"] = "batal"
            save_orders(orders)
            await context.bot.send_message(chat_id=int(orders[order_id]["user_id"]),
                text=f"❌ *Order #{order_id} Dibatalkan*\n\nHubungi admin untuk info lebih lanjut.", parse_mode="Markdown")
            await query.edit_message_reply_markup(reply_markup=None)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(user.id)
    msg = update.message
    state = user_states.get(uid, {})
    step = state.get("step", "menu")

    # Handle bottom keyboard buttons
    if msg.text == "🚀 Start":
        await start(update, context)
        return
    elif msg.text == "💰 Pricing":
        await pricing(update, context)
        return
    elif msg.text == "👤 Akun":
        await akun(update, context)
        return

    if step == "upload_foto":
        if msg.photo:
            user_states[uid]["foto_id"] = msg.photo[-1].file_id
            user_states[uid]["step"] = "upload_audio"
            text = (
                "✅ *Foto diterima!*\n\n"
                "🎵 Kirim *referensi video/audio* sebagai backsound\n"
                "_atau klik Skip jika tidak mau pakai backsound_"
            )
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⏭ Skip (tanpa backsound)", callback_data="skip_audio")]])
            await msg.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await msg.reply_text("❌ Tolong kirim *foto/gambar* ya!", parse_mode="Markdown")

    elif step == "upload_audio":
        if msg.audio or msg.voice or msg.video or msg.document:
            if msg.video:
                user_states[uid]["audio_id"] = msg.video.file_id
            elif msg.audio:
                user_states[uid]["audio_id"] = msg.audio.file_id
            elif msg.voice:
                user_states[uid]["audio_id"] = msg.voice.file_id
            elif msg.document:
                user_states[uid]["audio_id"] = msg.document.file_id
            user_states[uid]["step"] = "tunggu_bayar"
            qty = state.get("qty", 1)
            total = state.get("total", HARGA_VIDEO)
            text = (
                f"✅ *Referensi diterima!*\n\n"
                f"💳 *Pembayaran*\n\n"
                f"Order: *{qty} video*\n"
                f"Total: *Rp {total:,}*\n\n"
                f"Scan QR DANA atau transfer ke:\n"
                f"📱 *{DANA_NUMBER}*\n\n"
                f"Setelah transfer, kirim *screenshot bukti bayar* ke sini! 📸"
            )
            await msg.reply_text(text, parse_mode="Markdown")
            await msg.reply_photo(photo=QR_URL, caption="📱 Scan QR DANA ini untuk bayar!")
        else:
            await msg.reply_text("❌ Kirim video/audio referensi atau klik *Skip*!", parse_mode="Markdown")

    elif step == "tunggu_bayar":
        if msg.photo or msg.document:
            orders = load_orders()
            order_id = str(next_order_id(orders))
            qty = state.get("qty", 1)
            total = state.get("total", HARGA_VIDEO)
            foto_id = state.get("foto_id", "")
            audio_id = state.get("audio_id", "")

            orders[order_id] = {
                "user_id": str(user.id),
                "username": user.username or "",
                "nama": user.first_name or "",
                "qty": qty,
                "total": total,
                "foto_id": foto_id,
                "audio_id": audio_id,
                "status": "dibayar",
                "tanggal": datetime.now().strftime("%d/%m/%Y %H:%M")
            }
            save_orders(orders)
            user_states[uid] = {"step": "menu"}

            await msg.reply_text(
                f"✅ *Bukti bayar diterima!*\n\n"
                f"Order ID: *#{order_id}*\n"
                f"Status: *Menunggu konfirmasi admin*\n\n"
                f"Video akan segera diproses! 🎬",
                parse_mode="Markdown"
            )

            bukti_id = msg.photo[-1].file_id if msg.photo else msg.document.file_id
            caption = (
                f"🔔 *ORDER BARU #{order_id}*\n\n"
                f"👤 {user.first_name} | @{user.username or 'N/A'}\n"
                f"🎬 {qty} video | Rp {total:,}\n"
                f"📅 {orders[order_id]['tanggal']}"
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Proses", callback_data=f"admin_proses_{order_id}"),
                 InlineKeyboardButton("✅ Selesai", callback_data=f"admin_selesai_{order_id}")],
                [InlineKeyboardButton("❌ Batal", callback_data=f"admin_batal_{order_id}")]
            ])
            await context.bot.send_photo(chat_id=ADMIN_ID, photo=bukti_id, caption=caption,
                parse_mode="Markdown", reply_markup=keyboard)
            if foto_id:
                await context.bot.send_photo(chat_id=ADMIN_ID, photo=foto_id, caption=f"📸 Foto Order #{order_id}")
            if audio_id:
                try:
                    await context.bot.send_video(chat_id=ADMIN_ID, video=audio_id, caption=f"🎵 Referensi Order #{order_id}")
                except Exception:
                    await context.bot.send_document(chat_id=ADMIN_ID, document=audio_id, caption=f"🎵 Referensi Order #{order_id}")
        else:
            await msg.reply_text("❌ Kirim *screenshot bukti bayar* ya!", parse_mode="Markdown")

    else:
        await msg.reply_text("Ketik /start untuk mulai! 😊")

async def admin_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    orders = load_orders()
    if not orders:
        await update.message.reply_text("Belum ada order.")
        return
    text = "📊 *Semua Order:*\n\n"
    for oid, o in sorted(orders.items(), key=lambda x: int(x[0]), reverse=True)[:20]:
        emoji = {"pending": "⏳", "dibayar": "💳", "proses": "🔄", "selesai": "✅", "batal": "❌"}.get(o["status"], "❓")
        text += f"{emoji} #{oid} | {o['nama']} | {o['qty']}vid | Rp{o['total']:,} | {o['status']}\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def kirim_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Format: /kirim ORDER_ID\nContoh: /kirim 5")
        return
    order_id = context.args[0]
    orders = load_orders()
    if order_id not in orders:
        await update.message.reply_text(f"Order #{order_id} tidak ditemukan!")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply ke video yang mau dikirim dulu!")
        return
    user_id = int(orders[order_id]["user_id"])
    reply_msg = update.message.reply_to_message
    await context.bot.send_message(chat_id=user_id,
        text=f"🎬 *Video Order #{order_id} Sudah Selesai!*\n\nBerikut video pesanan kamu:", parse_mode="Markdown")
    if reply_msg.video:
        await context.bot.send_video(chat_id=user_id, video=reply_msg.video.file_id)
    elif reply_msg.document:
        await context.bot.send_document(chat_id=user_id, document=reply_msg.document.file_id)
    elif reply_msg.photo:
        await context.bot.send_photo(chat_id=user_id, photo=reply_msg.photo[-1].file_id)
    orders[order_id]["status"] = "selesai"
    save_orders(orders)
    await update.message.reply_text(f"✅ Video Order #{order_id} berhasil dikirim!")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("orders", admin_orders))
    app.add_handler(CommandHandler("kirim", kirim_video))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    print(f"✅ Bot {NAMA_BOT} berjalan...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
