import logging
import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters, ConversationHandler
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8363405427:AAFt_QEW0eYnjsXTBd4Kf1jfFzFyP0Jn1LU"
ADMIN_ID = 6222097444
DANA_NUMBER = "085726956029"
HARGA_VIDEO = 1500
NAMA_BOT = "Kling Motion AI"

MENU, PILIH_JUMLAH, UPLOAD_FOTO, UPLOAD_AUDIO, TUNGGU_BAYAR = range(5)

ORDERS_FILE = "orders.json"

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (
        f"🎬 *Selamat datang di {NAMA_BOT}!*\n\n"
        f"Halo {user.first_name}! 👋\n\n"
        f"Kami membuat video AI berkualitas tinggi dengan teknologi *Kling Motion Control*.\n\n"
        f"💰 Harga: *Rp {HARGA_VIDEO:,}/video*\n\n"
        f"Pilih menu di bawah ini:"
    )
    keyboard = [
        [InlineKeyboardButton("🎬 Order Video", callback_data="order")],
        [InlineKeyboardButton("📋 Pesanan Saya", callback_data="pesanan")],
        [InlineKeyboardButton("❓ Cara Order", callback_data="cara")],
        [InlineKeyboardButton("📞 Hubungi Admin", url="https://t.me/sedang_mengetik_sekarang")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bottom_keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("🚀 Start"), KeyboardButton("💰 Pricing"), KeyboardButton("👤 Akun")]],
        resize_keyboard=True, is_persistent=True
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    await update.message.reply_text("Gunakan tombol di bawah untuk navigasi cepat! 👇", reply_markup=bottom_keyboard)
    return MENU

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "order":
        text = (
            "🎬 *Order Video Baru*\n\n"
            f"💰 Harga: *Rp {HARGA_VIDEO:,}/video*\n\n"
            "Mau order berapa video?"
        )
        keyboard = [
            [InlineKeyboardButton("1 video - Rp 1.500", callback_data="qty_1")],
            [InlineKeyboardButton("3 video - Rp 4.500", callback_data="qty_3")],
            [InlineKeyboardButton("5 video - Rp 7.500", callback_data="qty_5")],
            [InlineKeyboardButton("10 video - Rp 15.000", callback_data="qty_10")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="back_menu")],
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return PILIH_JUMLAH

    elif data.startswith("qty_"):
        qty = int(data.split("_")[1])
        total = qty * HARGA_VIDEO
        context.user_data["qty"] = qty
        context.user_data["total"] = total
        text = (
            f"✅ *{qty} video dipilih*\n\n"
            f"Total: *Rp {total:,}*\n\n"
            "📸 Kirim *foto/gambar* yang mau dijadikan video:"
        )
        keyboard = [[InlineKeyboardButton("❌ Batal", callback_data="back_menu")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return UPLOAD_FOTO

    elif data == "skip_audio":
        qty = context.user_data.get("qty", 1)
        total = context.user_data.get("total", HARGA_VIDEO)
        text = (
            f"💳 *Pembayaran*\n\n"
            f"Order: *{qty} video*\n"
            f"Total: *Rp {total:,}*\n\n"
            f"Scan QR DANA di bawah atau transfer ke:\n"
            f"📱 *{DANA_NUMBER}*\n\n"
            f"Setelah transfer, kirim *screenshot bukti bayar* ke sini! 📸"
        )
        await query.edit_message_text(text, parse_mode="Markdown")
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo="https://i.ibb.co/B5hTzvGm/photo-6086659757784633356-y.jpg",
            caption="📱 Scan QR DANA ini untuk bayar!"
        )
        return TUNGGU_BAYAR

    elif data == "pesanan":
        user_id = str(query.from_user.id)
        orders = load_orders()
        user_orders = {k: v for k, v in orders.items() if v["user_id"] == user_id}
        if not user_orders:
            text = "📋 *Pesanan Saya*\n\nKamu belum punya pesanan.\nAyo order sekarang! 🎬"
        else:
            text = "📋 *Pesanan Saya*\n\n"
            for oid, o in sorted(user_orders.items(), key=lambda x: int(x[0]), reverse=True)[:10]:
                status_emoji = {"pending": "⏳", "dibayar": "💳", "proses": "🔄", "selesai": "✅", "batal": "❌"}.get(o["status"], "❓")
                text += f"{status_emoji} *Order #{oid}*\n"
                text += f"   Qty: {o['qty']} video | Total: Rp {o['total']:,}\n"
                text += f"   Status: {o['status'].upper()} | {o['tanggal']}\n\n"
        keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="back_menu")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return MENU

    elif data == "cara":
        text = (
            "❓ *Cara Order*\n\n"
            "1️⃣ Klik *Order Video*\n"
            "2️⃣ Pilih jumlah video\n"
            "3️⃣ Kirim *foto* yang mau dijadikan video\n"
            "4️⃣ Kirim *referensi video/audio* sebagai backsound (opsional)\n"
            "5️⃣ Transfer ke DANA kami\n"
            "6️⃣ Kirim *bukti bayar*\n"
            "7️⃣ Tunggu video selesai\n"
            "8️⃣ Video dikirim ke kamu! 🎬\n\n"
            f"💰 Harga: *Rp {HARGA_VIDEO:,}/video*\n"
            f"💳 DANA: *{DANA_NUMBER}*"
        )
        keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="back_menu")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return MENU

    elif data == "back_menu":
        text = (
            f"🎬 *{NAMA_BOT}*\n\n"
            f"💰 Harga: *Rp {HARGA_VIDEO:,}/video*\n\n"
            "Pilih menu:"
        )
        keyboard = [
            [InlineKeyboardButton("🎬 Order Video", callback_data="order")],
            [InlineKeyboardButton("📋 Pesanan Saya", callback_data="pesanan")],
            [InlineKeyboardButton("❓ Cara Order", callback_data="cara")],
            [InlineKeyboardButton("📞 Hubungi Admin", url="https://t.me/sedang_mengetik_sekarang")],
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return MENU

    elif data.startswith("admin_selesai_"):
        order_id = data.split("_")[2]
        orders = load_orders()
        if order_id in orders:
            orders[order_id]["status"] = "selesai"
            save_orders(orders)
            user_id = int(orders[order_id]["user_id"])
            await context.bot.send_message(chat_id=user_id, text=f"✅ *Order #{order_id} Selesai!*\n\nVideo kamu sudah selesai! 🎬", parse_mode="Markdown")
            await query.edit_message_text(f"✅ Order #{order_id} ditandai selesai!")
        return MENU

    elif data.startswith("admin_proses_"):
        order_id = data.split("_")[2]
        orders = load_orders()
        if order_id in orders:
            orders[order_id]["status"] = "proses"
            save_orders(orders)
            user_id = int(orders[order_id]["user_id"])
            await context.bot.send_message(chat_id=user_id, text=f"🔄 *Order #{order_id} Sedang Diproses!*\n\nVideo kamu sedang dibuat, mohon tunggu! 🎬", parse_mode="Markdown")
            await query.edit_message_text(f"🔄 Order #{order_id} sedang diproses!")
        return MENU

    elif data.startswith("admin_batal_"):
        order_id = data.split("_")[2]
        orders = load_orders()
        if order_id in orders:
            orders[order_id]["status"] = "batal"
            save_orders(orders)
            user_id = int(orders[order_id]["user_id"])
            await context.bot.send_message(chat_id=user_id, text=f"❌ *Order #{order_id} Dibatalkan*\n\nHubungi admin untuk info lebih lanjut.", parse_mode="Markdown")
            await query.edit_message_text(f"❌ Order #{order_id} dibatalkan!")
        return MENU

    return MENU

async def terima_foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        context.user_data["foto_id"] = update.message.photo[-1].file_id
        text = (
            "✅ *Foto diterima!*\n\n"
            "🎵 Kirim *referensi video/audio* sebagai backsound\n"
            "_atau klik Skip jika tidak mau pakai backsound_"
        )
        keyboard = [[InlineKeyboardButton("⏭ Skip (tanpa backsound)", callback_data="skip_audio")]]
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return UPLOAD_AUDIO
    else:
        await update.message.reply_text("❌ Tolong kirim *foto/gambar* ya!", parse_mode="Markdown")
        return UPLOAD_FOTO

async def terima_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.video:
        context.user_data["audio_id"] = update.message.video.file_id
    elif update.message.audio:
        context.user_data["audio_id"] = update.message.audio.file_id
    elif update.message.voice:
        context.user_data["audio_id"] = update.message.voice.file_id
    elif update.message.document:
        context.user_data["audio_id"] = update.message.document.file_id

    qty = context.user_data.get("qty", 1)
    total = context.user_data.get("total", HARGA_VIDEO)
    text = (
        f"✅ *Audio diterima!*\n\n"
        f"💳 *Pembayaran*\n\n"
        f"Order: *{qty} video*\n"
        f"Total: *Rp {total:,}*\n\n"
        f"Scan QR DANA di bawah atau transfer ke:\n"
        f"📱 *{DANA_NUMBER}*\n\n"
        f"Setelah transfer, kirim *screenshot bukti bayar* ke sini! 📸"
    )
    await update.message.reply_text(text, parse_mode="Markdown")
    await update.message.reply_photo(
        photo="https://i.ibb.co/B5hTzvGm/photo-6086659757784633356-y.jpg",
        caption="📱 Scan QR DANA ini untuk bayar!"
    )
    return TUNGGU_BAYAR

async def terima_bukti_bayar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not (update.message.photo or update.message.document):
        await update.message.reply_text("❌ Tolong kirim *screenshot bukti bayar* ya!", parse_mode="Markdown")
        return TUNGGU_BAYAR

    orders = load_orders()
    order_id = str(next_order_id(orders))
    user = update.effective_user
    qty = context.user_data.get("qty", 1)
    total = context.user_data.get("total", HARGA_VIDEO)
    foto_id = context.user_data.get("foto_id", "")
    audio_id = context.user_data.get("audio_id", "")

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

    await update.message.reply_text(
        f"✅ *Bukti bayar diterima!*\n\n"
        f"Order ID: *#{order_id}*\n"
        f"Status: *Menunggu konfirmasi admin*\n\n"
        f"Video akan segera diproses! 🎬",
        parse_mode="Markdown"
    )

    bukti_id = update.message.photo[-1].file_id if update.message.photo else update.message.document.file_id
    caption = (
        f"🔔 *ORDER BARU #{order_id}*\n\n"
        f"👤 Nama: {user.first_name}\n"
        f"🆔 Username: @{user.username or 'N/A'}\n"
        f"🎬 Qty: {qty} video\n"
        f"💰 Total: Rp {total:,}\n"
        f"📅 Tanggal: {orders[order_id]['tanggal']}"
    )
    keyboard = [
        [
            InlineKeyboardButton("🔄 Proses", callback_data=f"admin_proses_{order_id}"),
            InlineKeyboardButton("✅ Selesai", callback_data=f"admin_selesai_{order_id}"),
        ],
        [InlineKeyboardButton("❌ Batal", callback_data=f"admin_batal_{order_id}")]
    ]
    await context.bot.send_photo(chat_id=ADMIN_ID, photo=bukti_id, caption=caption, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    if foto_id:
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=foto_id, caption=f"📸 Foto untuk Order #{order_id}")
    if audio_id:
        try:
            await context.bot.send_video(chat_id=ADMIN_ID, video=audio_id, caption=f"🎵 Referensi untuk Order #{order_id}")
        except Exception:
            await context.bot.send_document(chat_id=ADMIN_ID, document=audio_id, caption=f"🎵 Referensi untuk Order #{order_id}")

    context.user_data.clear()
    return MENU

async def admin_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    orders = load_orders()
    if not orders:
        await update.message.reply_text("Belum ada order.")
        return
    text = "📊 *Semua Order:*\n\n"
    for oid, o in sorted(orders.items(), key=lambda x: int(x[0]), reverse=True)[:20]:
        status_emoji = {"pending": "⏳", "dibayar": "💳", "proses": "🔄", "selesai": "✅", "batal": "❌"}.get(o["status"], "❓")
        text += f"{status_emoji} #{oid} | {o['nama']} | {o['qty']}vid | Rp{o['total']:,} | {o['status']}\n"
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

    await context.bot.send_message(chat_id=user_id, text=f"🎬 *Video Order #{order_id} Sudah Selesai!*\n\nBerikut video pesanan kamu:", parse_mode="Markdown")

    if reply_msg.video:
        await context.bot.send_video(chat_id=user_id, video=reply_msg.video.file_id)
    elif reply_msg.document:
        await context.bot.send_document(chat_id=user_id, document=reply_msg.document.file_id)
    elif reply_msg.photo:
        await context.bot.send_photo(chat_id=user_id, photo=reply_msg.photo[-1].file_id)

    orders[order_id]["status"] = "selesai"
    save_orders(orders)
    await update.message.reply_text(f"✅ Video Order #{order_id} berhasil dikirim ke pembeli!")

async def pricing_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    keyboard = [[InlineKeyboardButton("🎬 Order Sekarang", callback_data="order")]]
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
async def akun_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        f"Username: @{user.username or 'N/A'}\n"
        f"ID: {user.id}\n\n"
        f"📊 *Statistik Order*\n"
        f"Total Order: *{total_order}*\n"
        f"Total Video: *{total_video}*\n"
        f"Order Selesai: *{selesai}*\n"
        f"Total Belanja: *Rp {total_bayar:,}*"
    )
    keyboard = [[InlineKeyboardButton("📋 Lihat Pesanan", callback_data="pesanan")]]
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [CallbackQueryHandler(button_handler)],
            PILIH_JUMLAH: [CallbackQueryHandler(button_handler)],
            UPLOAD_FOTO: [
                MessageHandler(filters.PHOTO, terima_foto),
                CallbackQueryHandler(button_handler),
            ],
            UPLOAD_AUDIO: [
                MessageHandler(filters.AUDIO | filters.VOICE | filters.VIDEO | filters.Document.ALL, terima_audio),
                CallbackQueryHandler(button_handler),
            ],
            TUNGGU_BAYAR: [
                MessageHandler(filters.PHOTO | filters.Document.ALL, terima_bukti_bayar),
                CallbackQueryHandler(button_handler),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
        per_message=False,
    )

    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.Regex("^🚀 Start$"), start))
    app.add_handler(MessageHandler(filters.Regex("^💰 Pricing$"), pricing_handler))
    app.add_handler(MessageHandler(filters.Regex("^👤 Akun$"), akun_handler))
    app.add_handler(CommandHandler("orders", admin_orders))
    app.add_handler(CommandHandler("kirim", kirim_video))
    app.add_handler(CallbackQueryHandler(button_handler))

    print(f"✅ Bot {NAMA_BOT} berjalan...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
