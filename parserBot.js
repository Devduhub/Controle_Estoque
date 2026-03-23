const intentKeywords = {
  ajuda: [/\b(ajuda|help|\/start|oi|olá|ola|bom dia|boa tarde|boa noite)\b/i],
  devolucao_fornecedor: [/\b(devolu[cç][aã]o|devolvendo|devolvendo pro|devolvendo para|devolucao)\b/i, /\b(fornecedor|fornecedor)\b/i],
  voltou_estoque: [/\b(voltou|retornou|retorno|dispon[íi]vel|disponivel|de volta|devolvido ao estoque|devolvida ao estoque)\b/i],
  usado_no_carro: [/\b(usei|usado|retirado|retirada|aplicado|instalado|coloquei|utilizei)\b/i],
  buscar_peca: [/\b(onde est[áa]|onde esta|cad[eê]|procura|procurei|localiza|saber onde)\b/i]
};

const vehicleWords = [
  'cobalt','renegade','tcross','hb20','onix','fiesta','focus','gol','palio','uno','ka','creta','city','civic','corolla'
];

function normalizeText(text) {
  return text.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
}

function extractPlate(raw) {
  if (!raw) return null;
  // Remove dashes and spaces and convert to uppercase
  const cleaned = raw.toUpperCase().replace(/[-\s]/g, '');
  // Brazilian plate heuristics: 3 letters + 4 digits OR 4 letters + 3 digits
  if (/^[A-Z]{3}\d{4}$/.test(cleaned) || /^[A-Z]{4}\d{3}$/.test(cleaned) || /^[A-Z0-9]{4,8}$/.test(cleaned)) {
    return cleaned;
  }
  return null;
}

function findPlate(text) {
  if (!text) return null;
  // Find tokens looking like plates
  const tokens = text.match(/\b[\w-]{4,8}\b/g);
  if (!tokens) return null;
  for (const token of tokens) {
    const candidate = token.replace(/[^A-Za-z0-9]/g, '');
    const plate = extractPlate(candidate);
    if (plate) return plate;
  }
  return null;
}

function findOS(text) {
  if (!text) return null;
  const m = text.match(/\bOS\s*[:\-]?\s*(\d{2,})\b/i);
  if (m) return m[1];
  const m2 = text.match(/\b(?:OS|os|os\s+numero|nº\s*OS)\s*(\d{2,})\b/i);
  if (m2) return m2[1];
  return null;
}

function parsePiece(text) {
  if (!text) return null;
  // common part words and stop words
  const knownParts = [
    'lanterna','sensor','moldura','parachoque','farol','bateria','amortecedor','pastilha','disco','embreagem','filtro','bomba','radiador','pneu','suspensao','escape','capo','painel','porta','vidro'
  ];
  const cleaned = normalizeText(text);
  for (const part of knownParts) {
    const regex = new RegExp('\\b'+part+'\\b', 'i');
    if (regex.test(cleaned)) {
      return part.charAt(0).toUpperCase() + part.slice(1);
    }
  }
  // fallback: pick first non-stop word around keywords
  const ignore = new Set(['onde','esta','esta','o','a','um','uma','de','do','da','no','na','por','pro','para','com','sem','foi','foi','usado','usei','voltou','voltado','retornou','peca','peça','peça']);
  const tokens = cleaned.split(/[^a-z0-9]+/).filter(Boolean);
  for (const t of tokens) {
    if (ignore.has(t)) continue;
    if (vehicleWords.includes(t)) continue;
    if (/^\d+$/.test(t)) continue;
    if (t.length <= 2) continue;
    return t.charAt(0).toUpperCase() + t.slice(1);
  }
  return null;
}

function classifyIntent(rawText) {
  if (!rawText || !rawText.trim()) return 'desconhecido';
  const text = normalizeText(rawText);
  if (intentKeywords.ajuda.some(rx => rx.test(text))) return 'ajuda';
  if (intentKeywords.devolucao_fornecedor.every(rx => rx.test(text))) return 'devolucao_fornecedor';
  if (intentKeywords.voltou_estoque.some(rx => rx.test(text))) return 'voltou_estoque';
  if (intentKeywords.usado_no_carro.some(rx => rx.test(text))) return 'usado_no_carro';
  if (intentKeywords.buscar_peca.some(rx => rx.test(text))) return 'buscar_peca';
  return 'desconhecido';
}

function parseMessage(rawText) {
  if (!rawText || !rawText.trim()) {
    return {
      intent: 'desconhecido',
      peca: null,
      peca_secundaria: null,
      placa: null,
      responsavel: null,
      os_numero: null,
      motivo: null
    };
  }

  const intent = classifyIntent(rawText);
  const placa = findPlate(rawText);
  const os_numero = findOS(rawText);

  // tentativa simples de extrair motivo se for devolucao fornecedor
  let motivo = null;
  const m = rawText.match(/(?:motivo de|motivo:|porque|pq|pois|veio)\s+(.+)/i);
  if (m) {
    motivo = m[1].trim();
  } else if (/\bveio errado\b/i.test(rawText)) {
    motivo = 'veio errado';
  }

  const peca = parsePiece(rawText);

  return {
    intent,
    peca: peca || null,
    peca_secundaria: null,
    placa: placa || null,
    responsavel: null,
    os_numero: os_numero || null,
    motivo: motivo || null
  };
}

if (require.main === module) {
  const input = process.argv.slice(2).join(' ');
  if (!input) {
    console.log('Uso: node parserBot.js "texto da mensagem"');
    console.log('Exemplo: node parserBot.js "onde está a lanterna renegade GGL8443"');
    process.exit(0);
  }
  console.log(JSON.stringify(parseMessage(input), null, 2));
}

module.exports = { parseMessage };
