/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'deep-twilight': '#07094A',
        'deep-twilight-2': '#07094A', // Same as base
        'deep-twilight-3': '#07095C',
        'lavender': '#DCDCEF',
        'white-custom': '#FEFEFE',
      }
    },
  },
  plugins: [],
}
