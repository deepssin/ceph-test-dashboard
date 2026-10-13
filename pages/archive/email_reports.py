import pandas as pd
import streamlit as st

from libs.config import get_alerts_config
from libs.defaults import (
    DEFAULT_ALERTS_DAILY_REPORT_ANCHOR_HOUR,
    DEFAULT_ALERTS_NIGHTLY_ANCHOR_HOUR,
)
from libs.mail_state import MailState

st.markdown(
    "<h1 style='text-align: center;'>Email reports</h1>",
    unsafe_allow_html=True,
)

st.markdown(
    """
Scheduled **weekly digests** and **daily smoke** notifications run inside the
dashboard process (APScheduler, UTC). Use **Reports → Nightly** for the same
run status in the UI.
"""
)

try:
    cfg = get_alerts_config()
    enabled = cfg.get("enabled")
except Exception as exc:
    st.warning(f"Mail config not loaded: {exc}")
    st.stop()

if enabled:
    st.success("Outbound nightly email is **enabled**.")
    st.markdown(
        f"- **Weekly digest** — Mon {DEFAULT_ALERTS_NIGHTLY_ANCHOR_HOUR:02d}:00 UTC  \n"
        f"- **Daily smoke** — {DEFAULT_ALERTS_DAILY_REPORT_ANCHOR_HOUR:02d}:00 UTC "
        "(only when smoke runs fail or die)"
    )
else:
    st.info("Outbound nightly email is **disabled** (`[alerts] enabled = false`).")

st.divider()
st.subheader("Sent mail archive")

sqlite_path = cfg.get("sqlite_path", "")
history = MailState.list_sent_mail(sqlite_path, limit=200) if sqlite_path else []

if not history:
    st.info(
        "No sent messages recorded yet. Entries appear here after the scheduler "
        "or `ceph-test-dashboard-alerts` successfully sends mail."
    )
else:
    summary = pd.DataFrame(
        [
            {
                "Sent (UTC)": r.sent_at.strftime("%Y-%m-%d %H:%M"),
                "Type": r.kind.replace("_", " "),
                "Branch": r.branch,
                "Subject": r.subject,
                "To": r.recipients,
            }
            for r in history
        ]
    )
    st.dataframe(summary, width="stretch", hide_index=True)

    labels = [
        f"{r.sent_at.strftime('%Y-%m-%d %H:%M')} · {r.branch} · {r.subject}"
        for r in history
    ]
    pick = st.selectbox("View message", range(len(history)), format_func=lambda i: labels[i])
    row = history[pick]

    st.markdown(f"**Subject:** {row.subject}")
    st.caption(f"Recipients: {row.recipients}")
    st.markdown(row.body_html, unsafe_allow_html=True)
