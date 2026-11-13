from playwright.sync_api import Page, expect


def test_health_page_shows_backend_ok(page: Page, base_url: str) -> None:
    page.goto(base_url + "/health")

    expect(page.get_by_test_id("health-status")).to_have_text("ok", timeout=30_000)
    expect(page.get_by_test_id("health-database")).to_have_text("ok", timeout=30_000)
