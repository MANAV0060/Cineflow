---
name: Cinematic Luxe
colors:
  surface: '#121318'
  surface-dim: '#121318'
  surface-bright: '#38393f'
  surface-container-lowest: '#0d0e13'
  surface-container-low: '#1a1b21'
  surface-container: '#1e1f25'
  surface-container-high: '#292a2f'
  surface-container-highest: '#34343a'
  on-surface: '#e3e1e9'
  on-surface-variant: '#e9bcb6'
  inverse-surface: '#e3e1e9'
  inverse-on-surface: '#2f3036'
  outline: '#af8782'
  outline-variant: '#5e3f3b'
  surface-tint: '#ffb4aa'
  primary: '#ffb4aa'
  on-primary: '#690003'
  primary-container: '#e50914'
  on-primary-container: '#fff7f6'
  inverse-primary: '#c0000c'
  secondary: '#ffb95f'
  on-secondary: '#472a00'
  secondary-container: '#ee9800'
  on-secondary-container: '#5b3800'
  tertiary: '#00dbe9'
  on-tertiary: '#00363a'
  tertiary-container: '#007f87'
  on-tertiary-container: '#e8fdff'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffdad5'
  primary-fixed-dim: '#ffb4aa'
  on-primary-fixed: '#410001'
  on-primary-fixed-variant: '#930007'
  secondary-fixed: '#ffddb8'
  secondary-fixed-dim: '#ffb95f'
  on-secondary-fixed: '#2a1700'
  on-secondary-fixed-variant: '#653e00'
  tertiary-fixed: '#7df4ff'
  tertiary-fixed-dim: '#00dbe9'
  on-tertiary-fixed: '#002022'
  on-tertiary-fixed-variant: '#004f54'
  background: '#121318'
  on-background: '#e3e1e9'
  surface-variant: '#34343a'
typography:
  display-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 56px
    fontWeight: '800'
    lineHeight: 64px
    letterSpacing: -0.03em
  display-xl-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 36px
    fontWeight: '800'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.025em
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 30px
    letterSpacing: -0.01em
  title-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 26px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 26px
    letterSpacing: -0.005em
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
    letterSpacing: 0em
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '600'
    lineHeight: 18px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 14px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 0.75rem
  margin: 3rem
  margin-mobile: 1.25rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style
The design system channels an immersive, theater-grade cinematic aesthetic tailored for premier film and episodic streaming. Designed for discerning cinephiles and high-engagement media consumers, the interface acts as an ambient projection room: deep, non-distracting canvases recede into absolute darkness while rich key art and vibrant metadata emerge with high-fidelity clarity. 

The stylistic direction fuses **Glassmorphism** with **Atmospheric Minimalist Dark Mode**. Translucent frosted scrims, edge-lit refraction boundaries, and micro-glow accents emulate the feel of precision optics and physical display glass. Surfaces exist as low-opacity planes suspended over darkened hero backdrops, creating deep visual depth without clutter. The resulting tone is refined, immersive, authoritative, and frictionless.

## Colors
The palette leverages a dark-room hierarchy designed to maximize dynamic range and visual impact of visual media:

- **Base Canvas & Surfaces**: Primary canvas sits at Deep Charcoal (`#090A0F`), stepping down to Pitch Black (`#0F111A`) for nested structural panels and elevated media wells. Surface overlays use variable white opacity (`rgba(255, 255, 255, 0.04)` to `rgba(255, 255, 255, 0.08)`) with matching micro-borders.
- **Neon Crimson (`#E50914`)**: Used exclusively for high-intent conversion points, primary play actions, active scrub heads, and live content indicators.
- **Electric Amber (`#F59E0B`)**: Reserved for critical ratings (e.g., IMDb/critics scores), VIP status tags, top-chart bookmarks, and warm highlights.
- **Vibrant Cyan (`#00F0FF`) & Slate Blue (`#6366F1`)**: Applied specifically to technical metadata (4K UHD, HDR10+, Dolby Vision, Spatial Audio badges) and interactive scrubbing timeline timestamps.
- **Typography & Neutrals**: Pure White (`#FFFFFF`) anchors headlines and active states; Cool Silver (`#94A3B8`) handles secondary descriptors; Muted Slate (`#64748B`) renders subtle captions and disabled elements.

## Typography
The system balances cinematic punch with high-density legibility. Headings set in **Plus Jakarta Sans** deliver geometric presence with subtle soft terminals that keep titles from feeling sterile or purely industrial. Body text and operational metadata rely on **Inter** for optical clarity across varying resolutions and dark-screen contrast tiers.

- Use **display-xl** for hero title treatments, marquee title cards, and editorial takeovers.
- All uppercase metadata chips and badges must utilize **label-sm** with positive letter tracking (`0.05em`) to ensure legibility when overlaid directly on photographic posters.
- Editorial descriptions and loglines use **body-lg** or **body-md** rendered strictly in Cool Silver (`#94A3B8`) to eliminate visual vibration against deep backdrops.

## Layout & Spacing
The layout adheres to a 12-column fluid grid system on desktop, an 8-column layout on tablet (`768px - 1024px`), and a 4-column layout on mobile (`<768px`). Outer margin spacing dynamically expands to provide cinema-scale breathing room on wide viewports (up to `1440px+` containers).

- **Horizontal Media Rails**: Break standard margin confinement, bleeding into screen edges with right padding offsets to indicate horizontal scrollability. Cards within rails maintain strict `space-md` (16px) gaps on desktop, compressing to `space-sm` (8px) on touch surfaces.
- **Section Rhythm**: Vertical intervals between topical content rails and featured spotlights use `space-xl` (40px) to prevent visual overlap between disparate video categories.
- **Hero Billboard**: Hero elements utilize dynamic viewport calculations (`70vh` to `85vh`), utilizing vertical content stacks grounded to the bottom-left quadrant using `margin` and `space-lg`.

## Elevation & Depth
Elevation is achieved using translucent optical stratification rather than high-contrast structural drops:

1. **Base Tier (Ground 0)**: Background canvases (`#090A0F` to `#0F111A`) with dynamic radial vignette masks to prevent key art bleed into UI navigation zones.
2. **Glass Tier 1 (Rails & Static Modules)**: Background `rgba(255, 255, 255, 0.03)`, `backdrop-blur-md`, subtle edge outline via `1px solid rgba(255, 255, 255, 0.06)`.
3. **Glass Tier 2 (Floating Navigation & Scrubbers)**: Background `rgba(15, 17, 26, 0.65)`, `backdrop-blur-xl`, border `1px solid rgba(255, 255, 255, 0.12)`, anchored with an ambient shadow: `0 8px 32px 0 rgba(0, 0, 0, 0.45)`.
4. **Spotlight Focus Tier (Hovered Cards & Dialogs)**: Scale transforms (`1.05x`) paired with an amplified rim highlight (`rgba(255, 255, 255, 0.2)`) and a directional neon drop-glow keyed to the primary brand red (`0 12px 40px -8px rgba(229, 9, 20, 0.35)`).

## Shapes
The design adopts a cohesive, modern rounded geometry (Level 2). Standard interface elements (buttons, badge tags, inline chips) feature an `8px` (`0.5rem`) base corner radius, balancing approachable ergonomics with sleek technical discipline. 

- Media preview cards and hero banners scale to `rounded-lg` (`16px`) to ensure softened edges framing widescreen 16:9 and 2:3 aspect media.
- Interactive control pills (such as Play/Resume and dynamic audio selector pods) scale upward to full pill silhouettes when floating detached from surface containers.

## Components

### Buttons
- **Primary Play Action**: Solid White (`#FFFFFF`) or Neon Crimson (`#E50914`) background, high-contrast dark or white typography, `rounded-md` (8px), padding `space-sm` `space-lg`. Includes leading standard icon (e.g., solid play glyph).
- **Secondary Glass Actions (Info, Add to Watchlist)**: Frosted background (`rgba(255, 255, 255, 0.1)`), text in Pure White, `backdrop-blur-lg`, outer border `1px solid rgba(255, 255, 255, 0.15)`. On hover: `rgba(255, 255, 255, 0.2)` with zero layout shift.
- **Icon Utility Buttons**: Circular `40px` or `48px` buttons, centered icon, `rgba(255, 255, 255, 0.08)` surface, `1px` subtle rim.

### Badges & Metadata Chips
- **Format Badges (4K, HDR, Spatial Audio)**: Compact container with `label-sm` bold uppercase font. Deep charcoal backdrop (`rgba(9, 10, 15, 0.8)`), border in Vibrant Cyan (`#00F0FF`) or Slate Blue (`#6366F1`) at `40%` opacity, foreground text colored to match badge border hue.
- **Maturity & Critic Tags**: Electric Amber border and text (`#F59E0B`) with black alpha backing for instant readability over fast-moving video canvas previews.

### Cards & Media Rails
- **Aspect Ratios**: 16:9 for episodic lists, continue watching, and live feeds; 2:3 for poster browses and curated collections.
- **Surface & Hover Behavior**: Base resting state uses `rounded-lg` (16px) with an invisible `1px solid rgba(255, 255, 255, 0.04)` border. On desktop hover, card expands smoothly (`scale-105`), elevates above sibling cards, activates a neon shadow ring, and crossfades to a silent looped micro-preview with dynamic playback progress bars.

### Player Timeline & Scrub Bar
- Horizontal scrubber line set to `4px` height (`rgba(255, 255, 255, 0.2)`), expanding to `6px` on track hover. Buffer track rendered in `rgba(255, 255, 255, 0.4)`, active playback path in Neon Crimson (`#E50914`), terminating in an Electric Amber scrub pin with glowing outer ring.

### Form Inputs & Search Fields
- Integrated frosted pill or `rounded-md` container (`rgba(255, 255, 255, 0.06)`), `1px solid rgba(255, 255, 255, 0.1)`. Search text in Pure White with placeholder in Muted Slate (`#64748B`). Active focus activates a Vibrant Cyan edge glow (`0 0 0 2px rgba(0, 240, 255, 0.35)`).