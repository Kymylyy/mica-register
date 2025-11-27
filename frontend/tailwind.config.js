/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        /* ============================================
           SEMANTIC TOKENS - Use these in components
           Supports alpha via / <alpha-value>
           ============================================ */
        
        /* Semantic backgrounds */
        surface:        'rgb(var(--surface) / <alpha-value>)',
        surfaceAlt:     'rgb(var(--surface-alt) / <alpha-value>)',
        surfaceElev:    'rgb(var(--surface-elev) / <alpha-value>)',

        /* Borders */
        borderSubtle:   'rgb(var(--border-subtle) / <alpha-value>)',
        borderStrong:   'rgb(var(--border-strong) / <alpha-value>)',

        /* Text */
        textMain:       'rgb(var(--text-main) / <alpha-value>)',
        textMuted:      'rgb(var(--text-muted) / <alpha-value>)',
        textSoft:       'rgb(var(--text-soft) / <alpha-value>)',

        /* Accent */
        accent:         'rgb(var(--accent) / <alpha-value>)',
        accentBg:       'rgb(var(--accent-bg) / <alpha-value>)',
        accentBorder:   'rgb(var(--accent-border) / <alpha-value>)',

        /* Status */
        success:        'rgb(var(--success) / <alpha-value>)',
        danger:         'rgb(var(--danger) / <alpha-value>)',
      },
    },
  },
  plugins: [],
}


