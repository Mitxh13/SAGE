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
        gemini: {
          950: '#0e0e10',
          900: '#131314', // Main Gemini canvas
          850: '#18191b',
          800: '#1e1f20', // Gemini sidebar / elevated surface
          750: '#232527',
          700: '#282a2c', // Input box & chips
          600: '#3c4043', // Borders
          500: '#5f6368', // Muted borders
          400: '#8e9196', // Secondary text
          300: '#c4c7c5', // Placeholder / secondary
          200: '#e3e3e3', // Main text
          100: '#f0f4f9', // Bright text
          blue: '#4a90e2',
          purple: '#9B72CF',
          sparkle: '#7a889b',
          amber: '#e5a93c',
          green: '#34A853',
        },
      },
      fontFamily: {
        sans: [
          'Google Sans',
          'Inter',
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'Roboto',
          'sans-serif',
        ],
      },
      boxShadow: {
        'glow-warm': '0 0 100px -20px rgba(234, 179, 8, 0.15)',
        'glow-blue': '0 0 100px -20px rgba(66, 133, 244, 0.18)',
        'pill': '0 4px 20px -2px rgba(0, 0, 0, 0.4)',
      },
    },
  },
  plugins: [],
}
