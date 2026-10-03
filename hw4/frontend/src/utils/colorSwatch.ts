// Maps the catalogue's free-text color names to a real swatch color/gradient
// for product cards. Unmapped names fall back to a neutral gray dot rather
// than guessing — the swatch is a visual aid for real `colors` data, never
// invented.
const COLOR_MAP: Record<string, string> = {
  black: '#1a1a1a',
  white: '#ffffff',
  navy: '#0f2a52',
  'navy blue': '#0f2a52',
  blue: '#2b5fa8',
  'light blue': '#a9c8e8',
  'royal blue': '#1d4fb0',
  gray: '#9a9a9a',
  'light gray': '#c7c7c7',
  'charcoal gray': '#4b4b4d',
  'dark heather gray': '#5c5c5e',
  'heather gray': '#8a8a8c',
  'heather charcoal gray': '#4b4b4d',
  'dark heather charcoal': '#3a3a3c',
  red: '#b3261e',
  green: '#2f6b4f',
  gold: '#c9a44c',
  yellow: '#e6c34a',
  cream: '#f2e8d5',
  ivory: '#f5f0e6',
  'dusty coral': '#e0917c',
  multicolor: 'linear-gradient(135deg, #b3261e 0%, #c9a44c 50%, #2b5fa8 100%)',
}

export function swatchStyle(color: string): string {
  return COLOR_MAP[color.toLowerCase().trim()] ?? '#b7bfca'
}
