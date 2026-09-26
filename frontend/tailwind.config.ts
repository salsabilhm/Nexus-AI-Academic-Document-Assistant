import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        nexus: {
          bg:       '#0d0014',
          surface:  '#130020',
          card:     '#1a0028',
          border:   '#2e1050',
          muted:    '#6b3fa0',
          text:     '#e8d5f5',
          'text-dim': '#a78bca',
          purple:   '#c084fc',
          'purple-bright': '#d8b4fe',
          'purple-deep':   '#7c3aed',
          accent:   '#e879f9',
        },
      },
      fontFamily: {
        display: ['Georgia', 'ui-serif', 'serif'],
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'sans-serif'],
      },
      animation: {
        'fade-up':    'fadeUp 0.5s ease both',
        'fade-in':    'fadeIn 0.4s ease both',
        'pulse-slow': 'pulse 3s ease-in-out infinite',
        'glow':       'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        fadeUp:  { from: { opacity: '0', transform: 'translateY(16px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        fadeIn:  { from: { opacity: '0' }, to: { opacity: '1' } },
        glow:    { from: { boxShadow: '0 0 10px rgba(192,132,252,0.2)' }, to: { boxShadow: '0 0 24px rgba(192,132,252,0.5)' } },
      },
      backgroundImage: {
        'nexus-gradient':    'linear-gradient(135deg, #1a0028 0%, #0d0014 100%)',
        'purple-glow':       'radial-gradient(ellipse at 50% 0%, rgba(124,58,237,0.25) 0%, transparent 65%)',
        'hero-glow':         'radial-gradient(ellipse at 70% 40%, rgba(192,132,252,0.15) 0%, transparent 60%)',
      },
    },
  },
  plugins: [],
} satisfies Config;
