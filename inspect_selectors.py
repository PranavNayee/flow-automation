"""
Deep scan for prompt input element on Flow creation page.
Looks for textarea, contenteditable, input, and any element that could be a text input.
"""
import sys
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import Config, action_delay

config = Config()
profile_path = config.get_path('BROWSER_PROFILE_PATH')
flow_url = config.get_env('FLOW_URL', 'https://labs.google/flow')

results = {'editable_elements': [], 'buttons': [], 'all_inputs': []}

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=str(profile_path),
        headless=False,
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    )
    page = context.pages[0] if context.pages else context.new_page()

    page.on('console', lambda msg: None)
    page.on('pageerror', lambda err: None)

    print("Navigating to Flow...")
    try:
        page.goto(flow_url, wait_until='domcontentloaded', timeout=60000)
    except Exception:
        pass
    action_delay(5, 8)

    # Click "New project"
    print("Clicking 'New project'...")
    clicked = False
    for sel in ['button:has-text("New project")', 'button:has-text("Create")']:
        try:
            if page.locator(sel).count() > 0:
                page.locator(sel).first.click()
                action_delay(3, 5)
                clicked = True
                print(f"  Clicked: {sel}")
                break
        except Exception as e:
            print(f"  ERROR: {e}")

    if not clicked:
        print("  WARNING: Could not click New project")

    action_delay(3, 5)
    try:
        page.wait_for_selector('textarea, button, [contenteditable="true"]', timeout=15000)
    except Exception:
        pass

    # Deep scan: all elements that could accept text input
    print("\n--- ALL EDITABLE / INPUT ELEMENTS ---")
    all_editable = page.evaluate("""() => {
        const els = [];
        const candidates = document.querySelectorAll(
            'textarea, input, [contenteditable="true"], [contenteditable="plaintext-only"]'
        );
        candidates.forEach(el => {
            const rect = el.getBoundingClientRect();
            // Only include visible elements
            if (rect.width > 0 && rect.height > 0) {
                els.push({
                    tag: el.tagName,
                    id: el.id || '',
                    className: el.className || '',
                    placeholder: el.placeholder || '',
                    'aria-label': el.getAttribute('aria-label') || '',
                    'data-testid': el.getAttribute('data-testid') || '',
                    type: el.type || '',
                    name: el.name || '',
                    innerText: (el.innerText || '').substring(0, 80),
                    value: el.value || '',
                    contentEditable: el.isContentEditable,
                    width: Math.round(rect.width),
                    height: Math.round(rect.height),
                });
            }
        });
        return els;
    }""")

    for el in all_editable:
        results['all_inputs'].append(el)
        print(f"  <{el['tag']}> id='{el['id']}' class='{el['className'][:60]}' "
              f"placeholder='{el['placeholder'][:30]}' aria-label='{el['aria-label'][:30]}' "
              f"data-testid='{el['data-testid'][:30]}' type='{el['type']}' "
              f"contentEditable={el['contentEditable']} "
              f"size={el['width']}x{el['height']} "
              f"text='{el['innerText'][:40]}'")

    # Also find ALL buttons with their text
    print("\n--- ALL BUTTONS ---")
    all_buttons = page.evaluate("""() => {
        const els = [];
        document.querySelectorAll('button').forEach(el => {
            const rect = el.getBoundingClientRect();
            if (rect.width > 0 && rect.height > 0) {
                els.push({
                    id: el.id || '',
                    className: el.className || '',
                    'aria-label': el.getAttribute('aria-label') || '',
                    'data-testid': el.getAttribute('data-testid') || '',
                    type: el.type || '',
                    innerText: (el.innerText || '').trim().substring(0, 60),
                    disabled: el.disabled,
                    width: Math.round(rect.width),
                    height: Math.round(rect.height),
                });
            }
        });
        return els;
    }""")

    for btn in all_buttons:
        results['buttons'].append(btn)
        print(f"  <button> id='{btn['id']}' aria-label='{btn['aria-label'][:30]}' "
              f"data-testid='{btn['data-testid'][:30]}' type='{btn['type']}' "
              f"disabled={btn['disabled']} text='{btn['innerText'][:40]}' "
              f"size={btn['width']}x{btn['height']}")

    # Save results
    output = Path('selector_inspection_results.json')
    with open(output, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {output.absolute()}")

    print("\nBrowser will close in 20 seconds...")
    page.wait_for_timeout(20000)
    context.close()

print("Done.")