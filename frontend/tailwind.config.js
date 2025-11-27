/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // ============================================
        // SEMANTIC TOKENS - Use these in components
        // ============================================
        
        // Surfaces
        surface: {
          DEFAULT: 'var(--color-surface)',
          subtle: 'var(--color-surface-subtle)',
          muted: 'var(--color-surface-muted)',
        },
        bg: {
          page: 'var(--color-bg-page)',
        },
        
        // Text
        text: {
          main: 'var(--color-text-main)',
          secondary: 'var(--color-text-secondary)',
          muted: 'var(--color-text-muted)',
          disabled: 'var(--color-text-disabled)',
        },
        
        // Borders & Dividers
        border: {
          DEFAULT: 'var(--color-border)',
          subtle: 'var(--color-border-subtle)',
        },
        divider: 'var(--color-divider)',
        
        // Interactive elements
        accent: {
          DEFAULT: 'var(--color-accent)',
          hover: 'var(--color-accent-hover)',
          active: 'var(--color-accent-active)',
          soft: 'var(--color-accent-soft)',
          'soft-hover': 'var(--color-accent-soft-hover)',
        },
        
        // Badges & Tags
        badge: {
          bg: 'var(--color-badge-bg)',
          text: 'var(--color-badge-text)',
          border: 'var(--color-badge-border)',
        },
        
        // Filter pills
        filter: {
          'inactive-bg': 'var(--color-filter-inactive-bg)',
          'inactive-text': 'var(--color-filter-inactive-text)',
          'inactive-border': 'var(--color-filter-inactive-border)',
          'inactive-hover-bg': 'var(--color-filter-inactive-hover-bg)',
          'inactive-hover-border': 'var(--color-filter-inactive-hover-border)',
          'active-bg': 'var(--color-filter-active-bg)',
          'active-text': 'var(--color-filter-active-text)',
          'active-hover': 'var(--color-filter-active-hover)',
        },
        
        // Table
        table: {
          'header-bg': 'var(--color-table-header-bg)',
          'row-hover': 'var(--color-table-row-hover)',
          'row-stripe': 'var(--color-table-row-stripe)',
        },
        
        // Buttons
        button: {
          'ghost-bg': 'var(--color-button-ghost-bg)',
          'ghost-text': 'var(--color-button-ghost-text)',
          'ghost-border': 'var(--color-button-ghost-border)',
          'ghost-hover-bg': 'var(--color-button-ghost-hover-bg)',
        },
        
        // Status
        error: {
          DEFAULT: 'var(--color-error)',
          bg: 'var(--color-error-bg)',
        },
        success: {
          DEFAULT: 'var(--color-success)',
          bg: 'var(--color-success-bg)',
        },
        
        // ============================================
        // RAW PALETTE - For advanced customization
        // Use semantic tokens above in components
        // ============================================
        primary: {
          50: 'var(--color-primary-50)',
          100: 'var(--color-primary-100)',
          200: 'var(--color-primary-200)',
          300: 'var(--color-primary-300)',
          400: 'var(--color-primary-400)',
          500: 'var(--color-primary-500)',
          600: 'var(--color-primary-600)',
          700: 'var(--color-primary-700)',
          800: 'var(--color-primary-800)',
          900: 'var(--color-primary-900)',
        },
        accent: {
          50: 'var(--color-accent-50)',
          100: 'var(--color-accent-100)',
          200: 'var(--color-accent-200)',
          300: 'var(--color-accent-300)',
          400: 'var(--color-accent-400)',
          500: 'var(--color-accent-500)',
          600: 'var(--color-accent-600)',
          700: 'var(--color-accent-700)',
          800: 'var(--color-accent-800)',
          900: 'var(--color-accent-900)',
        },
        neutral: {
          50: 'var(--color-neutral-50)',
          100: 'var(--color-neutral-100)',
          200: 'var(--color-neutral-200)',
          300: 'var(--color-neutral-300)',
          400: 'var(--color-neutral-400)',
          500: 'var(--color-neutral-500)',
          600: 'var(--color-neutral-600)',
          700: 'var(--color-neutral-700)',
          800: 'var(--color-neutral-800)',
          900: 'var(--color-neutral-900)',
        },
      },
    },
  },
  plugins: [],
}


