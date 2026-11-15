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
      keyframes: {
        float: { '0%,100%': { transform: 'translate3d(0,0,0)' }, '50%': { transform: 'translate3d(0,-22px,0)' } },
        drift: { '0%,100%': { transform: 'translate3d(0,0,0) scale(1)' }, '50%': { transform: 'translate3d(40px,30px,0) scale(1.12)' } },
        gradientx: { '0%,100%': { backgroundPosition: '0% 50%' }, '50%': { backgroundPosition: '100% 50%' } },
        marquee: { from: { transform: 'translateX(0)' }, to: { transform: 'translateX(-50%)' } },
        shine: { '0%': { transform: 'translateX(-120%) skewX(-20deg)' }, '60%,100%': { transform: 'translateX(220%) skewX(-20deg)' } },
      },
      animation: {
        float: 'float 6s ease-in-out infinite',
        'float-slow': 'float 9s ease-in-out infinite',
        drift: 'drift 18s ease-in-out infinite',
        'drift-rev': 'drift 24s ease-in-out infinite reverse',
        gradientx: 'gradientx 6s ease infinite',
        marquee: 'marquee 30s linear infinite',
        shine: 'shine 3.5s ease-in-out infinite',
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(139,92,246,.35), 0 8px 40px -12px rgba(34,211,238,.35)',
      },
    },
  },
  plugins: [],
}
