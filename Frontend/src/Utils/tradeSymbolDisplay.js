const MONTH_NAMES = {
  1: 'JAN',
  2: 'FEB',
  3: 'MAR',
  4: 'APR',
  5: 'MAY',
  6: 'JUN',
  7: 'JUL',
  8: 'AUG',
  9: 'SEP',
  10: 'OCT',
  11: 'NOV',
  12: 'DEC',
};

const MONTH_NUMBERS = {
  JAN: 1,
  FEB: 2,
  MAR: 3,
  APR: 4,
  MAY: 5,
  JUN: 6,
  JUL: 7,
  AUG: 8,
  SEP: 9,
  OCT: 10,
  NOV: 11,
  DEC: 12,
};

const cleanText = (value) => String(value || '').trim();

const compactText = (value) => cleanText(value).toUpperCase().replace(/[^A-Z0-9]/g, '');

const isCompleteOptionSymbol = (value) => {
  const compact = compactText(value);
  return Boolean(compact && /\d/.test(compact) && /(CE|PE|C|P)$/.test(compact));
};

const firstPresent = (...values) => values.find((value) => cleanText(value));

const normalizeOptionType = (value) => {
  const optionType = cleanText(value).toUpperCase();
  if (optionType === 'C') return 'CE';
  if (optionType === 'P') return 'PE';
  if (optionType === 'CE' || optionType === 'PE') return optionType;
  return '';
};

const normalizeUnderlying = (value) => {
  const compact = compactText(value);
  if (!compact) return '';
  const optionIndex = compact.search(/(\d|CE|PE)/);
  return optionIndex > 0 ? compact.slice(0, optionIndex) : compact;
};

const normalizeStrike = (value) => {
  const numeric = cleanText(value).match(/\d+(?:\.\d+)?/);
  if (!numeric) return '';
  return String(Number(numeric[0]));
};

const normalizeStrikePrice = (value) => {
  const strike = normalizeStrike(value);
  return strike === '0' ? '' : strike;
};

const normalizeYear = (value) => {
  const year = cleanText(value).match(/\d{2,4}/)?.[0] || '';
  if (!year) return '';
  return year.length === 2 ? year : year.slice(-2);
};

const normalizeMonth = (value) => {
  const text = cleanText(value).toUpperCase();
  if (!text) return '';
  const namedMonth = text.match(/[A-Z]{3}/)?.[0];
  if (namedMonth && MONTH_NUMBERS[namedMonth]) return namedMonth;
  const numericMonth = text.match(/\d{1,2}/)?.[0];
  if (!numericMonth) return '';
  return MONTH_NAMES[Number(numericMonth)] || '';
};

const normalizeDay = (value) => {
  const day = cleanText(value).match(/\d{1,2}/)?.[0] || '';
  return day ? day.padStart(2, '0') : '';
};

const parseExpiry = (signal, orderParams, contractMatch) => {
  const expiry = firstPresent(contractMatch.expiry, orderParams.expiry, orderParams.expiry_date, signal?.expiry);
  if (expiry) {
    const isoMatch = cleanText(expiry).match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (isoMatch) {
      return {
        day: isoMatch[3],
        month: MONTH_NAMES[Number(isoMatch[2])] || '',
        year: isoMatch[1].slice(-2),
      };
    }

    const compactMatch = cleanText(expiry).toUpperCase().match(/^(\d{1,2})([A-Z]{3})(\d{2,4})$/);
    if (compactMatch) {
      return {
        day: compactMatch[1].padStart(2, '0'),
        month: compactMatch[2],
        year: compactMatch[3].slice(-2),
      };
    }
  }

  return {
    day: normalizeDay(firstPresent(orderParams.day, signal.day)),
    month: normalizeMonth(firstPresent(orderParams.month, signal.month)),
    year: normalizeYear(firstPresent(orderParams.fullyear, orderParams.full_year, orderParams.year, signal.fullyear, signal.year)),
  };
};

export const getTradeSymbolDisplay = (signal) => {
  const orderParams = signal?.order_params && typeof signal.order_params === 'object' ? signal.order_params : {};
  const webhookSignal = signal?.webhook_signal && typeof signal.webhook_signal === 'object' ? signal.webhook_signal : {};
  const contractMatch = orderParams.contract_match && typeof orderParams.contract_match === 'object' ? orderParams.contract_match : {};

  const completeSymbol = [
    signal?.trading_symbol,
    orderParams.tradingsymbol,
    orderParams.trading_symbol,
    orderParams.trade_symbol,
    contractMatch.tradingsymbol,
    contractMatch.trading_symbol,
    contractMatch.symbol,
  ].find(isCompleteOptionSymbol);

  if (completeSymbol) {
    return cleanText(completeSymbol).toUpperCase();
  }

  const transactionType = cleanText(signal?.transaction_type).toUpperCase();
  const underlying = normalizeUnderlying(firstPresent(
    signal?.Index_Symbol,
    orderParams.underlying,
    orderParams.symbol,
    webhookSignal.underlying,
    signal?.trading_symbol,
  ));
  const strike = normalizeStrikePrice(firstPresent(
    orderParams.strike,
    orderParams.strike_price,
    orderParams.default_price,
    contractMatch.strike,
    webhookSignal.strike,
    webhookSignal.strike_price,
    webhookSignal.price,
    signal?.LivePrice,
  ));
  const optionType = normalizeOptionType(firstPresent(
    orderParams.option_type,
    orderParams.optionType,
    orderParams.Type,
    contractMatch.option_type,
    webhookSignal.option_type,
    webhookSignal.Type,
    transactionType.includes('CE') ? 'CE' : '',
    transactionType.includes('PE') ? 'PE' : '',
  ));
  const expiry = parseExpiry(signal, orderParams, contractMatch);
  const expiryText = expiry.day && expiry.month && expiry.year ? `${expiry.day}${expiry.month}${expiry.year}` : '';

  if (underlying && strike && optionType) {
    return [underlying, expiryText, strike, optionType].filter(Boolean).join('');
  }

  return cleanText(signal?.trading_symbol || signal?.Index_Symbol) || '-';
};
