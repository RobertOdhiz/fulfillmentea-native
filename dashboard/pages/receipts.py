import streamlit as st
import sys
import os
import base64
import html as html_lib
from io import BytesIO
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from typing import Optional

# PDF
from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas

import streamlit.components.v1 as components

# Add dashboard root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.client import api_client  # your client


# -------------------- Utilities --------------------
def fmt_date(d: Optional[str]) -> str:
    """Format a datetime string or object into a readable local string.
       Accepts ISO strings or datetime objects."""
    if d is None:
        return ""
    if isinstance(d, str):
        try:
            # parse plain ISO (assumes UTC if naive)
            dt = datetime.fromisoformat(d)
        except Exception:
            try:
                # fallback: attempt generic parse
                dt = datetime.strptime(d, "%Y-%m-%dT%H:%M:%S.%f")
            except Exception:
                return d
    elif isinstance(d, datetime):
        dt = d
    else:
        return str(d)
    # Display in 'YYYY-MM-DD HH:MM:SS' (UTC)
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def fmt_money(amount: float, currency: str = "USD") -> str:
    """Format currency with 2 decimals and currency code"""
    q = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{q:,} {currency}"


def safe(val):
    """Escape for HTML"""
    return html_lib.escape("" if val is None else str(val))


# -------------------- Receipt HTML and PDF --------------------
def receipt_to_html(receipt: dict) -> str:
    """Create HTML string for receipt sized for 80mm receipt printers."""
    # Extract fields; be defensive with missing keys
    parcel = receipt.get("parcel", {})
    payments = parcel.get("payments", []) if parcel else []
    sender_name = safe(parcel.get("sender_name"))
    sender_phone = safe(parcel.get("sender_phone"))
    sender_country = safe(parcel.get("sender_country_code") or "")
    receiver_name = safe(parcel.get("receiver_name"))
    receiver_phone = safe(parcel.get("receiver_phone"))
    receiver_country = safe(parcel.get("receiver_country_code") or "")
    parcel_type = safe(parcel.get("parcel_type"))
    value = fmt_money(parcel.get("value_amount", 0.0), parcel.get("value_currency", receipt.get("currency", "USD")))
    paid = fmt_money(parcel.get("amount_paid_amount", 0.0), parcel.get("amount_paid_currency", receipt.get("currency", "USD")))

    receipt_number = safe(receipt.get("receipt_number"))
    generated = fmt_date(receipt.get("generated_at"))
    printed = "Yes" if receipt.get("printed") else "No"

    # Payments lines
    payments_html = ""
    if payments:
        for p in payments:
            amt = fmt_money(p.get("amount", 0.0), p.get("currency", ""))
            method = safe(p.get("method"))
            paid_at = fmt_date(p.get("paid_at"))
            payments_html += f"<tr><td>{method}:</td><td style='text-align:right'>{amt}</td></tr><tr><td class='small'>Ref:</td><td class='small' style='text-align:right'>{safe(p.get('reference'))} {paid_at}</td></tr>"

    html_content = f"""<!doctype html>
<html><head>
<meta charset="utf-8"/>
<title>Receipt {receipt_number}</title>
<style>
  @page {{ size: 80mm auto; margin: 5mm; }}
  body {{ font-family: Arial, Helvetica, sans-serif; width:80mm; margin:0; padding:6px; font-size:12px; color:#000; }}
  .center {{ text-align:center; }}
  .bold {{ font-weight:700; }}
  .small {{ font-size:10px; color:#444; }}
  hr {{ border:none; border-top:1px dashed #000; margin:8px 0; }}
  table {{ width:100%; border-collapse:collapse; }}
  td {{ padding:2px 0; vertical-align:top; }}
  .right {{ text-align:right; }}
  .header h2 {{ margin:0; font-size:14px; }}
</style>
</head><body>
  <div class="center header">
    <h2>My Company / Store</h2>
    <div class="small">Address · Phone</div>
  </div>
  <hr/>

  <table>
    <tr><td class="bold">Receipt No:</td><td class="right">{receipt_number}</td></tr>
    <tr><td class="bold">Generated:</td><td class="right">{generated}</td></tr>
    <tr><td class="bold">Printed:</td><td class="right">{printed}</td></tr>
  </table>

  <hr/>
  <div class="bold">Sender</div>
  <table>
    <tr><td>Name:</td><td class="right">{sender_name}</td></tr>
    <tr><td>Phone:</td><td class="right">{sender_phone} {sender_country}</td></tr>
  </table>

  <hr/>
  <div class="bold">Receiver</div>
  <table>
    <tr><td>Name:</td><td class="right">{receiver_name}</td></tr>
    <tr><td>Phone:</td><td class="right">{receiver_phone} {receiver_country}</td></tr>
  </table>

  <hr/>
  <div class="bold">Parcel</div>
  <table>
    <tr><td>Type:</td><td class="right">{parcel_type}</td></tr>
    <tr><td>Declared Value:</td><td class="right">{value}</td></tr>
    <tr><td>Amount Paid:</td><td class="right">{paid}</td></tr>
  </table>

  <hr/>
  <div class="bold">Payments</div>
  <table>
    {payments_html or '<tr><td class="small">No payment records</td><td></td></tr>'}
  </table>

  <hr/>
  <div class="center small">Thank you for your business!<br/>Powered by Your App</div>
</body></html>"""
    return html_content


def create_receipt_pdf_bytes(receipt: dict) -> bytes:
    """Generate a simple PDF representation of the receipt (reportlab)."""
    parcel = receipt.get("parcel", {}) or {}
    sender_name = parcel.get("sender_name", "")
    sender_phone = parcel.get("sender_phone", "")
    receiver_name = parcel.get("receiver_name", "")
    receiver_phone = parcel.get("receiver_phone", "")
    parcel_type = parcel.get("parcel_type", "")
    value = fmt_money(parcel.get("value_amount", 0.0), parcel.get("value_currency", receipt.get("currency", "USD")))
    paid = fmt_money(parcel.get("amount_paid_amount", 0.0), parcel.get("amount_paid_currency", receipt.get("currency", "USD")))
    receipt_number = receipt.get("receipt_number", "")
    generated = fmt_date(receipt.get("generated_at"))
    printed = "Yes" if receipt.get("printed") else "No"

    width_mm = 80
    height_mm = 220
    width, height = (width_mm * mm, height_mm * mm)

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(width, height))
    x = 8 * mm
    y = height - 8 * mm
    def draw(text, bold=False, size=10):
        nonlocal y
        if bold:
            c.setFont("Helvetica-Bold", size)
        else:
            c.setFont("Helvetica", size)
        c.drawString(x, y, text)
        y -= (size + 2)

    draw("My Company / Store", bold=True, size=12)
    draw("Address · Phone", size=9)
    y -= 4
    draw("-" * 40, size=8)
    draw(f"Receipt No: {receipt_number}", size=9)
    draw(f"Generated: {generated}", size=8)
    draw(f"Printed: {printed}", size=8)
    draw("-" * 40, size=8)
    draw("Sender", bold=True, size=10)
    draw(f"Name: {sender_name}")
    draw(f"Phone: {sender_phone}")
    draw("-" * 40, size=8)
    draw("Receiver", bold=True, size=10)
    draw(f"Name: {receiver_name}")
    draw(f"Phone: {receiver_phone}")
    draw("-" * 40, size=8)
    draw("Parcel", bold=True, size=10)
    draw(f"Type: {parcel_type}")
    draw(f"Declared Value: {value}")
    draw(f"Amount Paid: {paid}")
    draw("-" * 40, size=8)
    draw("Payments", bold=True, size=10)
    payments = parcel.get("payments", []) or []
    if payments:
        for p in payments:
            draw(f"{p.get('method')}: {fmt_money(p.get('amount', 0.0), p.get('currency', ''))}", size=9)
            if p.get("reference"):
                draw(f"Ref: {p.get('reference')}", size=8)
    else:
        draw("No payment records", size=9)
    y -= 6
    draw("-" * 40, size=8)
    draw("Thank you for your business!", size=9)
    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()


# -------------------- Page: Render receipts --------------------
def render_receipts(token: str):
    st.title("Receipts Management")

    # ensure session state for persistence across reruns
    ss = st.session_state
    if "last_receipt_html" not in ss:
        ss["last_receipt_html"] = None
    if "last_receipt_pdf" not in ss:
        ss["last_receipt_pdf"] = None
    if "open_action" not in ss:
        ss["open_action"] = None  # tuple(action, html) where action in {"open","print","bulk_print"}

    try:
        parcels = api_client.get("/parcels", token) or []
    except Exception as e:
        st.error(f"Failed to fetch parcels: {e}")
        parcels = []

    # ---------- Generate form ----------
    st.subheader("Generate New Receipt")
    with st.form("generate_receipt"):
        col1, col2 = st.columns(2)
        with col1:
            parcel_id = st.text_input("Parcel ID")
        with col2:
            st.write("")
            st.caption("Enter parcel ID to generate a receipt")
        submitted = st.form_submit_button("Generate Receipt")

    if submitted and parcel_id:
        try:
            receipt = api_client.post(f"/payments/{parcel_id}/receipt", {}, token)
            # attach parcel details if API doesn't include them, attempt to find parcel locally
            # (some APIs return full receipt + parcel; if not, find parcel)
            if not receipt.get("parcel"):
                matched = next((p for p in parcels if p.get("id") == parcel_id), None)
                if matched:
                    # copy payments into parcel for consistent display
                    matched_payments = matched.get("payments", [])
                    matched["payments"] = matched_payments
                    receipt["parcel"] = matched
            # store HTML and PDF bytes in session state so buttons survive reruns
            html_fragment = receipt_to_html(receipt)
            ss["last_receipt_html"] = html_fragment
            ss["last_receipt_pdf"] = create_receipt_pdf_bytes(receipt)
            ss["last_receipt_meta"] = receipt  # keep raw for downloads etc.
            st.success(f"Receipt {receipt.get('receipt_number')} generated.")
            # show preview
            components.html(html_fragment, height=380, scrolling=True)

            # actions (open / print / download)
            c1, c2, c3 = st.columns([1, 1, 1])
            if c1.button("Open Receipt in New Tab"):
                ss["open_action"] = ("open", ss["last_receipt_html"])
            if c2.button("Print Receipt (POS)"):
                ss["open_action"] = ("print", ss["last_receipt_html"])
            if c3.button("Download PDF"):
                # show immediate download button using stored pdf bytes
                st.download_button("Download Receipt PDF",
                                   data=ss["last_receipt_pdf"],
                                   file_name=f"receipt_{receipt.get('receipt_number','')}.pdf",
                                   mime="application/pdf")
        except Exception as e:
            st.error(f"Failed to generate receipt: {e}")

    # ---------- Receipt History ----------
    st.subheader("Receipt History")
    if parcels:
        parcels_with_receipts = [p for p in parcels if p.get("receipt")]
        if parcels_with_receipts:
            for p in parcels_with_receipts:
                r = p["receipt"]
                with st.expander(f"Receipt {r.get('receipt_number')} — Parcel {r.get('parcel_id')}"):
                    cols = st.columns([3, 1, 1, 1])
                    with cols[0]:
                        st.markdown(f"**Amount:** {fmt_money(r.get('total_amount',0), r.get('currency'))}  \n**Generated:** {fmt_date(r.get('generated_at'))}")
                        # build html on demand (include parcel details from p)
                        full_receipt = dict(r)
                        full_receipt["parcel"] = p
                        html_frag = receipt_to_html(full_receipt)
                        components.html(html_frag, height=260, scrolling=True)

                    # Print button
                    with cols[1]:
                        if st.button("Print", key=f"print_{r.get('receipt_number')}"):
                            ss["open_action"] = ("print", html_frag)
                    # Open
                    with cols[2]:
                        if st.button("Open", key=f"open_{r.get('receipt_number')}"):
                            ss["open_action"] = ("open", html_frag)
                    # PDF download
                    with cols[3]:
                        if st.button("PDF", key=f"pdf_{r.get('receipt_number')}"):
                            pdfb = create_receipt_pdf_bytes(full_receipt)
                            st.download_button("Download PDF",
                                               data=pdfb,
                                               file_name=f"receipt_{r.get('receipt_number')}.pdf",
                                               mime="application/pdf")
            # Bulk print
            st.subheader("Bulk Print")
            if st.button("Print All Receipts"):
                # combine all receipts into one HTML and set action to bulk_print
                combined = "<html><head><meta charset='utf-8'><style>@page{size:80mm auto;margin:5mm;}body{font-family:Arial;width:80mm;margin:0;padding:6px;}hr{border:none;border-top:1px dashed #000;margin:8px 0;}</style></head><body>"
                for p in parcels_with_receipts:
                    full_receipt = dict(p["receipt"])
                    full_receipt["parcel"] = p
                    single = receipt_to_html(full_receipt)
                    # extract only body inner content
                    if "<body" in single:
                        inner = single.split("<body", 1)[1].split(">", 1)[1].rsplit("</body>", 1)[0]
                    else:
                        inner = single
                    combined += inner + "<div style='page-break-after:always'></div>"
                combined += "</body></html>"
                ss["open_action"] = ("bulk_print", combined)
        else:
            st.info("No receipts generated yet.")
    else:
        st.info("No parcels found.")

    # ---------- Statistics ----------
    if parcels:
        st.subheader("Receipt Statistics")
        total_parcels = len(parcels)
        receipts_count = sum(1 for p in parcels if p.get("receipt"))
        receipt_rate = (receipts_count / total_parcels * 100) if total_parcels else 0
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Parcels", total_parcels)
        c2.metric("Receipts Generated", receipts_count)
        c3.metric("Receipt Rate", f"{receipt_rate:.1f}%")

    # ---------- Handle open / print actions (render a transient components.html which opens a new window) ----------
    if ss.get("open_action"):
        action, html_payload = ss["open_action"]
        # build JS that opens a new window, writes the HTML and optionally triggers print
        # we base64 encode the content to avoid quote escaping
        b64 = base64.b64encode(html_payload.encode("utf-8")).decode()
        if action == "open":
            js = f"""
            <script>
            const html = atob("{b64}");
            const w = window.open("", "_blank");
            if(!w) {{
              alert("Popup blocked. Allow popups for this site to open the receipt.");
            }} else {{
              w.document.open();
              w.document.write(html);
              w.document.close();
            }}
            </script>
            """
        elif action == "print":
            # wait a bit then print
            js = f"""
            <script>
            const html = atob("{b64}");
            const w = window.open("", "_blank");
            if(!w) {{
              alert("Popup blocked. Allow popups for this site to open the receipt.");
            }} else {{
              w.document.open();
              w.document.write(html + '<script>window.onload=function(){{setTimeout(()=>window.print(),250);}};<\\/script>');
              w.document.close();
            }}
            </script>
            """
        elif action == "bulk_print":
            js = f"""
            <script>
            const html = atob("{b64}");
            const w = window.open("", "_blank");
            if(!w) {{
              alert("Popup blocked. Allow popups for this site to open the receipt.");
            }} else {{
              w.document.open();
              w.document.write(html + '<script>window.onload=function(){{setTimeout(()=>window.print(),350);}};<\\/script>');
              w.document.close();
            }}
            </script>
            """
        else:
            js = "<script>console.warn('unknown action');</script>"

        # Render JS. Use reasonable height so browser executes it.
        components.html(js, height=300)
        # clear the action to avoid repeating
        ss["open_action"] = None


if __name__ == "__main__":
    # demo token retrieval (replace as necessary)
    demo_token = st.secrets.get("API_TOKEN", "") if hasattr(st, "secrets") else ""
    render_receipts(demo_token)
