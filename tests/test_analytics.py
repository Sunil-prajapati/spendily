"""Tests for the Analytics placeholder page (GET /analytics) and its navbar link."""
import re

import pytest


def analytics_links(html):
    """Return the opening <a ...> tags whose href is /analytics."""
    return [
        tag for tag in re.findall(r"<a\b[^>]*>", html)
        if re.search(r'href="/analytics/?"', tag)
    ]


def class_list(tag):
    m = re.search(r'class="([^"]*)"', tag)
    return m.group(1).split() if m else []


class TestAnalyticsAccess:
    def test_anonymous_redirects_to_login(self, client):
        response = client.get("/analytics", follow_redirects=False)
        assert response.status_code == 302, "Anonymous should be redirected"
        assert "/login" in response.headers["Location"], "Should redirect to /login"

    def test_anonymous_redirect_target_renders_login(self, client):
        response = client.get("/analytics", follow_redirects=True)
        assert response.status_code == 200
        assert response.request.path == "/login"

    def test_logged_in_returns_200(self, auth_client):
        assert auth_client.get("/analytics").status_code == 200

    def test_logged_in_shows_analytics_title(self, auth_client):
        html = auth_client.get("/analytics").get_data(as_text=True)
        assert "Analytics" in html, "Expected Analytics title"
        assert re.search(r"<title>[^<]*Analytics[^<]*</title>", html, re.I), (
            "Expected Analytics in <title>"
        )

    def test_logged_in_shows_coming_soon(self, auth_client):
        html = auth_client.get("/analytics").get_data(as_text=True)
        assert "coming soon" in html.lower(), "Expected 'Coming soon' text"

    def test_page_extends_base_layout(self, auth_client):
        html = auth_client.get("/analytics").get_data(as_text=True)
        assert "<nav" in html, "Expected base layout navbar"


class TestAnalyticsNavLink:
    @pytest.mark.parametrize("path", ["/", "/login", "/register"])
    def test_link_absent_for_anonymous(self, client, path):
        html = client.get(path).get_data(as_text=True)
        assert analytics_links(html) == [], f"Analytics link must be hidden on {path}"

    @pytest.mark.parametrize("path", ["/", "/profile", "/analytics"])
    def test_link_present_for_logged_in(self, auth_client, path):
        html = auth_client.get(path).get_data(as_text=True)
        links = analytics_links(html)
        assert links, f"Analytics link expected on {path}"

    def test_link_text_is_analytics(self, auth_client):
        html = auth_client.get("/profile").get_data(as_text=True)
        assert re.search(r'<a\b[^>]*href="/analytics/?"[^>]*>\s*Analytics\s*</a>', html), (
            "Link text should be 'Analytics'"
        )

    def test_link_active_on_analytics_page(self, auth_client):
        html = auth_client.get("/analytics").get_data(as_text=True)
        tags = analytics_links(html)
        assert tags, "Analytics link missing"
        tag = tags[0]
        assert "active" in class_list(tag), f"Expected 'active' class: {tag}"
        assert 'aria-current="page"' in tag, f"Expected aria-current=page: {tag}"

    def test_link_not_active_on_profile_page(self, auth_client):
        html = auth_client.get("/profile").get_data(as_text=True)
        tags = analytics_links(html)
        assert tags, "Analytics link missing on /profile"
        tag = tags[0]
        assert "active" not in class_list(tag), f"Should not be active: {tag}"
        assert "aria-current" not in tag, f"Should not have aria-current: {tag}"
