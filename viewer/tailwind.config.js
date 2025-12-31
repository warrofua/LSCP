/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ['JetBrains Mono', 'Consolas', 'Monaco', 'monospace'],
      },
      colors: {
        cyber: {
          bg: '#050505',
          panel: '#0a0a0a',
          border: '#1a1a1a',
          text: '#e0e0e0',
          dim: '#808080',
          blue: '#00d4ff',
          red: '#ff006e',
          magenta: '#d946ef',
        }
      },
      backdropBlur: {
        xs: '2px',
      }
    },
  },
  plugins: [],
}
