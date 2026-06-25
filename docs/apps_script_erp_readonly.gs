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
const ERP_READONLY_VERSION = 'trace_fixed_columns_no_fact_almacen';
const ERP_TRACE_MAX_ROWS_PER_SHEET = 5000;
const ERP_ALMACEN_SHEET_NAME = 'ALMACÉN';
const ERP_ALMACEN_FALLBACK_SHEET_NAME = 'ALMACEN';
const ERP_APPLICATIONS_SHEET_NAME = 'APLICACIONES';

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

function doGet(e) {
  try {
    const action = e && e.parameter ? e.parameter.action : '';
    if (action === 'getDatosMuestraERP') {
      return jsonResponse(getDatosMuestraERP_(e.parameter.cvc || ''));
    }
    if (action === 'getTrazabilidadMuestraERP') {
      return jsonResponse(getTrazabilidadMuestraERP_(e.parameter.cvc || ''));
    }
    return jsonResponse(response_('error', '', {}, [], [], {}, [], [], {}, ['Accion no soportada']));
  } catch (err) {
    console.log('Error no controlado ERP endpoint: %s', err && err.stack ? err.stack : err);
    return jsonResponse(response_('error', '', {}, [], [], {}, [], [], {}, [String(err)]));
  }
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

  return response_(
    'found',
    normalizedCvc,
    largosResult.data,
    [],
    [],
    {},
    [],
    [],
    {},
    largosResult.warnings || []
  );
}

function getTrazabilidadMuestraERP_(cvc) {
  const startedAt = new Date();
  const startedMs = Date.now();
  const normalizedCvc = normalizeCvc_(cvc);
  console.log('getTrazabilidadMuestraERP cvc=%s normalized=%s', cvc, normalizedCvc);

  if (!normalizedCvc) {
    return traceResponse_(response_('error', '', {}, [], [], {}, [], [], {}, ['CVC obligatorio']), startedAt, startedMs, { sheets: [], rows: 0 });
  }

  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const largosResult = findLargosRecord_(spreadsheet, normalizedCvc);
  if (largosResult.status !== 'found') {
    return traceResponse_(response_(
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
    ), startedAt, startedMs, { sheets: [], rows: 0 });
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

  const stats = mergeTraceStats_(traceabilityResult.stats, salesResult.stats);
  return traceResponse_(response_(
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
  ), startedAt, startedMs, stats);
}

function test_getTrazabilidadMuestraERP_18_2026CVC() {
  const result = getTrazabilidadMuestraERP_('18-2026CVC');
  console.log(JSON.stringify(result, null, 2));
  return result;
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
    return { sales: [], warnings: ['No existe la hoja CONTRATOS'], stats: { sheets: [], rows: 0 } };
  }

  const lastRow = sheet.getLastRow();
  const lastColumn = sheet.getLastColumn();
  if (lastRow < 2 || lastColumn < 64) {
    return { sales: [], warnings: ['La hoja CONTRATOS no contiene columnas hasta BL'], stats: { sheets: [ERP_CONTRACTS_SHEET_NAME], rows: 0 } };
  }

  let dataRows = lastRow - 1;
  const warnings = [];
  if (dataRows > ERP_TRACE_MAX_ROWS_PER_SHEET) {
    dataRows = ERP_TRACE_MAX_ROWS_PER_SHEET;
    warnings.push('Hoja CONTRATOS limitada a ' + ERP_TRACE_MAX_ROWS_PER_SHEET + ' filas para evitar timeout');
  }
  const rows = sheet.getRange(2, 1, dataRows, lastColumn).getValues();
  const sales = [];
  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];
    const rowCvc = normalizeCvc_(row[2]); // CONTRATOS C
    if (rowCvc === normalizedCvc) {
      const sale = contractSaleFromFixedRow_(row);
      if (sale.cvv) {
        sales.push(sale);
      }
    }
  }
  return { sales: sales, warnings: warnings, stats: { sheets: [ERP_CONTRACTS_SHEET_NAME], rows: rows.length } };
}

function findTraceabilityMovements_(spreadsheet, normalizedCvc) {
  return readFixedTraceabilitySheets_(spreadsheet, normalizedCvc);
}

function readFixedTraceabilitySheets_(spreadsheet, normalizedCvc) {
  const warnings = [];
  const movements = [];
  const sheetsConsulted = [];
  let rowsAnalyzed = 0;

  const almacenResult = findAlmacenMovements_(spreadsheet, normalizedCvc);
  warnings.push.apply(warnings, almacenResult.warnings || []);
  movements.push.apply(movements, almacenResult.movements || []);
  rowsAnalyzed += almacenResult.stats.rows;
  if (almacenResult.stats.sheets.length > 0) {
    sheetsConsulted.push.apply(sheetsConsulted, almacenResult.stats.sheets);
  }

  const applicationsResult = findApplicationMovements_(spreadsheet, normalizedCvc);
  warnings.push.apply(warnings, applicationsResult.warnings || []);
  movements.push.apply(movements, applicationsResult.movements || []);
  rowsAnalyzed += applicationsResult.stats.rows;
  if (applicationsResult.stats.sheets.length > 0) {
    sheetsConsulted.push.apply(sheetsConsulted, applicationsResult.stats.sheets);
  }

  if (movements.length === 0) {
    warnings.push('No se encontraron movimientos en ALMACEN/APLICACIONES para el CVC');
  }
  return { movements: movements, warnings: warnings, stats: { sheets: sheetsConsulted, rows: rowsAnalyzed } };
}

function findAlmacenMovements_(spreadsheet, normalizedCvc) {
  const sheet = spreadsheet.getSheetByName(ERP_ALMACEN_SHEET_NAME) || spreadsheet.getSheetByName(ERP_ALMACEN_FALLBACK_SHEET_NAME);
  if (!sheet) {
    return { movements: [], warnings: ['No existe la hoja ALMACEN'], stats: { sheets: [], rows: 0 } };
  }

  const lastRow = sheet.getLastRow();
  const lastColumn = sheet.getLastColumn();
  if (lastRow < 2 || lastColumn < 28) {
    return { movements: [], warnings: ['La hoja ALMACEN no contiene columnas hasta AB'], stats: { sheets: [sheet.getName()], rows: 0 } };
  }

  let dataRows = lastRow - 1;
  const warnings = [];
  if (dataRows > ERP_TRACE_MAX_ROWS_PER_SHEET) {
    dataRows = ERP_TRACE_MAX_ROWS_PER_SHEET;
    warnings.push('Hoja ' + sheet.getName() + ' limitada a ' + ERP_TRACE_MAX_ROWS_PER_SHEET + ' filas para evitar timeout');
  }
  const rows = sheet.getRange(2, 1, dataRows, lastColumn).getValues();
  const movements = [];
  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];
    if (normalizeCvc_(row[9]) === normalizedCvc) { // ALMACEN J
      movements.push(almacenMovementFromFixedRow_(row));
    }
  }
  return { movements: movements, warnings: warnings, stats: { sheets: [sheet.getName()], rows: rows.length } };
}

function findApplicationMovements_(spreadsheet, normalizedCvc) {
  const sheet = spreadsheet.getSheetByName(ERP_APPLICATIONS_SHEET_NAME);
  if (!sheet) {
    return { movements: [], warnings: ['No existe la hoja APLICACIONES'], stats: { sheets: [], rows: 0 } };
  }

  const lastRow = sheet.getLastRow();
  const lastColumn = sheet.getLastColumn();
  if (lastRow < 2 || lastColumn < 13) {
    return { movements: [], warnings: ['La hoja APLICACIONES no contiene columnas hasta M'], stats: { sheets: [ERP_APPLICATIONS_SHEET_NAME], rows: 0 } };
  }

  let dataRows = lastRow - 1;
  const warnings = [];
  if (dataRows > ERP_TRACE_MAX_ROWS_PER_SHEET) {
    dataRows = ERP_TRACE_MAX_ROWS_PER_SHEET;
    warnings.push('Hoja APLICACIONES limitada a ' + ERP_TRACE_MAX_ROWS_PER_SHEET + ' filas para evitar timeout');
  }
  const rows = sheet.getRange(2, 1, dataRows, lastColumn).getValues();
  const movements = [];
  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];
    if (normalizeCvc_(row[4]) === normalizedCvc) { // APLICACIONES E
      movements.push(applicationMovementFromFixedRow_(row));
    }
  }
  return { movements: movements, warnings: warnings, stats: { sheets: [ERP_APPLICATIONS_SHEET_NAME], rows: rows.length } };
}

function contractSaleFromFixedRow_(row) {
  return {
    cvc: normalizeCvc_(row[2]),            // C
    cvv: normalizeCvc_(row[36]),           // AK
    cliente: cleanValue_(row[39]),         // AN
    sacos_vendidos: cleanValue_(row[43]),  // AR
    fecha_factura: cleanValue_(row[56]),   // BE
    transporte: cleanValue_(row[59]),      // BH
    comentarios_venta: cleanValue_(row[63]) // BL
  };
}

function almacenMovementFromFixedRow_(row) {
  const cvv = normalizeCvc_(row[25]); // Z
  return {
    origen: 'ALMACEN',
    fecha: cleanValue_(cvv ? row[22] : row[1]), // W salida / B entrada
    tipo_operacion: cvv ? 'SALIDA' : 'ENTRADA',
    cvc: normalizeCvc_(row[9]),        // J
    cvv: cvv,
    cliente_proveedor: cleanValue_(row[24]), // Y
    sacos: cleanValue_(cvv ? row[27] : row[12]), // AB vendidos / M entrada
    calidad: cleanValue_(row[8]),      // I
    estado: '',
    almacen: cleanValue_(row[0]),      // A
    stock_sacos: cleanValue_(row[21]), // V
    comentarios: cleanValue_(row[20])  // U
  };
}

function applicationMovementFromFixedRow_(row) {
  return {
    origen: 'APLICACIONES',
    fecha: cleanValue_(row[1]),       // B
    tipo_operacion: cleanValue_(row[3]), // D
    cvc: normalizeCvc_(row[4]),       // E
    cvv: normalizeCvc_(row[5]),       // F
    cliente_proveedor: '',
    sacos: cleanValue_(row[6]),       // G
    calidad: '',
    estado: cleanValue_(row[12]),     // M
    id_aplicacion: cleanValue_(row[0]), // A
    almacen: cleanValue_(row[7]),     // H
    periodo: cleanValue_(row[8]),     // I
    comentario: cleanValue_(row[9]),  // J
    id_origen: cleanValue_(row[10])   // K
  };
}

function buildTraceabilitySummary_(movements) {
  if (!movements || movements.length === 0) {
    return {};
  }
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

function mergeTraceStats_(movementStats, salesStats) {
  const seen = {};
  const sheets = [];
  let rows = 0;
  function addStats(stats) {
    if (!stats) {
      return;
    }
    rows += Number(stats.rows || 0);
    const names = stats.sheets || [];
    for (let i = 0; i < names.length; i++) {
      const name = cleanValue_(names[i]);
      if (name && !seen[name]) {
        seen[name] = true;
        sheets.push(name);
      }
    }
  }
  addStats(movementStats);
  addStats(salesStats);
  return { sheets: sheets, rows: rows };
}

function readSheetTable_(sheet, aliases, cvcFallbackColumn, cvcHeaderName, maxRows) {
  const lastRow = sheet.getLastRow();
  const lastColumn = sheet.getLastColumn();
  if (lastRow <= 0 || lastColumn <= 0) {
    return { error: 'La hoja ' + sheet.getName() + ' esta vacia' };
  }
  if (lastRow < ERP_DATA_START_ROW || lastColumn < cvcFallbackColumn) {
    return { error: 'La hoja ' + sheet.getName() + ' no contiene datos suficientes' };
  }

  if (lastColumn <= 0) {
    return { error: 'La hoja ' + sheet.getName() + ' no contiene columnas suficientes' };
  }
  const headers = sheet.getRange(ERP_HEADER_ROW, 1, 1, lastColumn).getValues()[0];
  const fieldIndexes = mapHeaders_(headers, aliases);
  const warnings = missingFieldWarnings_(fieldIndexes, aliases);

  if (fieldIndexes.cvc === undefined) {
    fieldIndexes.cvc = cvcFallbackColumn - 1;
    warnings.push('No se detecto columna ' + cvcHeaderName + ' por encabezado; se usa fallback columna C');
  }

  let dataRows = lastRow - ERP_DATA_START_ROW + 1;
  if (dataRows <= 0 || lastColumn <= 0) {
    return { error: 'La hoja ' + sheet.getName() + ' no contiene filas de datos' };
  }
  if (maxRows && dataRows > maxRows) {
    dataRows = maxRows;
    warnings.push('Hoja ' + sheet.getName() + ' limitada a ' + maxRows + ' filas para evitar timeout');
  }
  const rows = sheet.getRange(ERP_DATA_START_ROW, 1, dataRows, lastColumn).getValues();
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

function traceResponse_(payload, startedAt, startedMs, stats) {
  payload.source = 'google_sheets_trace';
  payload.version = ERP_READONLY_VERSION;
  payload.trazabilidad_movimientos = payload.trazabilidad_movimientos || [];
  payload.cvv_asociados = payload.cvv_asociados || [];
  payload.resumen_trazabilidad = payload.resumen_trazabilidad || {};
  payload.warnings = payload.warnings || [];
  payload.started_at = startedAt ? Utilities.formatDate(startedAt, Session.getScriptTimeZone(), "yyyy-MM-dd'T'HH:mm:ss") : '';
  payload.elapsed_ms = startedMs ? Date.now() - startedMs : 0;
  payload.hojas_consultadas = stats && stats.sheets ? stats.sheets : [];
  payload.filas_analizadas = stats && stats.rows ? stats.rows : 0;
  return payload;
}

function jsonResponse(payload) {
  return ContentService
    .createTextOutput(JSON.stringify(payload))
    .setMimeType(ContentService.MimeType.JSON);
}
