/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cream: {
          50: '#FAF8F4',
          100: '#F5F1E9', // Main whole-page canvas
          200: '#EAE4D8', // Sidebar & surface
          300: '#DDD5C7', // Borders
          400: '#C9BFAD',
          500: '#B0A28E',
        },
        sage: {
          50: '#F2F7F4',
          100: '#EAF2ED', // Softest sage component tint
          200: '#DCE8E0', // Component cards, input pills, list items
          300: '#B8D1C2', // Component borders
          400: '#8EB39D', // Hover borders
          500: '#649377',
          600: '#4B755E',
          700: '#385A48', // Primary buttons & key highlights
          800: '#294335', // Dark sage text
          900: '#1C2E24', // Deepest high-contrast sage text
          950: '#121E18',
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
        'sage-sm': '0 1px 3px 0 rgba(28, 46, 36, 0.06), 0 1px 2px -1px rgba(28, 46, 36, 0.04)',
        'sage-md': '0 4px 16px -2px rgba(28, 46, 36, 0.08), 0 2px 4px -2px rgba(28, 46, 36, 0.04)',
        'sage-lg': '0 10px 30px -4px rgba(28, 46, 36, 0.12), 0 4px 6px -2px rgba(28, 46, 36, 0.04)',
        'pill': '0 4px 20px -2px rgba(28, 46, 36, 0.10), 0 2px 6px -1px rgba(28, 46, 36, 0.05)',
      },
    },
  },
  plugins: [],
}
