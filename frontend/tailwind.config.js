/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#FF9F1C',
          foreground: '#000000',
          hover: '#FFB23F',
        },
        background: '#050505',
        surface: '#121212',
        border: '#262626',
        'text-main': '#FFFFFF',
        'text-muted': '#A3A3A3',
        success: '#00C853',
        error: '#FF3D00',
        warning: '#FFD600',
        info: '#2962FF',
        card: {
          DEFAULT: '#121212',
          foreground: '#FFFFFF',
        },
        muted: {
          DEFAULT: '#262626',
          foreground: '#A3A3A3',
        },
      },
      fontFamily: {
        sans: ['Manrope', 'sans-serif'],
        heading: ['Chivo', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        sm: '2px',
        DEFAULT: '4px',
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
