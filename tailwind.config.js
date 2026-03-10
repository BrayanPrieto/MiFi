/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'mifi-navy': 'var(--mifi-navy)',
        'mifi-navy-light': 'var(--mifi-navy-light)',
        'mifi-cyan': 'var(--mifi-cyan)',
        'mifi-green': 'var(--mifi-green)',
        'mifi-red': 'var(--mifi-red)',
        'mifi-bg': 'var(--mifi-bg)',

        primary: {
          50: '#f1f8fc',
          100: '#e1f0f9',
          200: '#c2e0f2',
          300: '#8fcae7',
          400: '#54add9',
          500: '#2b91c1',
          600: '#1f75a3',
          700: '#1a5e84',
          800: '#174f6e',
          900: '#17425c',
          950: 'var(--mifi-navy)',
        }
      }
    },
  },
  plugins: [require('tailwindcss-primeui')],
}
