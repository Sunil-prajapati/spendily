"""Tests for spec 06: date filter on GET /profile (`from` / `to` query params).

Demo seed data (user demo@spendly.com):
  2026-10-01 Food 45.50      2026-10-10 Health 25.00
  2026-10-04 Food 4.20       2026-10-12 Entertainment 15.99
  2026-10-05 Transport 30    2026-10-14 Shopping 60
  2026-10-08 Bills 82        2026-10-16 Other 12
8 expenses, total 274.69.
"""
import re
from datetime import date, timedelta

import pytest

ALL_CATEGORIES = {"Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"}


def get_profile(client, **params):
    return client.get("/profile", query_string=params)


def stat_values(html):
    """Return [expense_count, total_spent_display] from the stat tiles."""
    return re.findall(r'class="stat-value">\s*(.*?)\s*<', html, flags=re.S)


def categories(html):
    return set(re.findall(r'class="category-name">\s*(.*?)\s*<', html, flags=re.S))


def input_value(html, name):
    """Value attribute of the <input name="..."> element, or None."""
    for tag in re.findall(r"<input[^>]*>", html):
        if re.search(r'name="%s"' % re.escape(name), tag):
            m = re.search(r'value="([^"]*)"', tag)
            return m.group(1) if m else ""
    return None


def has_error(html):
    return 'class="filter-error"' in html


class TestUnfiltered:
    def test_no_params_returns_200(self, auth_client):
        assert get_profile(auth_client).status_code == 200

    def test_no_params_shows_all_expenses_and_total(self, auth_client):
        html = get_profile(auth_client).get_data(as_text=True)
        count, total = stat_values(html)[:2]
        assert count == "8", f"Expected 8 expenses, got {count}"
        assert total == "₹274.69", f"Expected ₹274.69, got {total}"

    def test_no_params_breakdown_has_all_categories(self, auth_client):
        html = get_profile(auth_client).get_data(as_text=True)
        assert categories(html) == ALL_CATEGORIES

    def test_no_params_no_error_message(self, auth_client):
        html = get_profile(auth_client).get_data(as_text=True)
        assert not has_error(html)

    def test_no_params_inputs_are_empty(self, auth_client):
        html = get_profile(auth_client).get_data(as_text=True)
        assert input_value(html, "from") == ""
        assert input_value(html, "to") == ""

    def test_empty_params_behave_as_unfiltered(self, auth_client):
        html = get_profile(auth_client, **{"from": "", "to": ""}).get_data(as_text=True)
        assert stat_values(html)[:2] == ["8", "₹274.69"]


class TestRangeFilter:
    def test_range_shows_three_expenses_totalling_137(self, auth_client):
        response = get_profile(auth_client, **{"from": "2026-10-05", "to": "2026-10-10"})
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        count, total = stat_values(html)[:2]
        assert count == "3", f"Expected 3 expenses, got {count}"
        assert total == "₹137.00", f"Expected ₹137.00, got {total}"

    def test_range_breakdown_only_transport_bills_health(self, auth_client):
        html = get_profile(
            auth_client, **{"from": "2026-10-05", "to": "2026-10-10"}
        ).get_data(as_text=True)
        assert categories(html) == {"Transport", "Bills", "Health"}

    def test_range_bounds_are_inclusive(self, auth_client):
        # Single-day ranges on boundary dates must include that day's expense.
        html = get_profile(
            auth_client, **{"from": "2026-10-05", "to": "2026-10-05"}
        ).get_data(as_text=True)
        assert stat_values(html)[:2] == ["1", "₹30.00"]

    def test_range_label_not_all_time(self, auth_client):
        html = get_profile(
            auth_client, **{"from": "2026-10-05", "to": "2026-10-10"}
        ).get_data(as_text=True)
        assert "All time" not in html, "Active range should replace the 'All time' label"

    def test_unfiltered_label_says_all_time(self, auth_client):
        html = get_profile(auth_client).get_data(as_text=True)
        assert "All time" in html


class TestSingleBound:
    def test_only_from_is_open_ended_upper(self, auth_client):
        # 10-10 Health 25 + 10-12 15.99 + 10-14 60 + 10-16 12 = 112.99
        html = get_profile(auth_client, **{"from": "2026-10-10"}).get_data(as_text=True)
        assert stat_values(html)[:2] == ["4", "₹112.99"]
        assert categories(html) == {"Health", "Entertainment", "Shopping", "Other"}

    def test_only_to_is_open_ended_lower(self, auth_client):
        # 10-01 45.50 + 10-04 4.20 + 10-05 30 = 79.70
        html = get_profile(auth_client, **{"to": "2026-10-05"}).get_data(as_text=True)
        assert stat_values(html)[:2] == ["3", "₹79.70"]
        assert categories(html) == {"Food", "Transport"}

    def test_single_bound_has_no_error(self, auth_client):
        html = get_profile(auth_client, **{"from": "2026-10-10"}).get_data(as_text=True)
        assert not has_error(html)


class TestFormPrefill:
    def test_inputs_prefilled_with_active_range(self, auth_client):
        html = get_profile(
            auth_client, **{"from": "2026-10-05", "to": "2026-10-10"}
        ).get_data(as_text=True)
        assert input_value(html, "from") == "2026-10-05"
        assert input_value(html, "to") == "2026-10-10"

    def test_only_from_prefilled_to_blank(self, auth_client):
        html = get_profile(auth_client, **{"from": "2026-10-05"}).get_data(as_text=True)
        assert input_value(html, "from") == "2026-10-05"
        assert input_value(html, "to") == ""

    def test_form_is_get_to_profile_with_date_inputs(self, auth_client):
        html = get_profile(auth_client).get_data(as_text=True)
        assert re.search(r'<form[^>]*method="get"', html, flags=re.I), "Filter form must use GET"
        assert 'type="date"' in html
        assert "Apply" in html


class TestPresetsAndClear:
    def test_preset_links_present(self, auth_client):
        html = get_profile(auth_client).get_data(as_text=True)
        for label in ("This Month", "Last 30 Days", "All Time"):
            assert label in html, f"Missing preset: {label}"

    def test_preset_links_point_to_profile(self, auth_client):
        html = get_profile(auth_client).get_data(as_text=True)
        for label in ("This Month", "Last 30 Days", "All Time"):
            m = re.search(r'<a[^>]*href="([^"]*)"[^>]*>\s*%s\s*</a>' % re.escape(label), html)
            assert m, f"Preset link not found: {label}"
            assert m.group(1).startswith("/profile"), f"{label} should link to /profile"

    def test_this_month_preset_starts_on_first_of_month(self, auth_client):
        html = get_profile(auth_client).get_data(as_text=True)
        m = re.search(r'<a[^>]*href="([^"]*)"[^>]*>\s*This Month\s*</a>', html)
        first = date.today().replace(day=1).isoformat()
        assert f"from={first}" in m.group(1).replace("&amp;", "&")

    def test_last_30_days_preset_ends_today_and_starts_in_past(self, auth_client):
        html = get_profile(auth_client).get_data(as_text=True)
        m = re.search(r'<a[^>]*href="([^"]*)"[^>]*>\s*Last 30 Days\s*</a>', html)
        href = m.group(1).replace("&amp;", "&")
        today = date.today()
        assert f"to={today.isoformat()}" in href
        found = re.search(r"from=(\d{4}-\d{2}-\d{2})", href)
        assert found, "Last 30 Days link must carry a from date"
        start = date.fromisoformat(found.group(1))
        assert 29 <= (today - start).days <= 30, "Last 30 Days should span ~30 days"

    def test_all_time_preset_has_no_bounds(self, auth_client):
        html = get_profile(auth_client).get_data(as_text=True)
        m = re.search(r'<a[^>]*href="([^"]*)"[^>]*>\s*All Time\s*</a>', html)
        assert "from=" not in m.group(1) and "to=" not in m.group(1)

    def test_clear_link_shown_when_filtered_and_returns_unfiltered(self, auth_client):
        html = get_profile(
            auth_client, **{"from": "2026-10-05", "to": "2026-10-10"}
        ).get_data(as_text=True)
        m = re.search(r'<a[^>]*href="([^"]*)"[^>]*>\s*Clear\s*</a>', html)
        assert m, "Clear link expected when a filter is active"
        follow = auth_client.get(m.group(1).replace("&amp;", "&"))
        assert follow.status_code == 200
        assert stat_values(follow.get_data(as_text=True))[:2] == ["8", "₹274.69"]


class TestEmptyRange:
    def test_range_without_expenses_shows_zero_and_message(self, auth_client):
        html = get_profile(
            auth_client, **{"from": "2025-01-01", "to": "2025-01-31"}
        ).get_data(as_text=True)
        count, total = stat_values(html)[:2]
        assert count == "0"
        assert total == "₹0.00"
        assert "No expenses in this period." in html
        assert categories(html) == set()

    def test_unfiltered_page_does_not_show_period_message(self, auth_client):
        html = get_profile(auth_client).get_data(as_text=True)
        assert "No expenses in this period." not in html


class TestInvalidInput:
    def test_from_after_to_shows_error_and_unfiltered_data(self, auth_client):
        response = get_profile(auth_client, **{"from": "2026-10-10", "to": "2026-10-05"})
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert has_error(html), "Expected inline error for reversed range"
        assert stat_values(html)[:2] == ["8", "₹274.69"]
        assert categories(html) == ALL_CATEGORIES

    @pytest.mark.parametrize("params", [
        {"from": "garbage"},
        {"to": "garbage"},
        {"from": "2026-13-45"},
        {"from": "10/05/2026", "to": "10/10/2026"},
        {"from": "2026-10-05", "to": "not-a-date"},
    ])
    def test_unparseable_date_shows_error_without_500(self, auth_client, params):
        response = get_profile(auth_client, **params)
        assert response.status_code == 200, f"Expected 200 for {params}, got {response.status_code}"
        assert has_error(response.get_data(as_text=True)), f"Expected error message for {params}"

    def test_garbage_from_ignored_so_data_unfiltered(self, auth_client):
        html = get_profile(auth_client, **{"from": "garbage"}).get_data(as_text=True)
        assert stat_values(html)[:2] == ["8", "₹274.69"]

    @pytest.mark.parametrize("payload", [
        "' OR 1=1 --",
        "2026-10-05' OR '1'='1",
        "'; DROP TABLE expenses; --",
    ])
    def test_sql_injection_does_not_error_or_change_results(self, auth_client, payload):
        response = get_profile(auth_client, **{"from": payload})
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert stat_values(html)[:2] == ["8", "₹274.69"], "Injection must not alter results"
        # Table must still exist and be queryable afterwards.
        after = get_profile(auth_client)
        assert stat_values(after.get_data(as_text=True))[:2] == ["8", "₹274.69"]

    def test_injection_in_to_param_is_safe(self, auth_client):
        response = get_profile(auth_client, **{"to": "' OR 1=1 --"})
        assert response.status_code == 200
        assert stat_values(response.get_data(as_text=True))[:2] == ["8", "₹274.69"]

    def test_very_long_value_does_not_500(self, auth_client):
        response = get_profile(auth_client, **{"from": "9" * 5000})
        assert response.status_code == 200


class TestAuthGuard:
    def test_logged_out_profile_redirects_to_login(self, client):
        response = client.get("/profile", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_logged_out_filtered_profile_redirects_to_login(self, client):
        response = client.get(
            "/profile", query_string={"from": "2026-10-05", "to": "2026-10-10"},
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_logged_out_response_does_not_leak_data(self, client):
        response = client.get("/profile", query_string={"from": "2026-10-05"})
        assert "₹" not in response.get_data(as_text=True)
