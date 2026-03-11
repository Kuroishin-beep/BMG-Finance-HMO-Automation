"""
app.py  —  Billing Processor
=============================
Entry point. Run with:  streamlit run app.py

Project layout:
    app.py                   ← this file
    config/
        constants.py         ← all hardwired column names, keys, magic strings
    core/
        processor.py         ← pure pandas/IO logic (no Streamlit)
        sheets.py            ← Google Sheets read/write logic (no Streamlit)
    ui/
        styles.py            ← CSS injection + step-header helper
    data/
        reference.xlsx       ← local fallback only (not used on Streamlit Cloud)
    .streamlit/
        secrets.toml         ← credentials (never commit this file)

Reference source priority:
    1. Google Sheets  — when st.secrets contains [gcp_service_account]
    2. Local file     — data/reference.xlsx  (local dev fallback)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd

from config.constants import (
    APP_TITLE, APP_ICON, APP_SUBTITLE,
    TAB_PROCESSOR, TAB_REFERENCE,
    REFERENCE_FILE_PATH,
    REF_COL_ID, REF_COL_NAME, REF_COL_ENTITY,
    BIL_COL_ID, BIL_COL_NAME,
    GSHEET_SECRET_KEY, GSHEET_SECTION, GSHEET_SPREADSHEET_KEY,
    SESSION_DEFAULTS,
    SK_REF_DF, SK_RAW_DF, SK_FILTERED_DF, SK_UPDATED_REF_DF,
    SK_NEW_EMPLOYEES, SK_MISSING_EMPLOYEES,
    SK_PROCESSED, SK_SEGREGATED_BYTES, SK_UPDATED_REF_BYTES,
    SK_REF_NAME, SK_RAW_NAME,
    XLSX_MIME,
    DOWNLOAD_BILLING_FILENAME, DOWNLOAD_REFERENCE_FILENAME,
    DOWNLOAD_BILLING_LABEL, DOWNLOAD_REFERENCE_LABEL,
)
from core.processor import (
    read_reference_df, read_billing_df,
    compare_employees, update_reference, add_entity_column, segregate_billing,
    df_to_excel_bytes, multi_sheet_excel_bytes,
)
from core.sheets import load_reference_from_sheet, save_reference_to_sheet
from ui.styles import inject_styles, step_header


# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide")
inject_styles()

# ── Session state bootstrap ───────────────────────────────────────────────────
for key, default in SESSION_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ── Detect reference source ───────────────────────────────────────────────────
# Google Sheets is used when secrets are present; local file otherwise.
def _using_gsheets() -> bool:
    try:
        return GSHEET_SECRET_KEY in st.secrets
    except Exception:
        return False


def _load_reference() -> pd.DataFrame:
    """Load reference from Google Sheets or local file, whichever is available."""
    if _using_gsheets():
        return load_reference_from_sheet(
            service_account_info=dict(st.secrets[GSHEET_SECRET_KEY]),
            spreadsheet_id=st.secrets[GSHEET_SECTION][GSHEET_SPREADSHEET_KEY],
        )
    elif os.path.isfile(REFERENCE_FILE_PATH):
        return read_reference_df(REFERENCE_FILE_PATH)
    else:
        return None


def _save_reference(updated_df: pd.DataFrame) -> None:
    """Write the updated reference back to Google Sheets (cloud only)."""
    if _using_gsheets():
        save_reference_to_sheet(
            service_account_info=dict(st.secrets[GSHEET_SECRET_KEY]),
            spreadsheet_id=st.secrets[GSHEET_SECTION][GSHEET_SPREADSHEET_KEY],
            updated_df=updated_df,
        )



# TABS

tab1, tab2 = st.tabs([TAB_PROCESSOR, TAB_REFERENCE])



# TAB 1 — BILLING PROCESSOR

with tab1:

    st.markdown(f"## {APP_ICON} {APP_TITLE}")
    st.caption(APP_SUBTITLE)
    st.divider()

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 1 — LOAD REFERENCE + UPLOAD BILLING FILE
    # ─────────────────────────────────────────────────────────────────────────
    using_sheets = _using_gsheets()
    source_label = "Google Sheets" if using_sheets else "data/reference.xlsx"

    step_header(1, "Upload Billing File",
                f"Master reference loads automatically from {source_label}.")

    with st.container(border=True):

        # ── Load reference ────────────────────────────────────────────────────
        if st.session_state[SK_REF_DF] is None:
            with st.spinner("Loading reference…"):
                ref_data = _load_reference()

            if ref_data is None:
                st.error(
                    "No reference source found.  \n"
                    "• **Deployed**: add credentials to Streamlit Secrets (see README).  \n"
                    "• **Local**: place `reference.xlsx` in the `data/` folder."
                )
                st.stop()

            st.session_state[SK_REF_DF]         = ref_data
            st.session_state[SK_UPDATED_REF_DF] = ref_data.copy()
            st.session_state[SK_REF_NAME]       = source_label

        ref_df: pd.DataFrame = st.session_state[SK_REF_DF]

        icon = "☁️" if using_sheets else "📂"
        st.success(
            f"{icon} Reference loaded from **{source_label}** — "
            f"**{len(ref_df):,}** employees in master list"
        )

        st.write("")

        # ── Billing file uploader ─────────────────────────────────────────────
        raw_file = st.file_uploader(
            "Raw Billing File (.xlsx)",
            type=["xlsx"],
            key="raw_uploader",
        )
        st.caption("The .xlsx billing export")

    if raw_file:
        if raw_file.name != st.session_state[SK_RAW_NAME]:
            st.session_state[SK_RAW_DF]            = read_billing_df(raw_file)
            st.session_state[SK_RAW_NAME]          = raw_file.name
            st.session_state[SK_PROCESSED]         = False
            st.session_state[SK_FILTERED_DF]       = None
            st.session_state[SK_SEGREGATED_BYTES]  = None
            st.session_state[SK_UPDATED_REF_BYTES] = None
        st.success(
            f"✓ **{raw_file.name}** — "
            f"**{len(st.session_state[SK_RAW_DF]):,}** data rows loaded"
        )
    else:
        st.info("Upload your raw billing file above to continue.")
        st.stop()

    raw_df: pd.DataFrame = st.session_state[SK_RAW_DF]

    st.divider()

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 2 — SANITY CHECK
    # ─────────────────────────────────────────────────────────────────────────
    step_header(2, "Sanity Check", "Confirming valid billing rows are present.")

    valid_rows = raw_df[raw_df[BIL_COL_ID].notna()].copy()
    st.session_state[SK_FILTERED_DF] = valid_rows

    with st.container(border=True):
        if valid_rows.empty:
            st.error("No valid billing rows found. Please check your file.")
            st.stop()

        sc1, sc2 = st.columns([1, 3])
        sc1.metric("Valid Billing Rows", f"{len(valid_rows):,}")
        with sc2:
            with st.expander("Preview billing rows", expanded=False):
                st.dataframe(valid_rows, use_container_width=True, height=220)

    st.divider()

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 3 — SYNC PREVIEW
    # ─────────────────────────────────────────────────────────────────────────
    step_header(3, "Sync Preview", "Comparing billing IDs against the master reference.")

    filtered_df: pd.DataFrame = st.session_state[SK_FILTERED_DF]
    new_ids, missing_ids = compare_employees(filtered_df, ref_df)

    st.session_state[SK_NEW_EMPLOYEES]     = list(new_ids)
    st.session_state[SK_MISSING_EMPLOYEES] = list(missing_ids)

    with st.container(border=True):
        m1, m2 = st.columns(2, gap="medium")
        m1.metric("New Employees",     len(new_ids),
                  help="In billing but not in the reference.")
        m2.metric("Missing Employees", len(missing_ids),
                  help="In the reference but absent from this billing file.")

        if new_ids:
            new_preview = (
                filtered_df[filtered_df[BIL_COL_ID].astype(str).str.strip().isin(new_ids)]
                [[BIL_COL_ID, BIL_COL_NAME]].drop_duplicates()
            )
            with st.expander(f"New — {len(new_ids)} employee(s)", expanded=False):
                st.dataframe(new_preview, use_container_width=True, height=200)

        if missing_ids:
            missing_preview = (
                ref_df[ref_df[REF_COL_ID].astype(str).str.strip().isin(missing_ids)]
                [[REF_COL_ID, REF_COL_NAME]].drop_duplicates()
            )
            with st.expander(f"Missing — {len(missing_ids)} employee(s)", expanded=False):
                st.dataframe(missing_preview, use_container_width=True, height=200)

    st.divider()

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 4 — EXECUTE PROCESSING
    # ─────────────────────────────────────────────────────────────────────────
    step_header(4, "Process & Segregate",
                "Updates the reference, merges entities, splits billing into sheets.")

    with st.container(border=True):
        run = st.button("Run Processing", type="primary",
                        use_container_width=True, key="run_btn")

        if run:
            with st.spinner("Processing…"):

                # 4a — Update reference in-memory
                updated_ref = update_reference(ref_df, filtered_df, new_ids, missing_ids)

                # 4b — Write updated reference back to Google Sheets (cloud only)
                if using_sheets and (new_ids or missing_ids):
                    try:
                        _save_reference(updated_ref)
                        sheet_saved = True
                    except Exception as e:
                        sheet_saved = False
                        sheet_error = str(e)
                else:
                    sheet_saved = False
                    sheet_error = None

                st.session_state[SK_UPDATED_REF_DF] = updated_ref

                # 4c — Merge authoritative Entity from reference into billing
                billing = add_entity_column(filtered_df, updated_ref)

                # 4d — Segregate into sheets
                sheets = segregate_billing(billing)

                if not sheets:
                    st.error("No data to segregate. Please check your input files.")
                    st.stop()

                # 4e — Serialise to in-memory bytes
                st.session_state[SK_SEGREGATED_BYTES]  = multi_sheet_excel_bytes(sheets)
                st.session_state[SK_UPDATED_REF_BYTES] = df_to_excel_bytes(updated_ref, "Reference")
                st.session_state[SK_PROCESSED]         = True

            # ── Post-processing messages ──────────────────────────────────────
            sheet_names = list(sheets.keys())
            st.success(
                f"Done — **{len(sheet_names)}** sheet(s) created: "
                + ", ".join(f"**{n}**" for n in sheet_names)
            )

            if using_sheets and sheet_saved:
                st.info("☁️ Google Sheet updated automatically — reference is now current.")
            elif using_sheets and not sheet_saved and (new_ids or missing_ids):
                st.warning(f"⚠️ Could not write back to Google Sheets: {sheet_error}")

            st.balloons()

        elif st.session_state[SK_PROCESSED]:
            st.success("Already processed. Download below, or re-run to refresh.")

    st.divider()

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 5 — DOWNLOADS
    # ─────────────────────────────────────────────────────────────────────────
    step_header(5, "Download Results")

    if not st.session_state[SK_PROCESSED]:
        st.caption("Complete Step 4 to unlock downloads.")
    else:
        with st.container(border=True):
            d1, d2 = st.columns(2, gap="medium")

            with d1:
                st.download_button(
                    label=f"↓  {DOWNLOAD_BILLING_LABEL}",
                    data=st.session_state[SK_SEGREGATED_BYTES],
                    file_name=DOWNLOAD_BILLING_FILENAME,
                    mime=XLSX_MIME,
                    use_container_width=True,
                    type="primary",
                )
                st.caption("Multi-sheet workbook — one tab per entity")

            with d2:
                st.download_button(
                    label=f"↓  {DOWNLOAD_REFERENCE_LABEL}",
                    data=st.session_state[SK_UPDATED_REF_BYTES],
                    file_name=DOWNLOAD_REFERENCE_FILENAME,
                    mime=XLSX_MIME,
                    use_container_width=True,
                )
                # Context-aware caption
                if using_sheets:
                    st.caption("Already saved to Google Sheets — this is a local backup copy")
                else:
                    st.caption("Save this over data/reference.xlsx for the next billing cycle")



# TAB 2 — SESSION REFERENCE VIEWER

with tab2:
    st.markdown("## Reference Viewer")
    st.caption("Live view of the master reference data held in memory for this session.")
    st.divider()

    ref_to_show: pd.DataFrame | None = st.session_state[SK_UPDATED_REF_DF]

    if ref_to_show is None:
        st.info("No reference loaded yet. Go to the Billing Processor tab to begin.")
    else:
        with st.container(border=True):
            rv1, rv2, rv3 = st.columns(3, gap="medium")
            rv1.metric("Total Records",       f"{len(ref_to_show):,}")
            rv2.metric("New Employees Added", f"{len(st.session_state[SK_NEW_EMPLOYEES]):,}")
            rv3.metric("Employees Removed",   f"{len(st.session_state[SK_MISSING_EMPLOYEES]):,}")

        st.divider()
        st.dataframe(ref_to_show, use_container_width=True, height=520)