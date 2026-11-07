/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        sage: {
          50: '#f4f7f5',
          100: '#e5ece7',
          200: '#cbd9cf',
          300: '#a5beb0',
          400: '#7a9f8c',
          500: '#5a826e',
          600: '#456756',
          700: '#385346',
          800: '#2f4339',
          900: '#283830',
          950: '#141f1a',
        },
      },
    },
  },
  plugins: [],
}
