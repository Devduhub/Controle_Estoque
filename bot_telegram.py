#!/usr/bin/env python3
import json
import logging
import os
import sys
import tempfile
from typing import Optional, Dict

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from parser_bot import parse_message

try:
    import openai
except ImportError:
    openai = None

def get_response_message(parsed: Dict[str, any]) -> str:
    """Generate conversational response based on parsed intent."""
    intent = parsed.get('intent')
    peca = parsed.get('peca')
    placa = parsed.get('placa')
    os_numero = parsed.get('os_numero')
    motivo = parsed.get('motivo')

    if intent == 'ajuda':
        return "👋 Olá! Sou o assistente de estoque da Anti Shock.\n\nPosso ajudar com:\n• 🔍 Buscar peças no estoque\n• 📦 Registrar peças usadas no carro\n• ↩️ Marcar peças que voltaram ao estoque\n• 🔄 Devoluções ao fornecedor\n\nMande a sua dúvida!"
    
    if intent == 'buscar_peca':
        msg = f"🔍 Procurando por "
        if peca:
            msg += f"'{peca}'"
        if placa:
            msg += f" - Placa {placa}"
        msg += "...\n\n✓ Peça registrada no sistema. Consultando localização no estoque..."
        return msg
    
    if intent == 'usado_no_carro':
        msg = "✅ Peça utilizada no carro anotada!\n\n"
        if peca:
            msg += f"📌 Peça: {peca}\n"
        if placa:
            msg += f"🚗 Placa: {placa}\n"
        if os_numero:
            msg += f"📋 OS: {os_numero}\n"
        msg += "\n✓ Registro feito com sucesso!"
        return msg
    
    if intent == 'voltou_estoque':
        msg = "↩️ Peça retornou ao estoque!\n\n"
        if peca:
            msg += f"📌 Peça: {peca}\n"
        if placa:
            msg += f"🚗 Placa: {placa}\n"
        msg += "\n✓ Agora disponível no inventário!"
        return msg
    
    if intent == 'devolucao_fornecedor':
        msg = "🔄 Devolução ao fornecedor registrada!\n\n"
        if peca:
            msg += f"📌 Peça: {peca}\n"
        if placa:
            msg += f"🚗 Placa: {placa}\n"
        if motivo:
            msg += f"❌ Motivo: {motivo}\n"
        msg += "\n✓ Esta devolução será processada!"
        return msg
    
    return "❓ Desculpe, não entendi muito bem. Tente descrever de forma mais clara ou digite /help para ver os comandos."

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def parse_audio_transcription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
    if openai is None:
        return None
    token = os.getenv('OPENAI_API_KEY')
    if not token:
        return None
    openai.api_key = token
    msg = update.message
    if msg.voice:
        file_id = msg.voice.file_id
    elif msg.audio:
        file_id = msg.audio.file_id
    elif msg.document and msg.document.mime_type and msg.document.mime_type.startswith('audio'):
        file_id = msg.document.file_id
    else:
        return None

    bot_file = context.bot.get_file(file_id)
    # The telegram library method is asynchronous; use await in caller if needed.
    return bot_file


async def transcribe_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
    if openai is None:
        return None
    key = os.getenv('OPENAI_API_KEY')
    if not key:
        return None
    openai.api_key = key

    msg = update.message
    if msg is None:
        return None

    file_obj = None
    if msg.voice:
        file_obj = await msg.voice.get_file()
    elif msg.audio:
        file_obj = await msg.audio.get_file()
    elif msg.document and msg.document.mime_type and msg.document.mime_type.startswith('audio'):
        file_obj = await msg.document.get_file()
    else:
        return None

    if not file_obj:
        return None

    with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as tmp:
        local_path = tmp.name
    try:
        await file_obj.download_to_drive(local_path)
        # Use OpenAI whisper transcription
        with open(local_path, 'rb') as f:
            transcript = openai.Audio.transcribe('gpt-4o-transcribe', f)

        text = transcript.get('text') if isinstance(transcript, dict) else None
        if isinstance(text, str):
            return text.strip()
    except Exception as exc:
        logger.exception('Falha na transcrição de áudio: %s', exc)
    finally:
        try:
            os.remove(local_path)
        except Exception:
            pass
    return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f'[START] Usuário iniciou chat: {update.message.from_user.id}')
    await update.message.reply_text(
        'Olá! Envie texto, foto com legenda ou áudio para obter JSON no formato do estoque.'
    )



async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        'Envie texto com a descrição do pedido. Ex: "onde está a lanterna renegade GGL8443".'
    )


async def parse_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    # Se a mensagem for JSON com chave openai_api_key, use para transcrição local
    text_input = None
    if update.message.text:
        text_input = update.message.text

    if text_input:
        cleaned = text_input.strip()
        if cleaned.startswith('{') and cleaned.endswith('}'):
            try:
                data = json.loads(cleaned)
                key_candidate = data.get('openai_api_key') or data.get('openai_key') or data.get('api_key')
                if key_candidate:
                    os.environ['OPENAI_API_KEY'] = key_candidate
                # Se mensagem contém texto adicional em campo message
                if data.get('message'):
                    text_input = data.get('message')
                elif data.get('text'):
                    text_input = data.get('text')
            except json.JSONDecodeError:
                pass

    if update.message.caption and not text_input:
        text_input = update.message.caption

    if text_input:
        logger.info(f'[MSG] Processando: {text_input[:80]}')
        parsed = parse_message(text_input)
        logger.info(f'[RESPONSE] intent={parsed["intent"]}, placa={parsed["placa"]}')
        response_msg = get_response_message(parsed)
        await update.message.reply_text(response_msg)
        return

    # Handle audio transcription
    if update.message.voice or update.message.audio or (update.message.document and update.message.document.mime_type and update.message.document.mime_type.startswith('audio')):
        logger.info('[AUDIO] Recebido áudio, tentando transcrever...')
        transcribed = await transcribe_audio(update, context)
        if transcribed:
            logger.info(f'[AUDIO] Transcrição: {transcribed[:80]}')
            parsed = parse_message(transcribed)
            logger.info(f'[RESPONSE] intent={parsed["intent"]}, placa={parsed["placa"]}')
            response_msg = get_response_message(parsed)
            await update.message.reply_text(response_msg)
            return

        await update.message.reply_text(
            'Recebi áudio, mas não consegui transcrever automaticamente. Envie texto ou legenda.'
        )
        return

    # Photo without caption or unsupported content
    if update.message.photo and not update.message.caption:
        await update.message.reply_text('Recebi foto sem legenda. Envie um texto ou legenda para parsear.')
        return

    await update.message.reply_text('Envie texto, foto com legenda ou áudio para reconhecer.')


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Comando desconhecido. Envie texto de estoque ou msg com foto/áudio.')


def main() -> None:
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        print('Erro: defina a variável de ambiente TELEGRAM_TOKEN com o token do bot.')
        sys.exit(1)

    print('='*60)
    print('BOT ANTISHOCK ESTOQUE INICIADO COM SUCESSO')
    print('='*60)
    print(f'Hora: {__import__("datetime").datetime.now().strftime("%H:%M:%S")}')
    print('Status: Aguardando mensagens no Telegram...')
    print('='*60)
    print()

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, parse_update))
    app.add_handler(MessageHandler(filters.PHOTO | filters.VOICE | filters.AUDIO | filters.Document.ALL, parse_update))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    logger.info('Bot iniciado. Aguardando mensagens...')
    app.run_polling()


if __name__ == '__main__':
    main()
