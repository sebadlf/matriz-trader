import { describe, expect, it } from 'vitest';
import { ApiError } from '../../api/http';
import { describeApiError, EMPTY, formatNumber, formatText } from './format';

describe('formatNumber (EB-3)', () => {
  it.each([null, undefined, Number.NaN])('%s → —', (value) => {
    expect(formatNumber(value)).toBe(EMPTY);
  });

  it('formatea con es-AR y hasta 6 decimales', () => {
    expect(formatNumber(0)).toBe('0');
    expect(formatNumber(123.5)).toBe('123,5');
    expect(formatNumber(1.1234567)).toBe('1,123457');
  });
});

describe('formatText (EB-3)', () => {
  it.each([null, undefined, ''])('%s → —', (value) => {
    expect(formatText(value)).toBe(EMPTY);
  });

  it('devuelve el texto tal cual', () => {
    expect(formatText('GGAL')).toBe('GGAL');
  });
});

describe('describeApiError', () => {
  it('usa detail string', () => {
    expect(describeApiError(new ApiError(502, { detail: 'Matriz: caído' }))).toBe('Matriz: caído');
  });

  it('une los msg de un detail 422', () => {
    const body = { detail: [{ msg: 'campo requerido' }, { msg: 'debe ser > 0' }] };
    expect(describeApiError(new ApiError(422, body))).toBe('campo requerido; debe ser > 0');
  });

  it('sin detail devuelve HTTP <status>', () => {
    expect(describeApiError(new ApiError(500, null))).toBe('HTTP 500');
    expect(describeApiError(new ApiError(503, { other: 1 }))).toBe('HTTP 503');
  });

  it('otro error → el backend no responde', () => {
    expect(describeApiError(new TypeError('Failed to fetch'))).toBe('El backend no responde');
    expect(describeApiError(undefined)).toBe('El backend no responde');
  });
});
