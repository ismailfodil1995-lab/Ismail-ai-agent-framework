from playwright.sync_api import sync_playwright


# ==========================================
# Open Website
# ==========================================

def open_website(url):

    try:

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=False
            )

            page = browser.new_page()

            page.goto(
                url,
                wait_until="domcontentloaded"
            )

            title = page.title()

            print("=" * 60)
            print("Browser Started")
            print(f"Title : {title}")
            print("=" * 60)

            input("Press ENTER to close browser...")

            browser.close()

            return f"Opened: {title}"

    except Exception as e:

        return f"Browser Error: {e}"


# ==========================================
# Google Search
# ==========================================

def google_search(query):

    try:

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=False
            )

            page = browser.new_page()

            # ==================================
            # Use DuckDuckGo for search
            # ==================================

            page.goto(
                "https://duckduckgo.com/",
                wait_until="domcontentloaded"
            )

            page.wait_for_timeout(2000)

            # ==================================
            # Search Box
            # ==================================

            search_box = page.locator(
                "input[name='q']"
            )

            search_box.fill(query)

            search_box.press("Enter")

            page.wait_for_timeout(4000)

            # ==================================
            # Collect Results
            # ==================================

            titles = []

            results = page.locator(
                "a[data-testid='result-title-a']"
            )

            count = results.count()

            for i in range(min(count, 5)):

                try:

                    title = results.nth(i).inner_text()

                    title = title.strip()

                    if title:
                        titles.append(title)

                except:
                    pass

            # ==================================
            # Fallback Selector
            # ==================================

            if not titles:

                results = page.locator(
                    "a.result__a"
                )

                count = results.count()

                for i in range(min(count, 5)):

                    try:

                        title = results.nth(i).inner_text()

                        title = title.strip()

                        if title:
                            titles.append(title)

                    except:
                        pass

            # ==================================
            # Show Results
            # ==================================

            print("=" * 60)
            print("Search Results")
            print("=" * 60)

            if titles:

                for title in titles:
                    print(title)

            else:

                print("No results.")

            print("=" * 60)

            # Keep browser open
            input("Press ENTER to close browser...")

            browser.close()

            # ==================================
            # Return Results To Agent
            # ==================================

            if not titles:

                return "No results."

            return "\n".join(titles)

    except Exception as e:

        return f"Search Error: {e}"


# ==========================================
# Direct DuckDuckGo Search
# ==========================================

def duckduckgo_search(query):

    return google_search(query)