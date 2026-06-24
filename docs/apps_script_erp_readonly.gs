/**
 * Endpoint ERP/TRACER solo lectura para Gestion de Muestras.
 *
 * Uso:
 *   GET ?action=getDatosMuestraERP&cvc=53-2026CVC
 *
 * Reglas:
 * - Solo lectura.
 * - No escribe en Google Sheets.
 * - No modifica stock.
 * - No aplica contratos.
 * - No depende de la interfaz TRACER.
 */

const ERP_LARGOS_SHEET_NAME = 'LARGOS';
const ERP_CONTRACTS_SHEET_NAME = 'CONTRATOS';
const ERP_HEADER_ROW = 3;
const ERP_DATA_START_ROW = 4;
const ERP_CVC_FALLBACK_COLUMN = 3;
const ERP_CVV_FALLBACK_COLUMN = 37; // AK
const ERP_SOURCE = 'google_sheets_largos';
const TRACER_FUNCTION_CANDIDATES = [
  'getTrazabilidadPorCVC',
  'obtenerTrazabilidadPorCVC',
  'generarTrazabilidadPorCVC',
  'getSecuenciaMovimientosPorCVC',
  'obtenerSecuenciaMovimientosPorCVC'
];

const LARGOS_FIELD_ALIASES = {
  cvc: ['CTR. COMPRA', 'CTR COMPRA', 'CVC', 'CONTRATO COMPRA', 'CONTRATO DE COMPRA'],
  proveedor: ['PROVEEDOR'],
  ref_proveedor: ['REF. PROVEEDOR', 'REF PROVEEDOR', 'REFERENCIA PROVEEDOR'],
  calidad: ['CALIDAD'],
  sacos_comprados: ['CANTIDAD SACOS'],
  kg_comprados: ['KG TEORICO'],
  precio_compra: ['PRECIO FIJO'],
  incoterm: ['INCOTERM'],
  almacen_lote: ['ALMACEN / LONG / N LOTE', 'ALMACEN / LONG / NO LOTE', 'ALMACEN / LONG / NUMERO LOTE'],
  muestra: ['MUESTRA'],
  comentarios: ['COMENTARIOS'],
  stock_sacos: ['STOCK SACOS'],
  estado: ['ESTADO']
};

const CONTRACT_FIELD_ALIASES = {
  cvc: ['CTR. COMPRA', 'CTR COMPRA', 'CVC', 'CONTRATO COMPRA', 'CONTRATO DE COMPRA'],
  cvv: ['CTR VENTA', 'CTR. VENTA', 'CVV', 'CONTRATO VENTA'],
  cliente: ['CLIENTE'],
  calidad_venta: ['CALIDAD'],
  sacos_vendidos: ['N SACOS', 'NO SACOS', 'NUMERO SACOS', 'SACOS'],
  kg_vendidos: ['KG'],
  precio_venta: ['PRECIO VENTA C/TM', 'PRECIO VENTA CTM', 'PRECIO VENTA'],
  valor_contrato: ['VALOR CONTRATO EUROS', 'VALOR CONTRATO'],
  fecha_factura: ['FECHA FACTURA'],
  cobro: ['COBRO'],
  incoterm_venta: ['INCOTERM'],
  comentarios_venta: ['COMENTARIOS']
};

const MOVEMENT_FIELD_ALIASES = {
  origen: ['ORIGEN', 'HOJA', 'FUENTE'],
  fecha: ['FECHA', 'FECHA MOVIMIENTO', 'DATE'],
  tipo_operacion: ['TIPO OPERACION', 'TIPO DE OPERACION', 'OPERACION', 'MOVIMIENTO'],
  cvc: ['CTR. COMPRA', 'CTR COMPRA', 'CVC', 'CONTRATO COMPRA'],
  cvv: ['CTR VENTA', 'CTR. VENTA', 'CVV', 'CONTRATO VENTA'],
  cliente_proveedor: ['CLIENTE PROVEEDOR', 'CLIENTE/PROVEEDOR', 'CLIENTE', 'PROVEEDOR'],
  sacos: ['SACOS', 'N SACOS', 'NO SACOS', 'NUMERO SACOS', 'CANTIDAD SACOS'],
  calidad: ['CALIDAD'],
  estado: ['ESTADO', 'STATUS']
};

function doGet(e) {
  const action = e && e.parameter ? e.parameter.action : '';
  if (action === 'getDatosMuestraERP') {
    return jsonResponse(getDatosMuestraERP_(e.parameter.cvc || ''));
  }
  return jsonResponse(response_('error', '', {}, [], [], {}, [], [], {}, ['Accion no soportada']));
}

function getDatosMuestraERP_(cvc) {
  const normalizedCvc = normalizeCvc_(cvc);
  console.log('getDatosMuestraERP cvc=%s normalized=%s', cvc, normalizedCvc);

  if (!normalizedCvc) {
    return response_('error', '', {}, [], [], {}, [], [], {}, ['CVC obligatorio']);
  }

  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const largosResult = findLargosRecord_(spreadsheet, normalizedCvc);
  if (largosResult.status !== 'found') {
    return response_(
      largosResult.status,
      normalizedCvc,
      largosResult.data || {},
      largosResult.matches || [],
      [],
      {},
      [],
      [],
      {},
      largosResult.warnings || []
    );
  }

  const traceabilityResult = findTraceabilityMovements_(spreadsheet, normalizedCvc);
  const salesResult = findAssociatedSales_(spreadsheet, normalizedCvc, largosResult.data);
  const warnings = [].concat(largosResult.warnings || [], traceabilityResult.warnings || [], salesResult.warnings || []);
  const summary = buildCommercialSummary_(largosResult.data, salesResult.sales);
  const traceabilitySummary = buildTraceabilitySummary_(traceabilityResult.movements);
  const associatedCvvs = uniqueCvvs_(traceabilityResult.movements, salesResult.sales);

  console.log(
    'CVC %s largos=found movimientos=%s ventas=%s cvv=%s warnings=%s',
    normalizedCvc,
    traceabilityResult.movements.length,
    salesResult.sales.length,
    associatedCvvs.join(', '),
    warnings.length
  );

  return response_(
    'found',
    normalizedCvc,
    largosResult.data,
    [],
    salesResult.sales,
    summary,
    traceabilityResult.movements,
    associatedCvvs,
    traceabilitySummary,
    warnings
  );
}

function findLargosRecord_(spreadsheet, normalizedCvc) {
  const sheet = spreadsheet.getSheetByName(ERP_LARGOS_SHEET_NAME);
  if (!sheet) {
    return { status: 'error', data: {}, matches: [], warnings: ['No existe la hoja LARGOS'] };
  }

  const table = readSheetTable_(sheet, LARGOS_FIELD_ALIASES, ERP_CVC_FALLBACK_COLUMN, 'CTR. COMPRA');
  if (table.error) {
    return { status: 'error', data: {}, matches: [], warnings: [table.error] };
  }

  const matches = [];
  for (let i = 0; i < table.rows.length; i++) {
    const row = table.rows[i];
    const rowCvc = normalizeCvc_(row[table.fieldIndexes.cvc]);
    if (rowCvc === normalizedCvc) {
      matches.push(recordFromRow_(row, table.fieldIndexes));
    }
  }

  if (matches.length === 0) {
    return { status: 'not_found', data: {}, matches: [], warnings: table.warnings };
  }
  if (matches.length > 1) {
    return { status: 'multiple', data: {}, matches: matches, warnings: table.warnings };
  }
  return { status: 'found', data: matches[0], matches: [], warnings: table.warnings };
}

function findAssociatedSales_(spreadsheet, normalizedCvc, largosData) {
  const sheet = spreadsheet.getSheetByName(ERP_CONTRACTS_SHEET_NAME);
  if (!sheet) {
    return { sales: [], warnings: ['No existe la hoja CONTRATOS'] };
  }

  const table = readSheetTable_(sheet, CONTRACT_FIELD_ALIASES, ERP_CVC_FALLBACK_COLUMN, 'CTR. COMPRA');
  if (table.error) {
    return { sales: [], warnings: [table.error] };
  }
  if (table.fieldIndexes.cvv === undefined && sheet.getLastColumn() >= ERP_CVV_FALLBACK_COLUMN) {
    table.fieldIndexes.cvv = ERP_CVV_FALLBACK_COLUMN - 1;
    table.warnings.push('No se detecto columna CTR VENTA por encabezado; se usa fallback columna AK');
  }

  const sales = [];
  for (let i = 0; i < table.rows.length; i++) {
    const row = table.rows[i];
    const rowCvc = normalizeCvc_(row[table.fieldIndexes.cvc]);
    if (rowCvc === normalizedCvc) {
      sales.push(recordFromRow_(row, table.fieldIndexes));
    }
  }
  return { sales: sales, warnings: table.warnings };
}

function findTraceabilityMovements_(spreadsheet, normalizedCvc) {
  const tracerResult = tryTracerHook_(normalizedCvc);
  if (tracerResult.movements.length > 0) {
    return tracerResult;
  }
  const scanResult = scanMovementSheets_(spreadsheet, normalizedCvc);
  scanResult.warnings = [].concat(tracerResult.warnings || [], scanResult.warnings || []);
  return scanResult;
}

function tryTracerHook_(normalizedCvc) {
  const warnings = [];
  for (let i = 0; i < TRACER_FUNCTION_CANDIDATES.length; i++) {
    const name = TRACER_FUNCTION_CANDIDATES[i];
    try {
      const fn = globalThis[name];
      if (typeof fn !== 'function') {
        continue;
      }
      console.log('Usando funcion TRACER para trazabilidad: %s', name);
      const result = fn(normalizedCvc);
      const movements = normalizeTracerMovements_(result);
      return { movements: movements, warnings: warnings };
    } catch (err) {
      warnings.push('Funcion TRACER ' + name + ' fallo: ' + err);
    }
  }
  warnings.push('No se encontro funcion TRACER reutilizable; se escanean hojas con movimientos');
  return { movements: [], warnings: warnings };
}

function normalizeTracerMovements_(result) {
  if (!result) {
    return [];
  }
  if (Array.isArray(result)) {
    return result.map(normalizeMovementObject_).filter(hasMovementData_);
  }
  if (Array.isArray(result.movimientos)) {
    return result.movimientos.map(normalizeMovementObject_).filter(hasMovementData_);
  }
  if (Array.isArray(result.trazabilidad_movimientos)) {
    return result.trazabilidad_movimientos.map(normalizeMovementObject_).filter(hasMovementData_);
  }
  return [];
}

function scanMovementSheets_(spreadsheet, normalizedCvc) {
  const warnings = [];
  const movements = [];
  const sheets = spreadsheet.getSheets();
  for (let i = 0; i < sheets.length; i++) {
    const sheet = sheets[i];
    const name = sheet.getName();
    if (name === ERP_LARGOS_SHEET_NAME || name === ERP_CONTRACTS_SHEET_NAME) {
      continue;
    }
    const table = readMovementTable_(sheet);
    if (!table) {
      continue;
    }
    for (let rowIndex = 0; rowIndex < table.rows.length; rowIndex++) {
      const row = table.rows[rowIndex];
      const rowCvc = normalizeCvc_(row[table.fieldIndexes.cvc]);
      if (rowCvc !== normalizedCvc) {
        continue;
      }
      const movement = recordFromRow_(row, table.fieldIndexes);
      movement.origen = movement.origen || name;
      movements.push(normalizeMovementObject_(movement));
    }
  }
  if (movements.length === 0) {
    warnings.push('No se encontraron movimientos para el CVC en hojas escaneadas');
  }
  return { movements: movements, warnings: warnings };
}

function readMovementTable_(sheet) {
  const lastRow = sheet.getLastRow();
  const lastColumn = sheet.getLastColumn();
  if (lastRow < ERP_DATA_START_ROW || lastColumn < ERP_CVC_FALLBACK_COLUMN) {
    return null;
  }
  const maxHeaderRows = Math.min(10, lastRow);
  for (let headerRow = 1; headerRow <= maxHeaderRows; headerRow++) {
    const headers = sheet.getRange(headerRow, 1, 1, lastColumn).getValues()[0];
    const fieldIndexes = mapHeaders_(headers, MOVEMENT_FIELD_ALIASES);
    if (fieldIndexes.cvc !== undefined && (fieldIndexes.cvv !== undefined || fieldIndexes.tipo_operacion !== undefined || fieldIndexes.sacos !== undefined)) {
      const rows = sheet.getRange(headerRow + 1, 1, lastRow - headerRow, lastColumn).getValues();
      return { rows: rows, fieldIndexes: fieldIndexes };
    }
  }
  return null;
}

function normalizeMovementObject_(raw) {
  return {
    origen: cleanValue_(raw.origen || raw.source || raw.hoja || raw.fuente),
    fecha: cleanValue_(raw.fecha || raw.date),
    tipo_operacion: cleanValue_(raw.tipo_operacion || raw.operacion || raw.movimiento),
    cvc: normalizeCvc_(raw.cvc),
    cvv: normalizeCvc_(raw.cvv),
    cliente_proveedor: cleanValue_(raw.cliente_proveedor || raw.cliente || raw.proveedor || raw.counterparty),
    sacos: cleanValue_(raw.sacos || raw.bags),
    calidad: cleanValue_(raw.calidad || raw.quality),
    estado: cleanValue_(raw.estado || raw.status)
  };
}

function hasMovementData_(movement) {
  return Boolean(movement && (movement.cvc || movement.cvv || movement.tipo_operacion || movement.sacos));
}

function buildTraceabilitySummary_(movements) {
  let totalBags = 0;
  let inBags = 0;
  let outBags = 0;
  let appBags = 0;
  let deappBags = 0;
  const clients = {};
  const cvvs = {};
  for (let i = 0; i < movements.length; i++) {
    const movement = movements[i];
    const bags = parseNumber_(movement.sacos);
    const op = normalizeHeader_(movement.tipo_operacion);
    totalBags += Math.abs(bags);
    if (op.indexOf('ENTRADA') >= 0 || op.indexOf('COMPRA') >= 0) {
      inBags += Math.abs(bags);
    } else if (op.indexOf('SALIDA') >= 0 || op.indexOf('VENTA') >= 0) {
      outBags += Math.abs(bags);
    } else if (op.indexOf('DEAPP') >= 0 || op.indexOf('DE APP') >= 0) {
      deappBags += Math.abs(bags);
    } else if (op.indexOf('APP') >= 0) {
      appBags += Math.abs(bags);
    }
    if (cleanValue_(movement.cliente_proveedor)) {
      clients[cleanValue_(movement.cliente_proveedor)] = true;
    }
    if (cleanValue_(movement.cvv)) {
      cvvs[cleanValue_(movement.cvv)] = true;
    }
  }
  return {
    total_sacos_movidos: formatNumber_(totalBags),
    sacos_entrada: formatNumber_(inBags),
    sacos_salida: formatNumber_(outBags),
    sacos_app: formatNumber_(appBags),
    sacos_deapp: formatNumber_(deappBags),
    clientes_unicos: String(Object.keys(clients).length),
    numero_cvv: String(Object.keys(cvvs).length)
  };
}

function uniqueCvvs_(movements, sales) {
  const seen = {};
  const result = [];
  function add(cvv) {
    const clean = normalizeCvc_(cvv);
    if (clean && !seen[clean]) {
      seen[clean] = true;
      result.push(clean);
    }
  }
  for (let i = 0; i < movements.length; i++) {
    add(movements[i].cvv);
  }
  for (let j = 0; j < sales.length; j++) {
    add(sales[j].cvv);
  }
  return result;
}

function readSheetTable_(sheet, aliases, cvcFallbackColumn, cvcHeaderName) {
  const lastRow = sheet.getLastRow();
  const lastColumn = sheet.getLastColumn();
  if (lastRow < ERP_DATA_START_ROW || lastColumn < cvcFallbackColumn) {
    return { error: 'La hoja ' + sheet.getName() + ' no contiene datos suficientes' };
  }

  const headers = sheet.getRange(ERP_HEADER_ROW, 1, 1, lastColumn).getValues()[0];
  const fieldIndexes = mapHeaders_(headers, aliases);
  const warnings = missingFieldWarnings_(fieldIndexes, aliases);

  if (fieldIndexes.cvc === undefined) {
    fieldIndexes.cvc = cvcFallbackColumn - 1;
    warnings.push('No se detecto columna ' + cvcHeaderName + ' por encabezado; se usa fallback columna C');
  }

  const rows = sheet.getRange(ERP_DATA_START_ROW, 1, lastRow - ERP_DATA_START_ROW + 1, lastColumn).getValues();
  return { rows: rows, fieldIndexes: fieldIndexes, warnings: warnings };
}

function mapHeaders_(headers, aliasesByField) {
  const fieldIndexes = {};
  for (let colIndex = 0; colIndex < headers.length; colIndex++) {
    const header = normalizeHeader_(headers[colIndex]);
    if (!header) {
      continue;
    }
    const fields = Object.keys(aliasesByField);
    for (let i = 0; i < fields.length; i++) {
      const field = fields[i];
      if (fieldIndexes[field] !== undefined) {
        continue;
      }
      if (headerMatches_(header, aliasesByField[field])) {
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
      record[field] = field === 'cvc' || field === 'cvv' ? normalizeCvc_(value) : value;
    }
  }
  return record;
}

function buildCommercialSummary_(largosData, sales) {
  const kgPurchased = parseNumber_(largosData.kg_comprados);
  const purchasePrice = parseNumber_(largosData.precio_compra);
  let totalKgSold = 0;
  let totalBagsSold = 0;
  let salePriceSum = 0;
  let salePriceCount = 0;
  const clients = {};
  const cvvs = {};

  for (let i = 0; i < sales.length; i++) {
    const sale = sales[i];
    totalKgSold += parseNumber_(sale.kg_vendidos);
    totalBagsSold += parseNumber_(sale.sacos_vendidos);
    const salePrice = parseNumber_(sale.precio_venta);
    if (salePrice) {
      salePriceSum += salePrice;
      salePriceCount += 1;
    }
    if (cleanValue_(sale.cliente)) {
      clients[cleanValue_(sale.cliente)] = true;
    }
    if (cleanValue_(sale.cvv)) {
      cvvs[cleanValue_(sale.cvv)] = true;
    }
  }

  const averageSalePrice = salePriceCount ? salePriceSum / salePriceCount : 0;
  const summary = {
    total_kg_vendidos: formatNumber_(totalKgSold),
    total_sacos_vendidos: formatNumber_(totalBagsSold),
    numero_cvv: String(Object.keys(cvvs).length || sales.length),
    clientes_unicos: String(Object.keys(clients).length),
    kg_comprados: kgPurchased ? formatNumber_(kgPurchased) : '',
    kg_pendientes: kgPurchased ? formatNumber_(kgPurchased - totalKgSold) : '',
    precio_compra: purchasePrice ? formatNumber_(purchasePrice) : '',
    precio_venta_medio: averageSalePrice ? formatNumber_(averageSalePrice) : '',
    margen_bruto_medio: averageSalePrice && purchasePrice ? formatNumber_(averageSalePrice - purchasePrice) : ''
  };
  return summary;
}

function missingFieldWarnings_(fieldIndexes, aliasesByField) {
  const warnings = [];
  const fields = Object.keys(aliasesByField);
  for (let i = 0; i < fields.length; i++) {
    const field = fields[i];
    if (fieldIndexes[field] === undefined) {
      warnings.push('Columna no encontrada: ' + field);
    }
  }
  return warnings;
}

function parseNumber_(value) {
  const text = cleanValue_(value);
  if (!text) {
    return 0;
  }
  let normalized = text.replace(/\s+/g, '');
  if (normalized.indexOf(',') >= 0) {
    normalized = normalized.replace(/\./g, '').replace(',', '.');
  }
  normalized = normalized.replace(/[^0-9.-]/g, '');
  const number = Number(normalized);
  return isNaN(number) ? 0 : number;
}

function formatNumber_(value) {
  if (value === null || value === undefined || value === '') {
    return '';
  }
  const number = Number(value);
  if (isNaN(number)) {
    return String(value);
  }
  return String(Math.round(number * 100) / 100);
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
    .replace(/\u00BA/g, 'O')
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

function response_(status, cvc, data, matches, sales, summary, movements, associatedCvvs, traceabilitySummary, warnings) {
  return {
    status: status,
    source: ERP_SOURCE,
    cvc: cvc,
    data: data || {},
    matches: matches || [],
    ventas_asociadas: sales || [],
    resumen_comercial: summary || {},
    trazabilidad_movimientos: movements || [],
    cvv_asociados: associatedCvvs || [],
    resumen_trazabilidad: traceabilitySummary || {},
    warnings: warnings || []
  };
}

function jsonResponse(payload) {
  return ContentService
    .createTextOutput(JSON.stringify(payload))
    .setMimeType(ContentService.MimeType.JSON);
}
