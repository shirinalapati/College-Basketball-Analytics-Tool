/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        illini: {
          orange: '#FF5F05',
          blue: '#13294B',
          'blue-light': '#1a3a6b',
          'orange-dim': '#cc4c04',
        },
        surface: {
          DEFAULT: '#0f1729',
          card: '#162236',
          border: '#2a3f5f',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Oswald', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
