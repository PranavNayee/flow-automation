# Flow UI Selector Update Guide

The following selectors need to be updated in `selectors.yaml`:

## main.prompt_textarea

**Current selector:** `div[aria-label="What do you want to create?"], div.ProseMirror[contenteditable="true"]`

**Error:** Element not found or not visible

**How to fix:**
1. Open Flow in your browser
2. Open DevTools (F12 or Cmd+Opt+I)
3. Use Element Picker (Ctrl+Shift+C / Cmd+Shift+C)
4. Click on the relevant UI element
5. In the Elements tab, right-click the highlighted element
6. Select 'Copy' → 'Copy selector'
7. Update `selectors.yaml` → `main.prompt_textarea`

**Prefer selectors in this order:**
1. `[data-testid='...']` (most stable)
2. `[aria-label='...']` (accessible, fairly stable)
3. `id='...'` (stable if present)
4. Semantic HTML with attributes (e.g., `button[type='submit']`)
5. CSS classes (least stable, avoid if possible)

---

## main.prompt_submit_button

**Current selector:** `button[aria-label="Start generation"]`

**Error:** Element not found or not visible

**How to fix:**
1. Open Flow in your browser
2. Open DevTools (F12 or Cmd+Opt+I)
3. Use Element Picker (Ctrl+Shift+C / Cmd+Shift+C)
4. Click on the relevant UI element
5. In the Elements tab, right-click the highlighted element
6. Select 'Copy' → 'Copy selector'
7. Update `selectors.yaml` → `main.prompt_submit_button`

**Prefer selectors in this order:**
1. `[data-testid='...']` (most stable)
2. `[aria-label='...']` (accessible, fairly stable)
3. `id='...'` (stable if present)
4. Semantic HTML with attributes (e.g., `button[type='submit']`)
5. CSS classes (least stable, avoid if possible)

---

