# SmartSuite UI Replication Spec

## Overview
This document outlines the exact design specifications to replicate SmartSuite's UI in the ISLA CRM.

---

## 1. COLOR PALETTE

### Primary Colors
```css
--primary: #4573D2;           /* SmartSuite Blue */
--primary-hover: #3B63B8;
--primary-light: #E8F0FE;
```

### Header Colors (Dark Blue)
```css
--header-bg: #4573D2;         /* SmartSuite Blue Header */
--header-text: #FFFFFF;
--header-hover: rgba(255,255,255,0.1);
```

### Sidebar Colors (Light Theme - like SmartSuite!)
```css
--sidebar-bg: #FFFFFF;        /* White background */
--sidebar-hover: #F0F4FF;     /* Light blue hover */
--sidebar-active: #E8F0FE;    /* Lighter blue active */
--sidebar-active-border: #4573D2; /* Blue left border */
--sidebar-text: #374151;      /* Dark gray text */
--sidebar-text-active: #4573D2; /* Blue text when active */
--sidebar-border: #E5E7EB;    /* Light gray border */
```

### Background Colors
```css
--bg-primary: #FFFFFF;
--bg-secondary: #F6F7F9;      /* Light gray page background */
--bg-tertiary: #ECEEF1;
```

### Status/Stage Colors (Soft Pastels)
```css
--status-blue: #4573D2;       /* New Lead */
--status-blue-bg: #E8F0FE;
--status-orange: #F5A623;     /* Inspection Scheduled */
--status-orange-bg: #FEF4E6;
--status-purple: #7C3AED;     /* Estimating */
--status-purple-bg: #F3E8FF;
--status-green: #22C55E;      /* Proposal Sent */
--status-green-bg: #DCFCE7;
--status-pink: #EC4899;       /* Follow Up */
--status-pink-bg: #FCE7F3;
--status-sky: #0EA5E9;        /* Nurturing */
--status-sky-bg: #E0F2FE;
--status-red: #EF4444;        /* Lost */
--status-red-bg: #FEE2E2;
```

### Gray Scale
```css
--gray-50: #F9FAFB;
--gray-100: #F3F4F6;
--gray-200: #E5E7EB;
--gray-300: #D1D5DB;
--gray-400: #9CA3AF;
--gray-500: #6B7280;
--gray-600: #4B5563;
--gray-700: #374151;
--gray-800: #1F2937;
--gray-900: #111827;
```

---

## 2. SIDEBAR DESIGN

### Structure
```
┌─────────────────────────────────┐
│  [Logo] ISLA CRM      [≡]      │  <- Header with collapse toggle
├─────────────────────────────────┤
│                                 │
│  🏠 Dashboard                   │  <- Nav items with icons
│  👥 Leads                       │
│  📊 Reports                     │
│  ⚙️ Settings                    │
│                                 │
├─────────────────────────────────┤
│                                 │
│  [Avatar] Admin                 │  <- User section at bottom
│  Logout                         │
│                                 │
└─────────────────────────────────┘
```

### Specifications
- **Width:** 240px expanded, 64px collapsed
- **Background:** #1E1F21 (dark charcoal)
- **Logo area:** 60px height, centered
- **Nav items:**
  - Height: 40px
  - Padding: 12px 16px
  - Border-radius: 8px
  - Left margin: 8px, Right margin: 8px
  - Icon size: 20px
  - Gap between icon and text: 12px
- **Active state:** Background #3D3E40, white text
- **Hover state:** Background #2D2E30
- **Transition:** 200ms ease

### Collapsed State
- Only icons visible
- Tooltip on hover showing label
- Width: 64px

---

## 3. TOP HEADER / TAB BAR

### For Views (when inside Leads)
```
┌──────────────────────────────────────────────────────────────┐
│  Grid View ▼  │  [🔍 Search]  [Filter ▼]  [Sort ▼]  [+ Add]  │
└──────────────────────────────────────────────────────────────┘
```

### Specifications
- **Height:** 52px
- **Background:** White
- **Border-bottom:** 1px solid #E5E7EB
- **View selector dropdown:** Left aligned
- **Actions:** Right aligned
- **Padding:** 0 24px

---

## 4. VIEW TYPES

### Grid View (Table)
- **Header row:**
  - Background: #F9FAFB
  - Font-weight: 500
  - Font-size: 12px
  - Text-transform: uppercase
  - Letter-spacing: 0.05em
  - Color: #6B7280
  - Height: 40px

- **Data rows:**
  - Height: 48px
  - Border-bottom: 1px solid #F3F4F6
  - Hover background: #F9FAFB
  
- **Grouped sections:**
  - Group header: 36px height
  - Left border: 4px solid [stage-color]
  - Background: #F9FAFB
  - Collapsible with chevron

### Kanban View (Future)
- Columns for each stage
- Cards with shadows
- Drag and drop

---

## 5. COMPONENTS

### Buttons
```css
/* Primary */
.btn-primary {
  background: #4573D2;
  color: white;
  border-radius: 6px;
  padding: 8px 16px;
  font-weight: 500;
}

/* Secondary */
.btn-secondary {
  background: white;
  border: 1px solid #E5E7EB;
  border-radius: 6px;
  padding: 8px 16px;
}
```

### Badges/Tags
```css
.badge {
  padding: 4px 10px;
  border-radius: 12px;  /* Pill shape */
  font-size: 12px;
  font-weight: 500;
}
```

### Cards
```css
.card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  border: 1px solid #E5E7EB;
}
```

### Inputs
```css
input, select {
  border: 1px solid #E5E7EB;
  border-radius: 6px;
  padding: 8px 12px;
  transition: border-color 200ms;
}
input:focus {
  border-color: #4573D2;
  box-shadow: 0 0 0 3px rgba(69, 115, 210, 0.1);
}
```

---

## 6. TYPOGRAPHY

```css
--font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;

/* Headings */
h1 { font-size: 24px; font-weight: 600; }
h2 { font-size: 20px; font-weight: 600; }
h3 { font-size: 16px; font-weight: 600; }

/* Body */
body { font-size: 14px; line-height: 1.5; }

/* Small */
.text-sm { font-size: 12px; }
.text-xs { font-size: 11px; }
```

---

## 7. SPACING SYSTEM

```css
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 20px;
--space-6: 24px;
--space-8: 32px;
--space-10: 40px;
--space-12: 48px;
```

---

## 8. SHADOWS

```css
--shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
--shadow-md: 0 4px 6px rgba(0,0,0,0.07);
--shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
```

---

## 9. BORDER RADIUS

```css
--radius-sm: 4px;
--radius-md: 6px;
--radius-lg: 8px;
--radius-xl: 12px;
--radius-full: 9999px;  /* Pills */
```

---

## 10. IMPLEMENTATION PRIORITY

### Phase 1: Sidebar + Color Palette (NOW)
1. Replace top navbar with left sidebar
2. Implement dark sidebar theme
3. Update color palette to SmartSuite colors
4. Add collapse functionality

### Phase 2: Views & Components
1. Refine Grid View table styling
2. Add view selector dropdown
3. Update buttons and inputs

### Phase 3: Kanban + Advanced
1. Implement Kanban board view
2. Add drag-and-drop
3. Dashboard widgets

---

## File Changes Required

1. `templates/base.html` - New sidebar layout
2. `static/css/main.css` - Complete color/component overhaul
3. `templates/leads.html` - Table styling updates
4. `static/js/main.js` - Sidebar toggle functionality
