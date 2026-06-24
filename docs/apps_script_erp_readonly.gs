/**
 * Endpoint ERP/TRACER solo lectura para Gestion de Muestras.
 *
 * Uso:
 *   GET ?action=getDatosMuestraERP&cvc=53-2026CVC
 *
 * Datos confirmados:
 * - Hoja: LARGOS
 * - Fila de cabecera: 3
 * - Datos desde fila 4
 * - CVC en columna C
 * - Encabezado CVC: CTR. COMPRA
 *
 * Reglas:
 * - Solo lectura.
 * - No escribe en Google Sheets.
 * - No modifica stock.
 * - No aplica contratos.
 * - No depende de la interfaz TRACER.
 */

const ERP_READONLY_SHEET_NAME = 'LARGOS';
const ERP_HEADER_ROW = 3;
const ERP_DATA_START_ROW = 4;
const ERP_CVC_FALLBACK_COLUMN = 3;
const ERP_SOURCE = 'google_sheets_largos';

const ERP_FIELD_ALIASES = {
  cvc: ['CTR. COMPRA', 'CTR COMPRA', 'CVC', 'CONTRATO COMPRA', 'CONTRATO DE COMPRA'],
  proveedor: ['PROVEEDOR'],
  ref_proveedor: ['REF. PROVEEDOR', 'REF PROVEEDOR', 'REFERENCIA PROVEEDOR'],
  calidad: ['CALIDAD'],
  sacos_comprados: ['CANTIDAD SACOS'],
  kg_comprados: ['KG TEORICO', 'KG TEORICO ', 'KG TEORICO'],
  precio_compra: ['PRECIO FIJO'],
  incoterm: ['INCOTERM'],
  almacen_lote: ['ALMACEN / LONG / N LOTE', 'ALMACEN / LONG / NO LOTE', 'ALMACEN / LONG / Nº LOTE'],
  muestra: ['MUESTRA'],
  comentarios: ['COMENTARIOS'],
  stock_sacos: ['STOCK SACOS'],
  estado: ['ESTADO']
};

function doGet(e) {
  const action = e && e.parameter ? e.parameter.action : '';
  if (action === 'getDatosMuestraERP') {
    return jsonResponse(getDatosMuestraERP_(e.parameter.cvc || ''));
  }
  return jsonResponse({
    status: 'error',
    source: ERP_SOURCE,
    message: 'Accion no soportada',
    data: {},
    matches: []
  });
}

function getDatosMuestraERP_(cvc) {
  const normalizedCvc = normalizeCvc_(cvc);
  console.log('getDatosMuestraERP cvc=%s normalized=%s', cvc, normalizedCvc);

  if (!normalizedCvc) {
    return response_('error', '', {}, [], ['CVC obligatorio']);
  }

  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = spreadsheet.getSheetByName(ERP_READONLY_SHEET_NAME);
  if (!sheet) {
    console.log('Hoja no encontrada: %s', ERP_READONLY_SHEET_NAME);
    return response_('error', normalizedCvc, {}, [], ['No existe la hoja LARGOS']);
  }

  const lastRow = sheet.getLastRow();
  const lastColumn = sheet.getLastColumn();
  if (lastRow < ERP_DATA_START_ROW || lastColumn < ERP_CVC_FALLBACK_COLUMN) {
    return response_('not_found', normalizedCvc, {}, [], ['La hoja LARGOS no contiene datos suficientes']);
  }

  const headers = sheet.getRange(ERP_HEADER_ROW, 1, 1, lastColumn).getValues()[0];
  const fieldIndexes = mapHeaders_(headers);
  const warnings = missingFieldWarnings_(fieldIndexes);

  if (fieldIndexes.cvc === undefined) {
    fieldIndexes.cvc = ERP_CVC_FALLBACK_COLUMN - 1;
    warnings.push('No se detecto columna CTR. COMPRA por encabezado; se usa fallback columna C');
  }

  const data = sheet.getRange(ERP_DATA_START_ROW, 1, lastRow - ERP_DATA_START_ROW + 1, lastColumn).getValues();
  const matches = [];
  for (let rowIndex = 0; rowIndex < data.length; rowIndex++) {
    const row = data[rowIndex];
    const rowCvc = normalizeCvc_(row[fieldIndexes.cvc]);
    if (rowCvc !== normalizedCvc) {
      continue;
    }
    matches.push(recordFromRow_(row, fieldIndexes));
  }

  console.log('CVC %s matches=%s warnings=%s', normalizedCvc, matches.length, warnings.length);

  if (matches.length === 0) {
    return response_('not_found', normalizedCvc, {}, [], warnings);
  }
  if (matches.length > 1) {
    return response_('multiple', normalizedCvc, {}, matches, warnings);
  }
  return response_('found', normalizedCvc, matches[0], [], warnings);
}

function mapHeaders_(headers) {
  const fieldIndexes = {};
  for (let colIndex = 0; colIndex < headers.length; colIndex++) {
    const header = normalizeHeader_(headers[colIndex]);
    if (!header) {
      continue;
    }
    const fields = Object.keys(ERP_FIELD_ALIASES);
    for (let i = 0; i < fields.length; i++) {
      const field = fields[i];
      if (fieldIndexes[field] !== undefined) {
        continue;
      }
      if (headerMatches_(header, ERP_FIELD_ALIASES[field])) {
        fieldIndexes[field] = colIndex;
      }
    }
  }
  return fieldIndexes;
}

function headerMatches_(normalizedHeader, aliases) {
  for (let i = 0; i < aliases.length; i++) {
    const alias = normalizeHeader_(aliases[i]);
    if (normalizedHeader === alias || normalizedHeader.indexOf(alias) >= 0 || alias.indexOf(normalizedHeader) >= 0) {
      return true;
    }
  }
  return false;
}

function recordFromRow_(row, fieldIndexes) {
  const record = {};
  const fields = Object.keys(fieldIndexes);
  for (let i = 0; i < fields.length; i++) {
    const field = fields[i];
    const value = cleanValue_(row[fieldIndexes[field]]);
    if (value !== '') {
      record[field] = field === 'cvc' ? normalizeCvc_(value) : value;
    }
  }
  return record;
}

function missingFieldWarnings_(fieldIndexes) {
  const warnings = [];
  const fields = Object.keys(ERP_FIELD_ALIASES);
  for (let i = 0; i < fields.length; i++) {
    const field = fields[i];
    if (fieldIndexes[field] === undefined) {
      warnings.push('Columna no encontrada: ' + field);
    }
  }
  return warnings;
}

function normalizeCvc_(value) {
  const text = cleanValue_(value).toUpperCase().replace(/\s+/g, ' ').trim();
  if (['', '-', 'N/A', 'NA', 'NONE', 'NULL', 'NAN'].indexOf(text) >= 0) {
    return '';
  }
  return text;
}

function normalizeHeader_(value) {
  return cleanValue_(value)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[._:\/\\()\[\]-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .toUpperCase();
}

function cleanValue_(value) {
  if (value === null || value === undefined) {
    return '';
  }
  if (Object.prototype.toString.call(value) === '[object Date]') {
    return Utilities.formatDate(value, Session.getScriptTimeZone(), 'yyyy-MM-dd');
  }
  const text = String(value).trim();
  if (['', '-', 'none', 'null', 'nan', 'n/a', 'na'].indexOf(text.toLowerCase()) >= 0) {
    return '';
  }
  return text;
}

function response_(status, cvc, data, matches, warnings) {
  return {
    status: status,
    source: ERP_SOURCE,
    cvc: cvc,
    data: data || {},
    matches: matches || [],
    warnings: warnings || []
  };
}

function jsonResponse(payload) {
  return ContentService
    .createTextOutput(JSON.stringify(payload))
    .setMimeType(ContentService.MimeType.JSON);
}
