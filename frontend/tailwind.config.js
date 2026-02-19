/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Beautiful Royal Blue Theme
        blue: {
          50: '#EFF6FF',
          100: '#DBEAFE',
          200: '#BFDBFE',
          300: '#93C5FD',
          400: '#60A5FA',
          500: '#3B82F6', // Primary electric blue
          600: '#2563EB',
          700: '#1D4ED8',
          800: '#1E40AF',
          900: '#1E3A8A',
        },
        charcoal: {
          50: '#F5F5F5',
          100: '#E8E8E8',
          200: '#D1D1D1',
          300: '#B0B0B0',
          400: '#888888',
          500: '#666666',
          600: '#4D4D4D',
          700: '#333333',
          800: '#1A1A1A', // Primary text
          900: '#0D0D0D',
        },
        dark: {
          // Rich, deep backgrounds with subtle blue undertones
          bg: '#0f1419',           // Deep blue-black
          surface: '#1a1f2e',      // Elevated surface
          card: '#232a3b',         // Cards and modals
          border: '#2d3748',       // Subtle borders
          hover: '#2a3441',        // Hover state
          active: '#323d4f',       // Active/pressed state
          elevated: '#283040',     // Floating elements
          muted: '#64748b',        // Muted text
        }
      },
      fontFamily: {
        sans: ['Inter', 'SF Pro Display', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      boxShadow: {
        'blue': '0 0 0 3px rgba(59, 130, 246, 0.35)',
        'blue-lg': '0 0 25px rgba(59, 130, 246, 0.25)',
        'blue-glow': '0 0 30px rgba(59, 130, 246, 0.4), 0 0 60px rgba(59, 130, 246, 0.2)',
        'soft': '0 2px 8px rgba(0, 0, 0, 0.08)',
        'soft-lg': '0 4px 20px rgba(0, 0, 0, 0.1)',
        // Dark mode specific shadows
        'dark-sm': '0 1px 2px rgba(0, 0, 0, 0.4)',
        'dark-md': '0 4px 6px rgba(0, 0, 0, 0.5)',
        'dark-lg': '0 10px 25px rgba(0, 0, 0, 0.6)',
        'dark-glow': '0 0 20px rgba(59, 130, 246, 0.15)',
        'dark-inner': 'inset 0 1px 0 rgba(255, 255, 255, 0.05)',
        'dark-border': '0 0 0 1px rgba(59, 130, 246, 0.1)',
      },
      borderRadius: {
        'xl': '12px',
        '2xl': '16px',
        '3xl': '24px',
      },
      animation: {
        'pulse-blue': 'pulse-blue 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.2s ease-out',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'shimmer': 'shimmer 2s linear infinite',
      },
      keyframes: {
        'pulse-blue': {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(59, 130, 246, 0.5)' },
          '50%': { boxShadow: '0 0 0 10px rgba(59, 130, 246, 0)' },
        },
        'glow': {
          '0%': { boxShadow: '0 0 5px rgba(59, 130, 246, 0.3)' },
          '100%': { boxShadow: '0 0 20px rgba(59, 130, 246, 0.6), 0 0 40px rgba(59, 130, 246, 0.3)' },
        },
        'shimmer': {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideDown: {
          '0%': { opacity: '0', transform: 'translateY(-10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
