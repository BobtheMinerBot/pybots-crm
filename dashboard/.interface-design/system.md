# ISLA Builders Dashboard — Design System

## Direction

**Personality:** Warmth & Utility
**Foundation:** Cool with warm accents (slate base, ocean/coral highlights)
**Depth:** Subtle shadows — cards have presence without competing with data

## The Feel

Like a well-organized jobsite office. Clean, functional, everything in its place. Glance and know exactly what's happening.

## Tokens

### Spacing
Base: 8px
Scale: 4, 8, 12, 16, 24, 32, 48, 64

### Colors
```css
/* Base */
--bg-base: #f8fafc;
--bg-surface: #ffffff;
--bg-elevated: #ffffff;
--bg-inset: #f1f5f9;

/* Text */
--text-primary: #0f172a;
--text-secondary: #475569;
--text-muted: #94a3b8;
--text-faint: #cbd5e1;

/* Borders */
--border-default: rgba(15, 23, 42, 0.08);
--border-subtle: rgba(15, 23, 42, 0.05);
--border-strong: rgba(15, 23, 42, 0.15);

/* Brand — Keys Inspired */
--accent-ocean: #0ea5e9;
--accent-ocean-soft: #e0f2fe;
--accent-coral: #f97316;
--accent-coral-soft: #fff7ed;
--accent-concrete: #64748b;
--accent-lime: #84cc16;
--accent-lime-soft: #ecfccb;

/* Semantic */
--success: #22c55e;
--success-soft: #dcfce7;
--warning: #f59e0b;
--warning-soft: #fef3c7;
--destructive: #ef4444;
--destructive-soft: #fee2e2;
```

### Shadows
```css
--shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.04);
--shadow-md: 0 2px 4px rgba(15, 23, 42, 0.04), 0 4px 8px rgba(15, 23, 42, 0.02);
--shadow-lg: 0 4px 8px rgba(15, 23, 42, 0.04), 0 8px 16px rgba(15, 23, 42, 0.03);
```

### Radius
```css
--radius-sm: 6px;
--radius-md: 8px;
--radius-lg: 12px;
--radius-xl: 16px;
```

### Typography
```css
--font-sans: 'Inter', system-ui, -apple-system, sans-serif;
--font-mono: 'SF Mono', 'Fira Code', monospace;

/* Scale */
--text-xs: 11px;
--text-sm: 13px;
--text-base: 14px;
--text-lg: 16px;
--text-xl: 20px;
--text-2xl: 24px;
--text-3xl: 32px;
```

## Patterns

### Card Default
- Background: var(--bg-surface)
- Border: 1px solid var(--border-default)
- Padding: 20px
- Radius: var(--radius-md)
- Shadow: var(--shadow-sm)

### Card Metric
- Same as default
- Number: var(--text-3xl), 600 weight, var(--text-primary)
- Label: var(--text-sm), 500 weight, var(--text-secondary)
- Trend: var(--text-xs), colored by direction

### Status Badge
- Padding: 4px 8px
- Radius: var(--radius-sm)
- Font: var(--text-xs), 500 weight
- Background: semantic soft color
- Text: semantic color

### Progress Bar
- Height: 8px
- Background: var(--bg-inset)
- Radius: 4px
- Fill: gradient or solid accent

### Button Primary
- Height: 36px
- Padding: 8px 16px
- Background: var(--accent-ocean)
- Color: white
- Radius: var(--radius-sm)
- Font: var(--text-sm), 500 weight

## Signature Element

**Project Flow Visualization** — Jobs shown as a horizontal journey from lead to payment. Geographic/timeline hybrid that shows where each project is in its lifecycle.

## Decisions

| Decision | Rationale | Date |
|----------|-----------|------|
| Warm utility | Craftsman's tool, not corporate dashboard | 2026-01-25 |
| Ocean/coral accents | Keys-inspired, not generic blue | 2026-01-25 |
| Subtle shadows | Cards need presence but data leads | 2026-01-25 |
| 8px base spacing | Comfortable density, not cramped | 2026-01-25 |
