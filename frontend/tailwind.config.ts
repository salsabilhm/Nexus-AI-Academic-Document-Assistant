import type { Config } from 'tailwindcss';

// Tailwind CSS v3 configuration.
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {},
  },
  plugins: [],
} satisfies Config;
