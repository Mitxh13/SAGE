/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        sage: {
          50: '#F5F8F6',
          100: '#E8EFEA',
          200: '#D0DFD6',
          300: '#ADC5B8',
          400: '#82A694',
          500: '#5C8773',
          600: '#466B5A',
          700: '#385547', // Primary dignified sage green
          800: '#2B4137',
          900: '#1E2E27',
          950: '#131D18',
        },
        cream: {
          50: '#FDFBF7',
          100: '#FAF6F0', // Soft warm cream canvas
          150: '#F4EFE7',
          200: '#EFE8DE', // Elevated surfaces / cards
          300: '#E3DACD', // Clean border dividers
          400: '#CFBFAB',
          500: '#B5A28D',
        },
        charcoal: {
          900: '#18201D', // High contrast typography
          800: '#26332E',
          700: '#394A43',
          600: '#4F635A',
          500: '#677D73', // Secondary labels
          400: '#8B9F96', // Muted timestamps / borders
          300: '#B8C6C0',
        },
      },
      fontFamily: {
        sans: [
          'Inter',
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'Roboto',
          'sans-serif',
        ],
      },
      boxShadow: {
        'sage-soft': '0 2px 14px -2px rgba(56, 85, 71, 0.08)',
        'pill': '0 4px 28px -4px rgba(30, 46, 39, 0.12), 0 2px 6px -1px rgba(0, 0, 0, 0.04)',
        'pill-hover': '0 8px 32px -4px rgba(30, 46, 39, 0.16), 0 2px 8px -1px rgba(0, 0, 0, 0.06)',
        'ambient': '0 20px 80px -20px rgba(92, 135, 115, 0.15)',
      },
    },
  },
  plugins: [],
}
