"""
external_links.py

Builds "compare prices" links that send the buyer to the search-results
page for a given product name on four external marketplaces: Jumia,
Konga, Jiji and Temu.

Note: none of these platforms publish a public product-data API, and
scraping their pages would violate their Terms of Service, so this
module intentionally does NOT pull data from them. It only builds a
well-formed outbound search URL — the same as a user typing the product
name into that site's own search box.
"""

from urllib.parse import quote_plus

PLATFORMS = {
    "Jumia": {
        "url": "https://www.jumia.com.ng/catalog/?q={query}",
        "color": "#f68b1e",
    },
    "Konga": {
        "url": "https://www.konga.com/search?search={query}",
        "color": "#e12c34",
    },
    "Jiji": {
        "url": "https://jiji.ng/search?query={query}",
        "color": "#3ab54a",
    },
    "Temu": {
        "url": "https://www.temu.com/search_result.html?search_key={query}",
        "color": "#fb6a19",
    },
}


def build_links(product_name: str) -> dict:
    """Return {platform_name: search_url} for the given product name."""
    q = quote_plus(product_name)
    return {name: info["url"].format(query=q) for name, info in PLATFORMS.items()}
