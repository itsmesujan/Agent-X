import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#030712', // Slate 950
        foreground: '#f8fafc',
        primary: {
          DEFAULT: '#06b6d4', // Cyan 500
          dark: '#0891b2',
          light: '#22d3ee',
        },
        surface: {
          DEFAULT: '#0f172a', // Slate 900
          border: '#1e293b',  // Slate 800
          hover: '#1e293b',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'monospace'],
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
};

export default config;
