#!/usr/bin/env python3
import json
import re
import sys
from typing import Optional, Dict

INTENT_RULES = {
    'ajuda': [r'\b(ajuda|help|/start|oi|ol[aá]|ola|bom dia|boa tarde|boa noite)\b'],
    'devolucao_fornecedor': [r'\b(devolu[cç][aã]o|devolvendo|devolvendo pro|devolvendo para|devolucao)\b', r'\b(fornecedor)\b'],
    'voltou_estoque': [r'\b(voltou|retornou|retorno|dispon[íi]vel|disponivel|de volta|de volta ao estoque|retornou ao estoque)\b'],
    'usado_no_carro': [r'\b(usei|usado|retirado|retirada|aplicado|instalado|coloquei|utilizei)\b'],
    'buscar_peca': [r'\b(onde est[áa]|onde esta|cad[eê]|procura|procurei|localiza|localizar|saber onde|onde fica)\b']
}

VEHICLE_WORDS = {
    'cobalt', 'renegade', 'tcross', 'hb20', 'onix', 'fiesta', 'focus', 'gol', 'palio', 'uno',
    'ka', 'creta', 'city', 'civic', 'corolla', 'prisma', 'fox', 'jeep', 's10', 'hilux'
}

KNOWN_PARTS = [
    'lanterna', 'sensor', 'moldura', 'parachoque', 'farol', 'bateria', 'amortecedor', 'pastilha',
    'disco', 'embreagem', 'filtro', 'bomba', 'radiador', 'pneu', 'suspensao', 'escape', 'capo',
    'painel', 'porta', 'vidro', 'mola', 'corrente', 'engrenagem'
]

IGNORE_WORDS = {
    'onde', 'esta', 'esta', 'o', 'a', 'um', 'uma', 'de', 'do', 'da', 'no', 'na', 'por', 'pro',
    'para', 'com', 'sem', 'foi', 'me', 'minha', 'meu', 'peca', 'peça', 'veiculo', 'carro', 'peças'
}

PLATE_TOKEN = re.compile(r'\b([A-Za-z0-9-]{4,8})\b')


def normalize(text: str) -> str:
    text = text or ''
    text = text.strip()
    text = text.lower()
    # Convert accented characters
    text = re.sub(r'[áàâãä]', 'a', text)
    text = re.sub(r'[éèêë]', 'e', text)
    text = re.sub(r'[íìîï]', 'i', text)
    text = re.sub(r'[óòôõö]', 'o', text)
    text = re.sub(r'[úùûü]', 'u', text)
    text = re.sub(r'[ç]', 'c', text)
    return text


def extract_plate(text: str) -> Optional[str]:
    text = text or ''
    for token in PLATE_TOKEN.findall(text):
        candidate = re.sub(r'[^A-Za-z0-9]', '', token).upper()
        if len(candidate) < 4 or len(candidate) > 8:
            continue
        # Valid pattern 3 letters + 4 digits or 4 letters + 3 digits or mixed alnum
        if re.fullmatch(r'[A-Z]{3}\d{4}|[A-Z]{4}\d{3}|[A-Z0-9]{4,8}', candidate):
            return candidate
    return None


def extract_os(text: str) -> Optional[str]:
    text = text or ''
    patterns = [
        r'\bOS\s*[:\-]?\s*(\d{2,})\b',
        r'\bos\s*(?:numero|n[ºo]|#)?\s*[:\-]?\s*(\d{2,})\b',
        r'\bordem de servico\s*(?:numero)?\s*[:\-]?\s*(\d{2,})\b'
    ]
    for p in patterns:
        m = re.search(p, text, flags=re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def classify_intent(raw_text: str) -> str:
    normalized = normalize(raw_text)
    if not normalized:
        return 'desconhecido'

    for intent, regexes in INTENT_RULES.items():
        if intent == 'devolucao_fornecedor':
            # require both general word and fornecedor mention
            if all(re.search(r, normalized) for r in regexes):
                return 'devolucao_fornecedor'
            continue
        if any(re.search(r, normalized) for r in regexes):
            return intent
    return 'desconhecido'


def parse_piece(raw_text: str) -> Optional[str]:
    if not raw_text:
        return None
    lower = normalize(raw_text)
    for piece in KNOWN_PARTS:
        if re.search(rf'\b{re.escape(piece)}\b', lower):
            return piece.capitalize()

    tokens = re.findall(r"[a-z0-9]+", lower)
    for token in tokens:
        if token in IGNORE_WORDS or token in VEHICLE_WORDS:
            continue
        if token.isdigit():
            continue
        if len(token) <= 2:
            continue
        return token.capitalize()
    return None


def extract_reason(raw_text: str) -> Optional[str]:
    if not raw_text:
        return None
    lower = raw_text.strip()
    lower_norm = normalize(raw_text)
    if 'veio errado' in lower_norm:
        return 'veio errado'
    m = re.search(r'(?:motivo\s*[:\-]?\s*|porque\s+|pq\s+|pois\s+)(.+)', lower, flags=re.IGNORECASE)
    if m:
        reason = m.group(1).strip()
        if reason:
            return reason
    return None


def parse_message(raw_text: str) -> Dict[str, Optional[str]]:
    if not raw_text or not raw_text.strip():
        return {
            'intent': 'desconhecido',
            'peca': None,
            'peca_secundaria': None,
            'placa': None,
            'responsavel': None,
            'os_numero': None,
            'motivo': None
        }

    intent = classify_intent(raw_text)
    placa = extract_plate(raw_text)
    os_numero = extract_os(raw_text)
    peca = parse_piece(raw_text)
    motivo = extract_reason(raw_text)

    return {
        'intent': intent,
        'peca': peca,
        'peca_secundaria': None,
        'placa': placa,
        'responsavel': None,
        'os_numero': os_numero,
        'motivo': motivo
    }


def main() -> None:
    arg_text = ' '.join(sys.argv[1:]).strip()
    if not arg_text:
        print('Uso: python parser_bot.py "mensagem do cliente"')
        print('Exemplo: python parser_bot.py "onde está a lanterna renegade GGL8443"')
        sys.exit(0)

    parsed = parse_message(arg_text)
    print(json.dumps(parsed, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
