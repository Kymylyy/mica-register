# Color Palette System

## Overview

The project uses a centralized color system based on CSS variables. All colors are defined in `src/index.css` and mapped to Tailwind classes in `tailwind.config.js`.

## How to Change Colors

### Quick Change - Edit CSS Variables

To change the entire color scheme, simply edit the CSS variables in `src/index.css`:

```css
:root {
  --color-primary-500: #3b82f6;  /* Change this to your primary color */
  --color-primary-600: #2563eb;  /* Darker shade */
  --color-primary-700: #1d4ed8;  /* Even darker */
  /* ... etc */
}
```

### Available Color Scales

Each color has a full scale from 50 (lightest) to 900 (darkest):
- `primary` - Main brand/accent color
- `secondary` - Alternative accent
- `sky` - Used for service badges and accents
- `slate` - Neutral grays for UI elements
- `gray` - Base grays
- `red` - Error/destructive actions
- `green` - Success states

## Example Color Palettes

### Palette 1: Current (Blue/Sky)
```css
--color-primary-500: #3b82f6;  /* Blue */
--color-primary-600: #2563eb;
--color-primary-700: #1d4ed8;
--color-sky-50: #f0f9ff;
--color-sky-600: #0284c7;
--color-sky-700: #0369a1;
```

### Palette 2: Purple/Indigo
```css
--color-primary-500: #8b5cf6;  /* Purple */
--color-primary-600: #7c3aed;
--color-primary-700: #6d28d9;
--color-sky-50: #eef2ff;
--color-sky-600: #4f46e5;
--color-sky-700: #4338ca;
```

### Palette 3: Green/Emerald
```css
--color-primary-500: #10b981;  /* Green */
--color-primary-600: #059669;
--color-primary-700: #047857;
--color-sky-50: #ecfdf5;
--color-sky-600: #059669;
--color-sky-700: #047857;
```

### Palette 4: Orange/Amber
```css
--color-primary-500: #f59e0b;  /* Orange */
--color-primary-600: #d97706;
--color-primary-700: #b45309;
--color-sky-50: #fffbeb;
--color-sky-600: #d97706;
--color-sky-700: #b45309;
```

### Palette 5: Teal/Cyan
```css
--color-primary-500: #14b8a6;  /* Teal */
--color-primary-600: #0d9488;
--color-primary-700: #0f766e;
--color-sky-50: #f0fdfa;
--color-sky-600: #0d9488;
--color-sky-700: #0f766e;
```

## Usage in Components

### Old Way (Direct Tailwind classes)
```jsx
<div className="bg-blue-50 text-blue-700 border-blue-200">
```

### New Way (Using CSS variables via Tailwind)
```jsx
<div className="bg-primary-50 text-primary-700 border-primary-200">
```

Or using the mapped colors:
```jsx
<div className="bg-sky-50 text-sky-700 border-sky-200">
```

## Migration Status

Currently, the codebase uses a mix of:
- Direct Tailwind classes (e.g., `bg-blue-50`, `text-slate-600`)
- CSS variables (e.g., `focus:ring-primary`)

The CSS variables system is ready. Components can be gradually migrated to use the new system for easier color customization.

## Testing Different Palettes

1. Copy one of the example palettes above
2. Replace the corresponding variables in `src/index.css`
3. Save and see the changes instantly (with hot reload)

All colors will update automatically because they're all mapped through CSS variables!

