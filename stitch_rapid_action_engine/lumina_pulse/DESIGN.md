---
name: Lumina Pulse
colors:
  surface: '#131319'
  surface-dim: '#131319'
  surface-bright: '#39383f'
  surface-container-lowest: '#0d0e13'
  surface-container-low: '#1b1b21'
  surface-container: '#1f1f25'
  surface-container-high: '#2a2930'
  surface-container-highest: '#34343b'
  on-surface: '#e4e1ea'
  on-surface-variant: '#bacac1'
  inverse-surface: '#e4e1ea'
  inverse-on-surface: '#303036'
  outline: '#85948c'
  outline-variant: '#3c4a43'
  surface-tint: '#2fe0aa'
  primary: '#44edb7'
  on-primary: '#003828'
  primary-container: '#00d09c'
  on-primary-container: '#00533c'
  inverse-primary: '#006c4f'
  secondary: '#c7c5d1'
  on-secondary: '#303039'
  secondary-container: '#464650'
  on-secondary-container: '#b6b4bf'
  tertiary: '#ffc8a3'
  on-tertiary: '#502500'
  tertiary-container: '#ffa15b'
  on-tertiary-container: '#733800'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#59fdc5'
  primary-fixed-dim: '#2fe0aa'
  on-primary-fixed: '#002116'
  on-primary-fixed-variant: '#00513b'
  secondary-fixed: '#e3e1ed'
  secondary-fixed-dim: '#c7c5d1'
  on-secondary-fixed: '#1b1b23'
  on-secondary-fixed-variant: '#464650'
  tertiary-fixed: '#ffdcc6'
  tertiary-fixed-dim: '#ffb785'
  on-tertiary-fixed: '#301400'
  on-tertiary-fixed-variant: '#713700'
  background: '#131319'
  on-background: '#e4e1ea'
  surface-variant: '#34343b'
  dark-bg: '#1E1E24'
  dark-highlight: '#2A2A33'
  dark-shadow: '#121216'
  light-bg: '#E0E5EC'
  light-highlight: '#FFFFFF'
  light-shadow: '#A3B1C6'
  accent-emerald: '#00D09C'
typography:
  display-lg:
    fontFamily: Outfit
    fontSize: 64px
    fontWeight: '800'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Outfit
    fontSize: 40px
    fontWeight: '800'
    lineHeight: '1.2'
  headline-lg:
    fontFamily: Outfit
    fontSize: 32px
    fontWeight: '700'
    lineHeight: '1.3'
  headline-md:
    fontFamily: Outfit
    fontSize: 24px
    fontWeight: '700'
    lineHeight: '1.4'
  body-lg:
    fontFamily: Outfit
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Outfit
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  label-md:
    fontFamily: Outfit
    fontSize: 14px
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.05em
  quote-text:
    fontFamily: literata
    fontSize: 20px
    fontWeight: '400'
    lineHeight: '1.5'
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  gutter: 24px
  margin-mobile: 20px
  margin-desktop: 64px
  max-width: 1440px
---

## Brand & Style
The design system is centered on **High-Definition Neumorphism**, a style that emphasizes tactile, physical interactions where UI elements appear to be molded from the same material as the background. The brand persona is sophisticated, analytical, and futuristic—evoking the feeling of a high-end physical control console.

The aesthetic relies on precise light modeling rather than lines. By using dual-source shadows (light highlights and dark shadows), we create a "Soft UI" that feels calm and organic. This is ideal for data-heavy dashboards like the Weekly Product Pulse, as it reduces visual noise and creates a cohesive, singular surface. The emotional response should be one of "effortless intelligence" and premium craftsmanship.

## Colors
This design system utilizes a dual-mode color strategy optimized for Neumorphic depth. 

### Light Mode
The background (`#E0E5EC`) acts as the "mid-tone" surface. Depth is created by a pure white highlight (`#FFFFFF`) on the top-left and a muted blue-gray shadow (`#A3B1C6`) on the bottom-right. 

### Dark Mode
The background (`#1E1E24`) provides a matte charcoal canvas. The highlights are subtle (`#2A2A33`) and the shadows are deep (`#121216`), creating a high-end, low-glare aesthetic.

### Accents
The **Emerald Green** (`#00D09C`) is used sparingly for high-value actions, status indicators, and data visualization. It should appear as if it is glowing from within the surface or applied as a vibrant "ink" on top of the molded shapes.

## Typography
The typography system relies on **Outfit**, a geometric sans-serif that complements the soft curves of Neumorphism. 

- **Headers:** Use heavy weights (700-800) to create a strong visual anchor against the soft-edged UI.
- **Body:** Set at weight 400 for maximum legibility.
- **Quotes:** To distinguish the "Voice of the Customer," use a serif font (**Literata**) in italics. This provides a human, editorial contrast to the technical geometric UI.
- **Hierarchy:** Maintain high contrast between display sizes and body text to ensure the dashboard remains scannable even with low-contrast Neumorphic borders.

## Layout & Spacing
The layout follows a **Fluid Grid** model with a maximum container width of 1440px. 

- **Rhythm:** Use an 8px base unit. Neumorphic elements require significant breathing room (padding) to allow their soft shadows to resolve without overlapping neighboring elements.
- **Grid:** A 12-column system is used for desktop. For report cards, use 4-column spans (3 cards per row). 
- **Responsive Behavior:** On mobile, margins reduce to 20px and the 12-column grid collapses to a single-column stack. Neumorphic "extrusion" (distance) should be slightly reduced on smaller screens to prevent elements from feeling overly bulky.

## Elevation & Depth
Depth is the core mechanic of this system. Rather than standard drop shadows, use **Dual Shadows**:

1.  **Extruded (Raised):** Used for primary cards and buttons.
    - *Light Side:* Top-left shadow (Light Mode: White / Dark Mode: `#2A2A33`).
    - *Dark Side:* Bottom-right shadow (Light Mode: `#A3B1C6` / Dark Mode: `#121216`).
2.  **Depressed (Inset):** Used for input fields and active button states.
    - Apply `box-shadow: inset` using the same dual-tone logic.
3.  **Softness:** Keep blur radiuses high (typically 1.5x to 2x the offset distance) to ensure the 3D effect remains "soft" and integrated. Avoid any solid borders (1px solid) unless they are extremely low opacity (e.g., 5% alpha) to define edges in complex overlaps.

## Shapes
The shape language is strictly **Rounded**. Sharp corners break the Neumorphic illusion of a continuous molded surface.

- **Cards & Large containers:** Use `rounded-lg` (1rem) or `rounded-xl` (1.5rem) to ensure a friendly, approachable feel.
- **Buttons & Chips:** Use a high degree of roundedness (up to pill-shaped) to invite interaction.
- **Consistency:** Every interactive element must share the same corner radius logic to maintain the "molded plastic" or "soft silicone" look.

## Components

### Buttons
- **Primary:** Extruded Neumorphic base. On hover, the shadow intensity increases. On click, the state switches to "depressed" (inset shadow) and the Emerald Green text/icon glows slightly.
- **Action Button ("Generate"):** A large, high-radius button with a subtle Emerald Green outer glow (`0 0 20px rgba(0, 208, 156, 0.3)`).

### Cards (Report View)
- Use the **Extruded** style. 
- For "AI-Generated" recommendations, add a thin, 1px inner glow using the primary Emerald Green at 20% opacity to signify the "intelligence" layer.
- **Quote Cards:** Feature a masonry layout with Literata italic text and a 5-star rating component at the top, colored in Emerald Green.

### Form Inputs
- **Text Fields:** Always **Depressed** (inset shadows). This creates a physical "well" for the user to type into.
- **Toggle (Day/Dark):** A pill-shaped track (depressed) with a circular thumb (extruded). The transition should be a smooth 300ms ease-in-out.

### Loading States
- The spinner should be a Neumorphic ring that "rotates" its light source, making it appear as if a physical bump is moving around a circular track. Combine this with pulsing Emerald Green text.