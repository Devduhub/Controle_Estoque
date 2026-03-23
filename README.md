<div align="center">

# 🤖 Bot Estoque Inteligente

**Automação inteligente de almoxarifado para oficinas automotivas**  
*Desenvolvido do zero por um gestor de estoque que resolveu um problema real com código*

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://core.telegram.org/bots)
[![OpenAI](https://img.shields.io/badge/OpenAI-Whisper-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com)
[![Make](https://img.shields.io/badge/Make-Automation-6D00CC?style=for-the-badge&logo=make&logoColor=white)](https://make.com)
[![Status](https://img.shields.io/badge/Status-Produção-00C853?style=for-the-badge)](#)

</div>

---

## 💡 O Problema Real

> Em uma oficina automotiva de grande porte, **peças de devolução desapareciam constantemente** — sem rastreamento, sem registro, sem responsável.  
> O prejuízo acumulado chegava a **R$ 100.000/mês** em peças perdidas e extravios.

A solução tradicional? Planilhas. Anotações em papel. WhatsApp sem estrutura.  
A solução que eu construí? Um **bot inteligente no Telegram** integrado ao banco de dados do estoque + **dois fluxos de automação no Make** para processar as notas fiscais automaticamente.

---

## 🎯 O que o sistema faz

```
Mecânico digita (ou fala) no Telegram
        ↓
Bot identifica a intenção da mensagem
        ↓
Registra no banco de dados em tempo real
        ↓
Estoque sempre atualizado. Devolução rastreada. Prejuízo zerado.
```

### Funcionalidades principais

| Função | Como usar | Exemplo |
|--------|-----------|---------|
| 🔍 **Buscar peça** | Perguntar onde está | `"onde está a lanterna renegade GGL***"` |
| 📦 **Registrar uso** | Informar que usou | `"usei o sensor cobalt GGL***** OS ****"` |
| ↩️ **Devolveu ao estoque** | Informar retorno | `"voltou ao estoque moldura onix ABC***"` |
| 🔄 **Devolução fornecedor** | Registrar devolução | `"devolução fornecedor farol veio errado"` |
| 🎙️ **Mensagem de voz** | Falar no Telegram | *(transcrição automática via Whisper)* |
| 📸 **Foto com legenda** | Tirar foto da peça | *(legenda é processada normalmente)* |

---

## 🏗️ Arquitetura do Projeto

```
botantishock/
│
├── 🤖 bot_telegram.py        # Núcleo do bot — recebe e responde mensagens
├── 🧠 parser_bot.py          # Motor de NLP — classifica intenções e extrai dados
├── 🔧 parserBot.js            # Versão JS do parser (compatibilidade Make/Node)
│
├── ⚙️  run_bot.bat            # Script de inicialização Windows
├── 📋 requirements.txt        # Dependências Python
├── 🔒 .env.example            # Modelo de variáveis de ambiente (NÃO commitar o .env real)
└── 📖 README.md               # Este arquivo
```

---

## 🧠 Como o Parser de NLP funciona

O `parser_bot.py` é o cérebro do sistema. Ele **não usa uma API de IA para classificar** — foi construído com lógica própria usando regex e dicionários, tornando-o rápido, gratuito e previsível.

```python
# Exemplo: o bot recebe essa mensagem
"onde está a lanterna do renegade GGL8443"

# O parser identifica:
{
  "intent": "buscar_peca",      # ← identificou que é uma busca
  "peca": "Lanterna",           # ← extraiu o nome da peça
  "placa": "GGL8443",           # ← extraiu a placa do veículo
  "os_numero": null,
  "motivo": null
}
```

### Intenções reconhecidas

```python
INTENT_RULES = {
    'buscar_peca':          # onde está / cadê / procura / localizar
    'usado_no_carro':       # usei / usado / retirado / aplicado / instalado
    'voltou_estoque':       # voltou / retornou / disponível / de volta
    'devolucao_fornecedor': # devolução + fornecedor (ambos obrigatórios)
    'ajuda':                # oi / ajuda / help / bom dia
}
```

---

## 🔊 Transcrição de Áudio com Whisper

Mecânicos com mãos ocupadas podem **mandar áudio** — o bot transcreve automaticamente usando o modelo `gpt-4o-transcribe` da OpenAI e processa o texto como uma mensagem normal.

```python
async def transcribe_audio(update, context):
    file_obj = await msg.voice.get_file()
    await file_obj.download_to_drive(local_path)
    transcript = openai.Audio.transcribe('gpt-4o-transcribe', f)
    # → texto processado pelo parser normalmente
```

---

## ⚡ Os 2 Fluxos de Automação no Make

Além do bot, construí **dois fluxos no Make** que automatizam o processamento de notas fiscais:

### Fluxo 1 — Automação de NFs
```
Nova NF recebida (e-mail/sistema)
    → Make captura os dados
    → Parser extrai: fornecedor, peças, quantidades, valores
    → Registra automaticamente no banco de dados do estoque
    → Notifica no Telegram em tempo real
```

### Fluxo 2 — Controle de Devoluções
```
Mecânico registra devolução via bot
    → Make processa o evento
    → Atualiza saldo no estoque
    → Gera registro auditável com data/hora/responsável
    → Elimina "peças fantasma" que causavam o prejuízo
```

> 💰 **Resultado:** Sistema implantado em produção. Prejuízo de R$ 100k/mês com peças de devolução perdidas foi **eliminado**.

---

## 🚀 Como rodar localmente

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/botantishock.git
cd botantishock
```

### 2. Configure as variáveis de ambiente
```bash
cp .env.example .env
# Edite o .env com seus tokens reais
```

```env
TELEGRAM_TOKEN=seu_token_aqui
OPENAI_API_KEY=sua_chave_aqui
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Execute
```bash
python bot_telegram.py
```

> No Windows, pode usar o `run_bot.bat` após configurar o `.env`.

---

## 🛠️ Stack Tecnológica

| Tecnologia | Uso |
|-----------|-----|
| **Python 3.11** | Linguagem principal do bot |
| **python-telegram-bot 20.6** | Framework assíncrono para Telegram |
| **OpenAI Whisper** | Transcrição de mensagens de voz |
| **Regex / NLP próprio** | Classificação de intenções sem API externa |
| **Make** | Automação dos fluxos de NF e devolução |
| **JavaScript / Node.js** | Parser alternativo para integração Make |

---

## 👨‍💻 Sobre o Autor

Construí este projeto como **Gerente de Almoxarifado** da Antishock — tendo formação formal em programação, identificando um problema real de negócio e resolvendo com tecnologia.

Este projeto representa minha transição para a área de tecnologia, combinando:
- Visão de processo (2+ anos de gestão operacional)
- Automação prática (Make, bots, integrações,n8n)
- Desenvolvimento (Python, JavaScript, APIs)

📎 [![LinkedIn](https://img.shields.io/badge/LinkedIn-automatizadu-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/automatizadu/)
[![Gmail](https://img.shields.io/badge/Gmail-eduardosilvapsn1-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:eduardosilvapsn1@gmail.com)

---

## 📄 Licença

MIT License — use, modifique e distribua à vontade.

---

<div align="center">

**⭐ Se esse projeto te inspirou, deixa uma estrela no repositório!**

*"Não esperei alguém resolver meu problema. Aprendi a resolver eu mesmo."*

</div>
