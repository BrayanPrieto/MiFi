/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        display: ['Space Grotesk', 'Plus Jakarta Sans', 'sans-serif'],
      },
      boxShadow: {
        soft: '0 1px 2px rgba(15,23,42,0.03), 0 8px 24px rgba(15,23,42,0.05), inset 0 1px 1px rgba(255,255,255,0.65)',
        'soft-lg': '0 2px 4px rgba(15,23,42,0.04), 0 18px 48px rgba(15,23,42,0.09), inset 0 1px 1px rgba(255,255,255,0.7)',
      },
      borderRadius: {
        squircle: '24px',
      },
      transitionTimingFunction: {
        soft: 'cubic-bezier(0.32, 0.72, 0, 1)',
      },
      colors: {
        'mifi-navy': 'var(--mifi-navy)',
        'mifi-navy-light': 'var(--mifi-navy-light)',
        'mifi-cyan': 'var(--mifi-cyan)',
        'mifi-green': 'var(--mifi-green)',
        'mifi-red': 'var(--mifi-red)',
        'mifi-amber': 'var(--mifi-amber)',
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
