import contextlib
import io
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image
from playwright.sync_api import sync_playwright

import enumerate_all as capture


URL = "https://example.grafana.azure.com/d/test?from=1&to=2"


def snapshot(text="Metric\n42", **overrides):
    result = {"text": text, "rows": [], "loading": False, "errors": [],
              "table": False, "expected_rows": 0, "chart": True}
    result.update(overrides)
    return result


class SnapshotTests(unittest.TestCase):
    def test_title_only_is_not_ready_even_when_canvas_exists(self):
        self.assertIsNone(capture.validate_snapshot(snapshot("Metric"), "Metric"))

    def test_loading_is_not_ready(self):
        self.assertIsNone(capture.validate_snapshot(snapshot(loading=True), "Metric"))

    def test_zero_event_counter_is_valid_data(self):
        self.assertEqual(capture.validate_snapshot(
            snapshot("VM Events:\nReboots\n0", chart=False), "VM Events:"), "data")

    def test_no_data_is_case_insensitive_and_not_title_substring(self):
        self.assertEqual(capture.validate_snapshot(
            snapshot("Metric\nNO DATA", chart=False), "Metric"), "no_data")
        self.assertIsNone(capture.validate_snapshot(
            snapshot("No Data Rate", chart=False), "No Data Rate"))

    def test_error_is_explicit(self):
        with self.assertRaisesRegex(capture.CaptureError, "query failed"):
            capture.validate_snapshot(snapshot(errors=["query failed"]), "Metric")

    def test_no_data_ignores_generic_status_badge(self):
        for status in ("Panel status", "No data", " NO DATA "):
            with self.subTest(status=status):
                self.assertEqual(capture.validate_snapshot(
                    snapshot("Outages\nNo data", errors=[status]), "Outages"), "no_data")

    def test_no_data_does_not_hide_real_query_error(self):
        with self.assertRaisesRegex(capture.CaptureError, "query failed"):
            capture.validate_snapshot(
                snapshot("Outages\nNo data", errors=["Panel status", "query failed"]), "Outages")

    def test_generic_status_without_no_data_is_not_ignored(self):
        with self.assertRaisesRegex(capture.CaptureError, "Panel status"):
            capture.validate_snapshot(snapshot("Outages", errors=["Panel status"]), "Outages")

    def test_no_data_while_loading_is_not_final(self):
        self.assertIsNone(capture.validate_snapshot(
            snapshot("Outages\nNo data", loading=True, errors=["Panel status"]), "Outages"))

    def test_expanded_grid_requires_all_rows_and_unclipped_bounds(self):
        rows = [{"text": "Header", "visible": True, "clipped": False},
                {"text": "Value", "visible": True, "clipped": True}]
        state = snapshot("Table\nHeader\nValue", table=True, rows=rows, expected_rows=3)
        self.assertEqual(capture.validate_snapshot(state, "Table"), "data")
        self.assertIsNone(capture.validate_snapshot(state, "Table", expanded=True))
        rows[1]["clipped"] = False
        self.assertIsNone(capture.validate_snapshot(state, "Table", expanded=True))
        state["expected_rows"] = 2
        self.assertEqual(capture.validate_snapshot(state, "Table", expanded=True), "data")

    def test_wait_ready_requires_stable_populated_text(self):
        panel = MagicMock()
        populated = snapshot()
        with patch.object(capture, "panel_snapshot", side_effect=[
            snapshot("Metric"), populated, populated
        ]):
            state, status = capture.wait_ready(panel, "Metric", time.monotonic() + 10)
        self.assertEqual(status, "data")
        self.assertEqual(state["text"], "Metric\n42")
        self.assertEqual(panel.page.wait_for_timeout.call_count, 2)


class CaptureRetryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.out = Path(self.directory.name)
        self.panel = MagicMock()
        self.panel.page.is_closed.return_value = False
        self.panel.page.locator.return_value.count.return_value = 1
        self.panel.screenshot.side_effect = lambda **kwargs: Image.new(
            "RGB", (80, 40), "white"
        ).save(kwargs["path"])

    def test_no_data_never_takes_screenshot(self):
        with patch.object(capture, "wait_ready", return_value=(snapshot("Metric\nNo data"), "no_data")):
            result = capture.capture_panel(self.panel, "Metric", 1, self.out)
        self.assertIsNone(result["file"])
        self.assertTrue(result["no_data"])
        self.panel.screenshot.assert_not_called()
        self.panel.scroll_into_view_if_needed.assert_called_once()

    def test_changed_text_retries_same_panel_and_page(self):
        state = snapshot()
        with (
            patch.object(capture, "wait_ready", side_effect=[
                (state, "data"), (state, "data"), (snapshot("Metric\n43"), "data"),
                (state, "data"), (state, "data"), (state, "data"),
            ]),
            patch.object(capture, "hide_chrome"),
            patch.object(capture, "restore_chrome") as restore,
            patch.object(capture, "restore_panel"),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            result = capture.capture_panel(self.panel, "Metric", 1, self.out)
        self.assertEqual(result["status"], "data")
        self.assertEqual(self.panel.screenshot.call_count, 2)
        self.assertEqual(restore.call_count, 2)
        self.panel.page.goto.assert_not_called()
        self.panel.page.context.new_page.assert_not_called()

    def test_table_chrome_changes_do_not_trigger_recapture(self):
        rows = [{"text": "Time\nValue", "visible": True, "clipped": False},
                {"text": "20:28\nShutdown", "visible": True, "clipped": False}]
        before = snapshot("Reboot Detail\nTime\nValue\n20:28\nShutdown", table=True, rows=rows)
        after = dict(before, text=before["text"] + "\nPanel menu")
        with (
            patch.object(capture, "wait_ready", side_effect=[
                (before, "data"), (before, "data"), (after, "data"),
            ]),
            patch.object(capture, "expand_panel"),
            patch.object(capture, "hide_chrome"),
            patch.object(capture, "restore_chrome"),
            patch.object(capture, "restore_panel"),
        ):
            result = capture.capture_panel(self.panel, "Reboot Detail", 1, self.out)
        self.assertEqual(result["status"], "data")
        self.panel.screenshot.assert_called_once()

    def test_table_evidence_changes_remain_distinct(self):
        before = snapshot(table=True, rows=[{"text": "Shutdown"}])
        after = snapshot(table=True, rows=[{"text": "Reset"}])
        self.assertNotEqual(capture.evidence_signature(before), capture.evidence_signature(after))

    def test_exhausted_retries_return_error_without_success_shaped_file(self):
        with (
            patch.object(capture, "wait_ready", side_effect=capture.CaptureError("not ready")),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            result = capture.capture_panel(self.panel, "Metric", 1, self.out)
        self.assertEqual(result["status"], "error")
        self.assertIsNone(result["file"])
        self.assertEqual(self.panel.scroll_into_view_if_needed.call_count, 2)

    def test_lost_session_stops_without_retrying_login(self):
        self.panel.page.locator.return_value.count.return_value = 0
        with (
            patch.object(capture, "wait_ready", side_effect=capture.CaptureError("session expired")),
            contextlib.redirect_stderr(io.StringIO()),
            self.assertRaisesRegex(capture.CaptureError, "session lost"),
        ):
            capture.capture_panel(self.panel, "Metric", 1, self.out)
        self.assertEqual(self.panel.scroll_into_view_if_needed.call_count, 1)
        self.panel.page.goto.assert_not_called()


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.out = Path(self.directory.name)
        self.context = MagicMock()
        self.page = MagicMock()
        self.page.url = "about:blank"
        self.context.pages = [self.page]
        self.runtime = MagicMock()
        self.runtime.chromium.launch_persistent_context.return_value = self.context
        self.manager = MagicMock()
        self.manager.__enter__.return_value = self.runtime

    def test_one_launch_navigation_and_close_after_validation(self):
        sentinel = self.out / "keep.txt"
        sentinel.write_text("unrelated")
        events = []
        self.context.close.side_effect = lambda: events.append("close")
        with (
            patch.object(capture, "sync_playwright", return_value=self.manager),
            patch.object(capture, "capture_dashboard", side_effect=lambda *args: events.append("validate") or [{}]),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            result = capture.main([URL, str(self.out)])
        self.assertEqual(result, 0)
        self.assertEqual(events, ["validate", "close"])
        self.runtime.chromium.launch_persistent_context.assert_called_once()
        self.page.goto.assert_called_once_with(URL, wait_until="domcontentloaded", timeout=60000)
        self.context.new_page.assert_not_called()
        self.context.close.assert_called_once()
        self.assertEqual(sentinel.read_text(), "unrelated")

    def test_existing_context_and_matching_tab_are_not_reopened_or_closed(self):
        self.page.url = URL
        with patch.object(capture, "capture_dashboard", return_value=[{}]), contextlib.redirect_stdout(io.StringIO()):
            capture.capture_in_context(self.context, URL, self.out)
        self.page.goto.assert_not_called()
        self.context.new_page.assert_not_called()
        self.context.close.assert_not_called()

    def test_validation_failure_closes_once_and_does_not_relaunch(self):
        with (
            patch.object(capture, "sync_playwright", return_value=self.manager),
            patch.object(capture, "capture_dashboard", side_effect=capture.CaptureError("bad evidence")),
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()) as stderr,
        ):
            result = capture.main([URL, str(self.out)])
        self.assertEqual(result, 1)
        self.runtime.chromium.launch_persistent_context.assert_called_once()
        self.context.close.assert_called_once()
        self.assertIn("bad evidence", stderr.getvalue())

    def test_launch_failure_does_not_retry(self):
        self.runtime.chromium.launch_persistent_context.side_effect = capture.PlaywrightError("profile locked")
        with (
            patch.object(capture, "sync_playwright", return_value=self.manager),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(capture.main([URL, str(self.out)]), 1)
        self.runtime.chromium.launch_persistent_context.assert_called_once()

    def test_signin_timeout_does_not_open_another_page(self):
        self.page.wait_for_selector.side_effect = capture.PlaywrightError("timeout")
        with (
            contextlib.redirect_stdout(io.StringIO()),
            self.assertRaisesRegex(capture.CaptureError, "without opening another session"),
        ):
            capture.capture_in_context(self.context, URL, self.out)
        self.page.goto.assert_called_once()
        self.context.new_page.assert_not_called()
        self.context.close.assert_not_called()


class LocalRenderingTests(unittest.TestCase):
    """Offline DOM fixtures in an ephemeral headless browser, never the auth profile."""

    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(channel="msedge", headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.page = self.browser.new_page(viewport={"width": 1200, "height": 800})
        self.page.route("**/*", lambda route: route.abort())
        self.addCleanup(self.page.close)
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.out = Path(self.directory.name)

    def table_fixture(self, title="Table", row_count=12):
        rows = '<div role="row"><div role="columnheader">Time</div><div role="columnheader">Value</div></div>'
        rows += "".join(
            f'<div role="row"><div role="gridcell">{i}</div><div role="gridcell">Value {i}</div></div>'
            for i in range(row_count)
        )
        self.page.set_content(f"""<style>
            body{{background:#101217;color:white;margin:0}}
            .react-grid-item{{position:absolute;top:20px;left:20px;width:240px;height:120px;background:#101217}}
            section{{height:100%;display:flex;flex-direction:column}}
            .content{{flex:1;overflow:hidden}}
            [role=grid]{{height:70px;width:220px;overflow:auto}}
            [role=row]{{display:flex;width:600px;height:30px;flex-shrink:0}}
            [role=gridcell],[role=columnheader]{{width:300px;flex-shrink:0}}
            </style><div class="react-grid-item" id="target"><section>
            <h2 data-testid="data-testid Panel header {title}">{title}</h2>
            <div class="content"><div role="grid" aria-rowcount="{row_count + 1}">{rows}</div></div>
            </section></div>
            <div class="react-grid-item" id="neighbor" style="top:120px;background:red"></div>""")
        return self.page.locator("#target")

    def test_expanded_table_captures_all_rows_and_restores_layout(self):
        panel = self.table_fixture()
        with contextlib.redirect_stderr(io.StringIO()):
            result = capture.capture_panel(panel, "Table", 1, self.out, timeout=10)
        self.assertEqual(result["status"], "data", result.get("error"))
        self.assertEqual(len(result["rows"]), 13)
        self.assertIn("Value 11", result["text"])
        self.assertEqual(round(panel.bounding_box()["height"]), 120)
        self.assertEqual(self.page.locator("#neighbor").evaluate("el=>getComputedStyle(el).visibility"), "visible")
        with Image.open(self.out / result["file"]) as image:
            self.assertGreater(image.width, 300)
            self.assertGreater(image.height, 390)
            self.assertNotEqual(image.convert("RGB").getpixel((25, 160)), (255, 0, 0))

    def test_delayed_render_does_not_capture_title_only(self):
        self.page.set_content("""<div class="react-grid-item">
            <h2>VM Events:</h2><div id="values"></div></div>
            <script>setTimeout(()=>document.querySelector('#values').innerText='Reboots\\n11',400)</script>""")
        result = capture.capture_panel(self.page.locator(".react-grid-item"), "VM Events:", 1, self.out)
        self.assertEqual(result["status"], "data")
        self.assertIn("Reboots\n11", result["text"])

    def test_dashboard_panel_reordering_keeps_original_identity(self):
        self.page.set_content("""
            <div class="react-grid-item" id="first">
              <h2 data-testid="data-testid Panel header First">First</h2>42
            </div>
            <div class="react-grid-item" id="second">
              <h2 data-testid="data-testid Panel header Second">Second</h2>24
            </div>
        """)
        def fake_capture(panel, title, index, out_dir):
            if title == "First":
                panel.evaluate("el => el.parentElement.appendChild(el)")
            return {"index": index, "title": title, "status": "data", "file": None}
        with patch.object(capture, "capture_panel", side_effect=fake_capture):
            result = capture.capture_dashboard(self.page, self.out)
        self.assertEqual([item["title"] for item in result], ["First", "Second"])

    def test_grid_keys_survive_element_id_changes(self):
        self.page.set_content("""
            <div class="react-grid-item" id="first" data-griditem-key="grid-first">
              <h2 data-testid="data-testid Panel header First">First</h2>42
            </div>
            <div class="react-grid-item" id="second" data-griditem-key="grid-second">
              <h2 data-testid="data-testid Panel header Second">Second</h2>24
            </div>
        """)
        def fake_capture(panel, title, index, out_dir):
            if title == "First":
                panel.page.evaluate("""() => {
                    document.querySelectorAll('.react-grid-item').forEach(el => {
                        el.id += '-remounted';
                    });
                }""")
            return {"index": index, "title": title, "status": "data", "file": None}
        with patch.object(capture, "capture_panel", side_effect=fake_capture):
            result = capture.capture_dashboard(self.page, self.out)
        self.assertEqual([item["title"] for item in result], ["First", "Second"])

    def test_hidden_table_rows_do_not_block_loaded_data(self):
        panel = self.table_fixture(row_count=3)
        panel.evaluate("""el => {
            const hidden = document.createElement('div');
            hidden.setAttribute('role', 'row');
            hidden.style.display = 'none';
            el.querySelector('[role="grid"]').appendChild(hidden);
        }""")
        result = capture.capture_panel(panel, "Table", 1, self.out, timeout=15)
        self.assertEqual(result["status"], "data", result.get("error"))
        self.assertEqual(len(result["rows"]), 4)

    def test_cells_overflowing_row_width_are_fitted(self):
        panel = self.table_fixture(row_count=3)
        self.page.add_style_tag(content="[role=row]{width:400px;overflow:visible}")
        with patch.object(capture, "autocrop"):
            result = capture.capture_panel(panel, "Table", 1, self.out, timeout=15)
        self.assertEqual(result["status"], "data", result.get("error"))
        with Image.open(self.out / result["file"]) as image:
            self.assertGreaterEqual(image.width, 600)

    def test_display_contents_rows_use_visible_cells(self):
        panel = self.table_fixture(row_count=3)
        self.page.add_style_tag(content="""
            [role=grid] { display:grid; grid-template-columns:300px 300px; }
            [role=row] { display:contents; }
            [role=gridcell],[role=columnheader] { height:30px; }
        """)
        result = capture.capture_panel(panel, "Table", 1, self.out, timeout=15)
        self.assertEqual(result["status"], "data", result.get("error"))
        self.assertEqual(len(result["rows"]), 4)

    def test_nested_display_contents_header_is_counted_and_captured(self):
        panel = self.table_fixture(row_count=3)
        panel.evaluate("""el => {
            const header = el.querySelector('[role="row"]');
            const wrapper = document.createElement('div');
            wrapper.style.display = 'contents';
            while (header.firstChild) wrapper.appendChild(header.firstChild);
            header.appendChild(wrapper);
        }""")
        result = capture.capture_panel(panel, "Table", 1, self.out, timeout=15)
        self.assertEqual(result["status"], "data", result.get("error"))
        self.assertEqual(len(result["rows"]), 4)
        self.assertIn("Time", result["rows"][0])
        self.assertIn("Value", result["rows"][0])

    def test_no_data_does_not_produce_an_image(self):
        self.page.set_content('<div class="react-grid-item"><h2>Outages</h2>No Data</div>')
        result = capture.capture_panel(self.page.locator(".react-grid-item"), "Outages", 1, self.out)
        self.assertEqual(result["status"], "no_data")
        self.assertEqual(list(self.out.iterdir()), [])

    def test_no_data_status_badge_does_not_fail_dashboard(self):
        self.page.set_content("""<div class="react-grid-item">
            <h2 data-testid="data-testid Panel header Outages">Outages</h2>
            <span role="alert" aria-label="Panel status"
                  style="display:inline-block;width:16px;height:16px"></span>
            <div>No data</div></div>""")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as stderr:
            manifest = capture.capture_dashboard(self.page, self.out)
        self.assertEqual(manifest[0]["status"], "no_data")
        self.assertTrue(manifest[0]["no_data"])
        self.assertIsNone(manifest[0]["file"])
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual([p.name for p in self.out.iterdir()], ["manifest.json"])

    def test_incomplete_grid_is_rejected(self):
        panel = self.table_fixture()
        capture.expand_panel(panel)
        panel.locator('[role="grid"]').evaluate("el=>el.setAttribute('aria-rowcount','99')")
        state = capture.panel_snapshot(panel)
        self.assertIsNone(capture.validate_snapshot(state, "Table", expanded=True))

    def test_failed_panels_are_persisted_and_fail_the_run(self):
        self.page.set_content("""<div class="react-grid-item">
            <h2 data-testid="data-testid Panel header Test">Test</h2>
            <div role="alert">Query failed</div></div>""")
        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(capture.CaptureError, "Evidence validation failed"):
                capture.capture_dashboard(self.page, self.out)
        manifest = json.loads((self.out / "manifest.json").read_text())
        self.assertEqual(manifest[0]["status"], "error")
        self.assertIsNone(manifest[0]["file"])
        self.assertIn("Query failed", manifest[0]["error"])


if __name__ == "__main__":
    unittest.main()
