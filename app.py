import sys
import os

# Allow sibling imports when run from the project root
sys.path.insert(0, os.path.dirname(__file__))
import streamlit as st
import pandas as pd

# Project imports 
from config.constants import (
    APP_TITLE, APP_ICON, APP_SUBTITLE,
    TAB_PROCESSOR, TAB_REFERENCE,
    ID_COLUMN_CANDIDATES, NAME_COLUMN_CANDIDATES,
    ENTITY_COLUMN_CANDIDATES, SUBJECT_COLUMN_CANDIDATES,
    SESSION_DEFAULTS,
    SK_REF_DF, SK_RAW_DF, SK_FILTERED_DF, SK_UPDATED_REF_DF,
    SK_NEW_EMPLOYEES, SK_MISSING_EMPLOYEES,
    SK_PROCESSED, SK_SEGREGATED_BYTES, SK_UPDATED_REF_BYTES,
    SK_REF_NAME, SK_RAW_NAME,
    REFERENCE_FILE_PATH,
    BILLING_KEYWORDS,
    XLSX_MIME,
    DOWNLOAD_BILLING_FILENAME, DOWNLOAD_REFERENCE_FILENAME,
    DOWNLOAD_BILLING_LABEL, DOWNLOAD_REFERENCE_LABEL,
)
from core.processor import (
    normalize_columns, find_column, read_excel_to_df,
    filter_billing_rows, compare_employees,
    update_reference, merge_entity, segregate_billing,
    df_to_excel_bytes, multi_sheet_excel_bytes,
)
from ui.styles import inject_styles, step_header


#  Page config
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
)

inject_styles()

# Session state bootstrap 
for key, default in SESSION_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default


# 
# TABS
# 
tab1, tab2 = st.tabs([TAB_PROCESSOR, TAB_REFERENCE])


# TAB 1 — BILLING PROCESSOR
with tab1:

    # Page header 
    st.markdown(f"## {APP_ICON} {APP_TITLE}")
    st.caption(APP_SUBTITLE)
    st.divider()

        # STEP 1 — FILE UPLOADS
        step_header(1, "Upload Billing File", "The master reference is loaded automatically from data/reference.xlsx.")

    with st.container(border=True):
        # Auto-load reference from data/reference.xlsx
        ref_exists = os.path.isfile(REFERENCE_FILE_PATH)

        if ref_exists:
            # Only reload from disk if not yet in session (avoids re-reading every rerun)
            if st.session_state[SK_REF_DF] is None or st.session_state[SK_REF_NAME] != REFERENCE_FILE_PATH:
                st.session_state[SK_REF_DF]         = normalize_columns(pd.read_excel(REFERENCE_FILE_PATH, engine="openpyxl"))
                st.session_state[SK_UPDATED_REF_DF] = st.session_state[SK_REF_DF].copy()
                st.session_state[SK_REF_NAME]       = REFERENCE_FILE_PATH
            st.success("✓ Reference loaded from **data/reference.xlsx**")
        else:
            st.error(
                "**data/reference.xlsx** not found. "
                "Place your master reference file at `billing_processor/data/reference.xlsx` and restart."
            )
            st.stop()

        st.write("")  # small spacer

        #  Billing file uploader 
        raw_file = st.file_uploader(
            "Raw Billing File",
            type=["xlsx"],
            key="raw_uploader",
            label_visibility="visible",
        )
        st.caption("Any .xlsx billing export")

    # Load billing file into session state — skip reload if unchanged
    if raw_file:
        if raw_file.name != st.session_state[SK_RAW_NAME]:
            st.session_state[SK_RAW_DF]            = normalize_columns(read_excel_to_df(raw_file))
            st.session_state[SK_RAW_NAME]          = raw_file.name
            # Reset downstream on new file
            st.session_state[SK_PROCESSED]         = False
            st.session_state[SK_FILTERED_DF]       = None
            st.session_state[SK_SEGREGATED_BYTES]  = None
            st.session_state[SK_UPDATED_REF_BYTES] = None
        st.success(f"✓ {raw_file.name}")
    else:
        st.info("Upload your raw billing file above to continue.")
        st.stop()

    ref_df: pd.DataFrame = st.session_state[SK_REF_DF]
    raw_df: pd.DataFrame = st.session_state[SK_RAW_DF]

    st.divider()

        # STEP 2 — SANITY CHECK
        step_header(2, "Sanity Check", "Scanning for qualifying billing rows.")

    subject_col = find_column(raw_df, SUBJECT_COLUMN_CANDIDATES)

    if subject_col is None:
        st.error(
            "Could not detect a subject/description column in the raw billing file. "
            f"Expected one of: {', '.join(SUBJECT_COLUMN_CANDIDATES)}."
        )
        st.stop()

    filtered_df = filter_billing_rows(raw_df, subject_col, BILLING_KEYWORDS)
    st.session_state[SK_FILTERED_DF] = filtered_df

    with st.container(border=True):
        kw_display = "  ·  ".join(f'"{k}"' for k in BILLING_KEYWORDS)
        st.caption(f"Keywords scanned — {kw_display}   |   Column used: **{subject_col}**")

        if filtered_df.empty:
            st.error("No matching rows found. Check that your billing file contains the expected keywords.")
            st.stop()

        sc1, sc2 = st.columns([1, 3])
        sc1.metric("Qualifying Rows", f"{len(filtered_df):,}")
        with sc2:
            with st.expander("Preview matching rows", expanded=False):
                st.dataframe(filtered_df, use_container_width=True, height=220)

    st.divider()

        # STEP 3 — SYNC PREVIEW
        step_header(3, "Sync Preview", "Comparing billing IDs against the master reference.")

    raw_id_col   = find_column(filtered_df, ID_COLUMN_CANDIDATES)
    raw_name_col = find_column(filtered_df, NAME_COLUMN_CANDIDATES)
    ref_id_col   = find_column(ref_df,      ID_COLUMN_CANDIDATES)
    ref_name_col = find_column(ref_df,      NAME_COLUMN_CANDIDATES)

    missing_required = [
        label for col, label in [
            (raw_id_col,   "ID column (billing file)"),
            (raw_name_col, "Name column (billing file)"),
            (ref_id_col,   "ID column (reference file)"),
            (ref_name_col, "Name column (reference file)"),
        ] if col is None
    ]
    if missing_required:
        st.error(f"Required columns not found: {', '.join(missing_required)}")
        st.stop()

    new_ids, missing_ids = compare_employees(filtered_df, ref_df, raw_id_col, ref_id_col)
    st.session_state[SK_NEW_EMPLOYEES]     = list(new_ids)
    st.session_state[SK_MISSING_EMPLOYEES] = list(missing_ids)

    with st.container(border=True):
        m1, m2 = st.columns(2, gap="medium")
        m1.metric("New Employees", len(new_ids),
                  help="Present in billing but absent from the reference file.")
        m2.metric("Missing Employees", len(missing_ids),
                  help="Present in the reference file but absent from billing.")

        if new_ids:
            new_preview = (
                filtered_df[filtered_df[raw_id_col].astype(str).str.strip().isin(new_ids)]
                [[raw_id_col, raw_name_col]].drop_duplicates()
            )
            with st.expander(f"New employees — {len(new_ids)} record(s)", expanded=False):
                st.dataframe(new_preview, use_container_width=True, height=200)

        if missing_ids:
            missing_preview = (
                ref_df[ref_df[ref_id_col].astype(str).str.strip().isin(missing_ids)]
                [[ref_id_col, ref_name_col]].drop_duplicates()
            )
            with st.expander(f"Missing employees — {len(missing_ids)} record(s)", expanded=False):
                st.dataframe(missing_preview, use_container_width=True, height=200)

    st.divider()

        # STEP 4 — EXECUTE PROCESSING
        step_header(4, "Process & Segregate",
                "Updates the reference, merges entities, then splits billing into sheets.")

    with st.container(border=True):
        run = st.button(
            "Run Processing",
            type="primary",
            use_container_width=True,
            key="run_btn",
        )

        if run:
            with st.spinner("Working…"):
                ref_entity_col = find_column(ref_df, ENTITY_COLUMN_CANDIDATES)
                if ref_entity_col is None:
                    st.error(
                        "Could not find an Entity column in the reference file. "
                        f"Expected one of: {', '.join(ENTITY_COLUMN_CANDIDATES)}."
                    )
                    st.stop()

                # 4a — Update reference in-memory
                updated_ref = update_reference(
                    ref_df, filtered_df,
                    ref_id_col, ref_name_col, ref_entity_col,
                    raw_id_col, raw_name_col,
                    new_ids, missing_ids,
                )
                st.session_state[SK_UPDATED_REF_DF] = updated_ref

                # 4b — Merge entity column into billing rows
                billing = merge_entity(
                    filtered_df, updated_ref,
                    raw_id_col, ref_id_col, ref_entity_col,
                )

                # 4c — Segregate into sheets
                sheets = segregate_billing(billing, raw_name_col)

                if not sheets:
                    st.error("No data to segregate. Please check your input files.")
                    st.stop()

                # 4d — Serialise to bytes
                st.session_state[SK_SEGREGATED_BYTES]  = multi_sheet_excel_bytes(sheets)
                st.session_state[SK_UPDATED_REF_BYTES] = df_to_excel_bytes(updated_ref, "Reference")
                st.session_state[SK_PROCESSED]         = True

            sheet_names = list(sheets.keys())
            st.success(
                f"Done — {len(sheet_names)} sheet(s) created: "
                + ", ".join(f"**{n}**" for n in sheet_names)
            )
            st.balloons()

        elif st.session_state[SK_PROCESSED]:
            st.success("Already processed. Download your files below, or re-run to refresh.")

    st.divider()

    
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
                st.caption("Multi-sheet workbook, one tab per entity")
            with d2:
                st.download_button(
                    label=f"↓  {DOWNLOAD_REFERENCE_LABEL}",
                    data=st.session_state[SK_UPDATED_REF_BYTES],
                    file_name=DOWNLOAD_REFERENCE_FILENAME,
                    mime=XLSX_MIME,
                    use_container_width=True,
                )
                st.caption("Save this over data/reference.xlsx to keep your master list current")


# TAB 2 — SESSION REFERENCE VIEWER

with tab2:
    st.markdown("## Reference Viewer")
    st.caption("Live view of the master reference data held in memory for this session.")
    st.divider()

    ref_to_show: pd.DataFrame | None = st.session_state[SK_UPDATED_REF_DF]

    if ref_to_show is None:
        st.info("No reference file loaded yet. Upload your Master Reference File in the Billing Processor tab.")
    else:
        with st.container(border=True):
            rv1, rv2, rv3 = st.columns(3, gap="medium")
            rv1.metric("Total Records",       f"{len(ref_to_show):,}")
            rv2.metric("New Employees Added", f"{len(st.session_state[SK_NEW_EMPLOYEES]):,}")
            rv3.metric("Employees Removed",   f"{len(st.session_state[SK_MISSING_EMPLOYEES]):,}")

        st.divider()
        st.dataframe(ref_to_show, use_container_width=True, height=520)