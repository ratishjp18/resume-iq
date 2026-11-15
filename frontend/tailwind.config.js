/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: { 950: '#070b17', 900: '#0b1020', 800: '#111833', 700: '#1a2344' },
        brand: { purple: '#8b5cf6', cyan: '#22d3ee' },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['"Space Grotesk"', 'Inter', 'sans-serif'],
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(139,92,246,.35), 0 8px 40px -12px rgba(34,211,238,.35)',
      },
    },
  },
  plugins: [],
}
