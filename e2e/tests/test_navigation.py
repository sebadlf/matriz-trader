import re

from playwright.sync_api import Page, expect


def test_root_redirects_and_menu_navigates_without_reload(page: Page, base_url: str) -> None:
    page.goto(base_url + "/")
    expect(page).to_have_url(re.compile(r"/orders$"))
    expect(page.get_by_test_id("page-ordenes")).to_be_visible()

    page.evaluate("() => { window.__noReload = true }")
    page.get_by_test_id("menu-strategies").click()

    expect(page).to_have_url(re.compile(r"/strategies$"))
    expect(page.get_by_test_id("page-estrategias")).to_be_visible()
    assert page.evaluate("() => window.__noReload === true")


def test_direct_load_of_strategies(page: Page, base_url: str) -> None:
    response = page.goto(base_url + "/strategies")
    assert response is not None
    assert response.status == 200
    expect(page.get_by_test_id("page-estrategias")).to_be_visible()
    expect(page.get_by_test_id("app-menu")).to_be_visible()
