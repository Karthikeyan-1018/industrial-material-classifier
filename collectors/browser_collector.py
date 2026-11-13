"""TradeIndia search and product-page collection using a headless browser."""

import re
from urllib.parse import urljoin, urlparse

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


TRADEINDIA_HOME_URL = "https://www.tradeindia.com/"
SEARCH_INPUT_SELECTOR = "input.searchBox"
SEARCH_BUTTON_SELECTOR = "button.srchBtn"
PRODUCT_LINK_SELECTOR = 'a[href*="/products/"]'
MATERIAL_TERMS = (
    "stainless steel", "mild steel", "carbon steel", "alloy steel", "steel",
    "aluminium", "aluminum", "brass", "copper", "cast iron", "metal",
    "hdpe", "ldpe", "pvc", "cpvc", "polypropylene", "abs", "nylon",
    "ptfe", "polycarbonate", "polyethylene", "polyvinyl chloride",
)
RESTRICTED_MARKERS = (
    "captcha", "verify you are human", "access denied", "too many requests",
    "please login", "sign in to continue",
)


def _valid_product_url(url):
    parsed = urlparse(url or "")
    host = (parsed.hostname or "").lower()
    return (
        parsed.scheme == "https"
        and (host == "tradeindia.com" or host.endswith(".tradeindia.com"))
        and re.fullmatch(r"/products/[^/]+-c\d+\.html", parsed.path) is not None
    )


def _title_matches_keyword(product_name, keyword):
    title_terms = set(re.findall(r"[a-z0-9]+", product_name.casefold()))
    query_terms = [term for term in re.findall(r"[a-z0-9]+", keyword.casefold()) if len(term) > 2]
    if not query_terms:
        return True
    minimum_matches = max(1, (2 * len(query_terms) + 2) // 3)
    return sum(term in title_terms for term in set(query_terms)) >= minimum_matches


def _material_evidence(text):
    """Return page text snippets mentioning material terms as evidence only."""
    specs_start = re.search(r"\bProduct Specifications\b", text, re.I)
    if specs_start:
        text = text[specs_start.end():]
        details_end = re.search(r"\bCompany Details\b", text, re.I)
        if details_end:
            text = text[:details_end.start()]
    found = []
    for line in (line.strip() for line in text.splitlines()):
        if line and any(re.search(r"\b" + re.escape(term) + r"\b", line, re.I) for term in MATERIAL_TERMS):
            if line not in found:
                found.append(line[:500])
    return " | ".join(found[:20])


class BrowserCollector:
    def __init__(self, timeout_ms=45000):
        self.timeout_ms = timeout_ms

    def get_top_product(self, keyword):
        if not keyword or not keyword.strip():
            raise ValueError("Search keyword cannot be empty.")

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.set_default_timeout(self.timeout_ms)
                try:
                    response = page.goto(TRADEINDIA_HOME_URL, wait_until="domcontentloaded", timeout=self.timeout_ms)
                    status = response.status if response else None
                    if status in (401, 403, 429):
                        raise RuntimeError(
                            f"TradeIndia returned HTTP {status}; access is restricted or rate limited. "
                            "Stop and retry only when access is authorized and the limit has cleared."
                        )

                    search_input = page.locator(SEARCH_INPUT_SELECTOR)
                    search_button = page.locator(SEARCH_BUTTON_SELECTOR)
                    if search_input.count() == 0 or search_button.count() == 0:
                        raise RuntimeError(
                            "TradeIndia homepage search controls were not found; the page layout may have changed."
                        )
                    search_input.first.fill(keyword.strip())
                    search_button.first.click()
                    try:
                        page.wait_for_url("**/search.html?keyword=*", timeout=self.timeout_ms)
                    except PlaywrightTimeoutError as exc:
                        raise RuntimeError(
                            f"TradeIndia did not complete a keyword search for {keyword!r}. "
                            f"Current page title={page.title().strip()!r}, URL={page.url!r}."
                        ) from exc

                    links = page.locator(PRODUCT_LINK_SELECTOR)
                    try:
                        # A generic navigation link can appear before TradeIndia hydrates
                        # its search results. Wait for the observed product-detail URL shape.
                        page.wait_for_function(
                            """() => Array.from(document.querySelectorAll('a[href*="/products/"]')).some((a) => {
                                try {
                                    const path = new URL(a.href).pathname;
                                    return /^\\/products\\/[^/]+-c\\d+\\.html$/.test(path) && a.innerText.trim();
                                } catch (_) { return false; }
                            })""",
                            timeout=self.timeout_ms,
                        )
                    except PlaywrightTimeoutError as exc:
                        body = page.locator("body").inner_text(timeout=3000).strip()
                        if any(marker in body.lower() for marker in RESTRICTED_MARKERS):
                            raise RuntimeError(
                                "TradeIndia displayed an access, login, CAPTCHA, or rate-limit page. "
                                "The collector stops here and does not attempt to bypass it."
                            ) from exc
                        excerpt = " ".join(body.split())[:240] or "(empty page)"
                        raise RuntimeError(
                            "No TradeIndia product links appeared within the wait period. "
                            f"HTTP status={status or 'unknown'}, title={page.title().strip()!r}, "
                            f"final URL={page.url!r}, page text={excerpt!r}."
                        ) from exc

                    # TradeIndia can include image and title links for one listing.
                    # Choose the first product URL whose link has a visible title.
                    product_name = ""
                    product_url = ""
                    valid_listing_seen = False
                    link_count = links.count()
                    link_samples = []
                    for index in range(link_count):
                        link = links.nth(index)
                        name = " ".join(link.inner_text().split())
                        href = link.get_attribute("href")
                        if index < 6:
                            link_samples.append(f"{name[:70]!r} -> {href!r}")
                        if name and href:
                            candidate = urljoin(page.url, href)
                            if _valid_product_url(candidate):
                                valid_listing_seen = True
                                if not _title_matches_keyword(name, keyword):
                                    continue
                                product_name, product_url = name, candidate
                                break
                    if not product_name:
                        if valid_listing_seen:
                            raise RuntimeError(
                                f"TradeIndia returned product detail links, but none of their titles matched "
                                f"the keyword {keyword!r}; no record was saved. "
                                f"Page title={page.title().strip()!r}, URL={page.url!r}, "
                                f"sample links={link_samples!r}."
                            )
                        raise RuntimeError(
                            "TradeIndia returned navigation or category links, but no valid product-detail "
                            "link matching /products/<name>-c<id>.html; no record was saved. "
                            f"Page title={page.title().strip()!r}, URL={page.url!r}, "
                            f"product-link count={link_count}, sample links={link_samples!r}."
                        )

                    detail = browser.new_page()
                    try:
                        detail_response = detail.goto(product_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                        detail_status = detail_response.status if detail_response else None
                        if detail_status in (401, 403, 429):
                            raise RuntimeError(
                                f"TradeIndia detail page returned HTTP {detail_status}; access is restricted or rate limited."
                            )
                        detail.locator("body").wait_for(state="visible", timeout=self.timeout_ms)
                        page_text = detail.locator("body").inner_text(timeout=self.timeout_ms)
                    except PlaywrightTimeoutError as exc:
                        raise RuntimeError("Timed out opening or reading the TradeIndia product detail page.") from exc
                    if any(marker in page_text.lower() for marker in RESTRICTED_MARKERS):
                        raise RuntimeError(
                            "TradeIndia displayed an access, login, CAPTCHA, or rate-limit page. "
                            "The collector stops here and does not attempt to bypass it."
                        )
                    if not _valid_product_url(detail.url):
                        raise RuntimeError("TradeIndia redirected the product page to an unexpected URL.")
                    return {
                        "product_name": product_name,
                        "source_url": detail.url,
                        "material_evidence": _material_evidence(page_text),
                    }
                except PlaywrightTimeoutError as exc:
                    raise RuntimeError("Timed out waiting for TradeIndia search results.") from exc
            finally:
                browser.close()
