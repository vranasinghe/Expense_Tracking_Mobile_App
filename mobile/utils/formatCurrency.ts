import type { Currency } from '../store/types';

export function formatCurrency(amount: number, currency: Currency = '$'): string {
  const absAmount = Math.abs(amount);
  let formatted: string;

  if (absAmount >= 1000000) {
    formatted = `${(absAmount / 1000000).toFixed(2)}M`;
  } else if (absAmount >= 1000) {
    formatted = absAmount.toLocaleString('en-US', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    });
  } else {
    formatted = absAmount.toString();
  }

  return `${currency}${formatted}`;
}

export function formatCompact(amount: number, currency: Currency = '$'): string {
  const abs = Math.abs(amount);
  if (abs >= 1000000) return `${currency}${(abs / 1000000).toFixed(1)}M`;
  if (abs >= 1000) return `${currency}${(abs / 1000).toFixed(1)}K`;
  return `${currency}${abs}`;
}
