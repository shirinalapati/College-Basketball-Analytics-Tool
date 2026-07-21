/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        illini: {
          orange: '#003087',
          blue: '#001A57',
          'blue-light': '#0a2d6b',
          'orange-dim': '#002060',
        },
        surface: {
          DEFAULT: '#0e0f11',
          card: '#181a1f',
          border: '#2f3339',
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
