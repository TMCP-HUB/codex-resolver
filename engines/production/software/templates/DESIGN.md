# DESIGN.md

This file is the project design contract for AI-assisted UI work.
It defines how the product should look, feel, and behave so agents do not invent random styling on every task.

## Product direction

| Field | Decision |
|---|---|
| Product | TODO |
| Audience | TODO |
| Primary action | TODO |
| Brand mood | TODO |
| Design intensity | Quiet / Professional / Premium / Expressive / Experimental |
| Main visual risk | TODO |

## Non-negotiables

- Mobile-first layout.
- Primary action must be obvious without hunting.
- Repeated components must use the same spacing, radius, and state rules.
- Do not clone another brand.
- Do not add decorative effects that reduce readability or performance.
- Do not introduce a new UI library unless the task explicitly requires it.

## Page type priorities

| Page type | Main job | Layout priority | Avoid |
|---|---|---|---|
| Marketing landing | Convert and build trust | Hero, proof, CTA, service clarity | Generic SaaS layout with weak trust |
| Service page | Explain one offer and push contact | Clear sections, proof, repeated CTA | Long text wall with no action path |
| Location page | Rank and feel local | Local headings, service cards, area proof | Thin duplicate pages |
| Calculator or wizard | Guide input step by step | One decision per step, sticky summary | Showing every control at once on mobile |
| Admin dashboard | Manage data fast | Scan speed, density, safe actions | Pretty cards hiding operational state |
| Menu or catalog | Browse and choose quickly | Categories, item cards, prices | Desktop-first tables on phones |
| Documentation | Teach and unblock | Headings, examples, code blocks | Decoration fighting readability |
| Experimental page | Create memory and emotion | Strong art direction, controlled motion | Effects breaking usability |

## Design tokens

### Color

| Token | Value | Use |
|---|---|---|
| background | TODO | App/page background |
| surface | TODO | Cards, panels, elevated blocks |
| surface-muted | TODO | Quiet sections, subtle panels |
| text | TODO | Main readable text |
| text-muted | TODO | Secondary text and helper copy |
| border | TODO | Default dividers and card borders |
| border-strong | TODO | Active or emphasized borders |
| primary | TODO | Main CTA and primary highlights |
| primary-hover | TODO | Main CTA hover state |
| secondary | TODO | Secondary CTA or accent |
| success | TODO | Success state |
| warning | TODO | Warning state |
| danger | TODO | Error or destructive action |

### Typography

| Token | Value | Use |
|---|---|---|
| font-body | TODO | Body and UI text |
| font-heading | TODO | H1-H3 headings |
| font-mono | TODO | Code, IDs, technical labels |
| text-xs | 12px | Badges, helper text |
| text-sm | 14px | Labels, compact UI |
| text-base | 16px | Body text |
| text-lg | 18px | Lead text |
| h1 | TODO | Main page headline |
| h2 | TODO | Section heading |
| h3 | TODO | Card heading |
| line-height-body | 1.5 | Body readability |
| line-height-heading | 1.1-1.2 | Tight headings |

### Spacing

| Token | Value | Use |
|---|---:|---|
| space-0 | 0 | Reset and flush edges |
| space-1 | 4px | Tiny icon and label gaps |
| space-2 | 8px | Compact internal gaps |
| space-3 | 12px | Button and form micro spacing |
| space-4 | 16px | Default component padding |
| space-6 | 24px | Card padding and grid gaps |
| space-8 | 32px | Section internal spacing |
| space-12 | 48px | Mobile section padding |
| space-16 | 64px | Desktop section padding |
| space-24 | 96px | Large hero rhythm only |

### Radius

| Token | Value | Use |
|---|---:|---|
| radius-sm | TODO | Badges, tiny controls |
| radius-md | TODO | Inputs and buttons |
| radius-lg | TODO | Cards |
| radius-xl | TODO | Large panels |
| radius-pill | 999px | Pills and rounded CTAs |

### Shadow and elevation

| Token | Value | Use |
|---|---|---|
| shadow-none | none | Flat UI |
| shadow-soft | TODO | Default card elevation |
| shadow-elevated | TODO | Floating panels, dropdowns |
| shadow-overlay | TODO | Modals and high-focus surfaces |

### Motion

| Token | Value | Use |
|---|---|---|
| duration-fast | 120ms | Hover and active feedback |
| duration-normal | 180ms | Menus, small transitions |
| duration-slow | 320ms | Page-level or hero transitions |
| easing-standard | ease-out | Default UI motion |
| reduced-motion | required | Disable non-essential animation |

## Layout rules

| Area | Rule |
|---|---|
| Container | Use one consistent max width per page family. Do not invent section-specific widths. |
| Section padding | Mobile first. Use larger vertical rhythm only where it improves scanning. |
| Grid gap | Use tokenized gaps. Do not mix arbitrary values in repeated grids. |
| Cards | Same card family must share radius, border, padding, and image behavior. |
| Forms | Labels, errors, focus states, loading states, and disabled states must be visible. |
| CTA | Primary action must remain visible and predictable on mobile. |
| Empty states | Must explain what happened and what the user can do next. |

## Component rules

| Component | Required behavior | Forbidden behavior |
|---|---|---|
| Button | Define primary, secondary, ghost, danger, disabled, loading | New button style per section |
| Card | Define padding, border, radius, media handling | Random shadows or inconsistent radius |
| Form input | Label, helper text, error, focus, disabled | Placeholder-only labels |
| Table | Dense desktop, card/list fallback on mobile | Horizontal overflow as the only mobile plan |
| Modal | Backdrop, close, max width, scroll behavior | Content trapped off-screen |
| Navigation | Active state, mobile state, CTA placement | Moving CTA unpredictably |
| Hero | One main message, one primary action, optional secondary action | Every selling point in the hero |
| Wizard | Current step, progress, back/next, summary | All steps visible at once on mobile |

## Responsive behavior

| Breakpoint | Behavior |
|---|---|
| Mobile | One-column by default, obvious CTA, no tiny tap targets |
| Tablet | Two-column where content benefits, preserve reading flow |
| Desktop | Use wider grid only when it improves comprehension |

Minimum tap target: 44px height or width for interactive controls.

## Accessibility baseline

- Text contrast must be readable against the actual background.
- Focus states must be visible for keyboard users.
- Inputs need programmatic labels.
- Do not rely on color alone for errors or status.
- Respect reduced motion for non-essential animations.
- Images need useful alt text unless decorative.

## Do and don't

| Do | Don't |
|---|---|
| Reuse tokens and shared components | Scatter one-off Tailwind chains everywhere |
| Keep repeated sections visually consistent | Make every block a different design system |
| Make state visible | Hide loading, error, empty, or disabled states |
| Check mobile first | Fix only desktop screenshots |
| Document new variants | Add unexplained visual exceptions |
| Use motion to clarify | Use motion as decoration that slows users down |

## Visual QA checklist

Before calling a UI task done:

- [ ] The page follows this `DESIGN.md`.
- [ ] Repeated components use consistent spacing, radius, borders, and shadows.
- [ ] Primary CTA is obvious on mobile.
- [ ] Forms have label, focus, error, loading, and disabled states where relevant.
- [ ] Tables or dense layouts have a mobile plan.
- [ ] Motion is controlled and has a reduced-motion fallback where relevant.
- [ ] No unrelated visual rewrite was included.
- [ ] New tokens or variants are documented here.

## Design compliance note template

```md
## Design compliance

- Design source: DESIGN.md
- Page type:
- Design intensity:
- Tokens touched:
- Components touched:
- Mobile check:
- Visual risks:
- Verdict: pass / partial / fail
```
