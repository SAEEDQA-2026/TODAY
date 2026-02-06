import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from hijri_converter import Gregorian
import io
import os
import streamlit.components.v1 as components

# --- 1. الإعدادات وتصنيفات النظام ---
st.set_page_config(page_title="المستشار المالي 2026 - بداية جديدة", layout="wide")

DB_FILE = "finance_master_2026.csv"

DAILY_CATS = ["بنزين", "ماء", "الزيت", "الغاز", "السيارة", "تصليح", "فواتير", "مقاضي البيت", "مقاهي", "خضاروفواكهه", "مخالفات", "مقاضي البنات", "المستشفيات والصيدليات", "مطاعم", "ترفيه وحجوزات", "خدمات خارجية", "قطات", "عناية", "أخرى"]
INCOME_CATS = ["الراتب", "حساب المواطن", "الدعم السكني", "الاسهم", "مسترجعات", "حقوق خاصة", "العمالة", "انتداب", "اركابات", "أخرى"]
FIXED_CATS = ["القرض الشخصي", "القرض العقاري", "امي", "كفالة", "الاعاشة", "قرض شخصي", "القرض"]

# --- 2. نظام الحماية (33550) ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align:center;'>🔒 نظام الإدارة المالية 2026</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        pwd = st.text_input("أدخل رمز الدخول", type="password")
        if pwd == "33550":
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

# --- 3. محرك الميزانية (قاعدة 27 المرنة) ---
def get_salary_day(year, month):
    try:
        t_27 = date(int(year), int(month), 27)
        wd = t_27.weekday() # 4=Friday, 5=Saturday
        if wd == 4: return 26 # الجمعة يبدأ 26
        if wd == 5: return 28 # السبت يبدأ 28
        return 27
    except: return 27

def get_fiscal_cycle(dt):
    if pd.isna(dt) or not hasattr(dt, 'year'): return "None"
    sd = get_salary_day(dt.year, dt.month)
    if dt.day >= sd:
        target = dt + pd.DateOffset(months=1)
        return target.strftime("%m-%Y")
    return dt.strftime("%m-%Y")

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['التاريخ'] = pd.to_datetime(df['التاريخ'], errors='coerce')
        # فلترة البيانات لتبدأ من ميزانية 2026 فقط (أي تاريخ بعد 2025-12-25)
        df = df[df['التاريخ'] >= '2025-12-26']
        df['المبلغ'] = pd.to_numeric(df['المبلغ'], errors='coerce').fillna(0)
        return df.dropna(subset=['التاريخ']).reset_index(drop=True)
    return pd.DataFrame(columns=['التاريخ', 'اليوم', 'النوع', 'التصنيف', 'المبلغ', 'التفاصيل'])

def save_data(df):
    df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')

if 'df' not in st.session_state:
    st.session_state.df = load_data()

def get_hijri():
    today = date.today()
    h = Gregorian(today.year, today.month, today.day).to_hijri()
    days = {"Saturday": "السبت", "Sunday": "الأحد", "Monday": "الإثنين", "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء", "Thursday": "الخميس", "Friday": "الجمعة"}
    return days.get(today.strftime("%A"), ""), f"{today.year}/{today.month:02d}/{today.day:02d} | {h.year}/{h.month:02d}/{h.day:02d}"

# --- 4. الهيدر والساعة الحية ---
d_name, d_full = get_hijri()
st.markdown(f"""
    <div style="background-color:#0f172a; padding:20px; border-radius:15px; text-align:center; color:white; border-bottom: 5px solid #3b82f6;">
        <h1 style="margin:0; font-size: 55px; font-weight: 900;">{d_name}</h1>
        <div id="live_clock_2026" style="font-size: 45px; color: #3b82f6; font-weight: bold; font-family: monospace; margin: 10px 0;">00:00:00</div>
        <h3 style="margin:0; opacity:0.8;">{d_full}</h3>
    </div>
""", unsafe_allow_html=True)

components.html("""
    <script>
    function update() {
        const now = new Date();
        window.parent.document.getElementById('live_clock_2026').innerHTML = now.toLocaleTimeString('en-GB', { hour12: false });
    }
    setInterval(update, 1000); update();
    </script>
""", height=0)

# --- 5. معالجة البيانات ---
df = st.session_state.df
if not df.empty:
    df['دورة_الميزانية'] = df['التاريخ'].apply(get_fiscal_cycle)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 الرئيسية 2026", "🛒 مصروف يومي", "💰 دخل وثوابت", "🔄 المقارنات", "⚙️ السجلات والإدارة"])

# --- Tab 1: الرئيسية ---
with tab1:
    if not df.empty:
        # حساب المتبقي الصافي لعام 2026
        t_in_2026 = df[df['النوع'].isin(['دخل', 'الدخل'])]['المبلغ'].sum()
        t_out_2026 = df[~df['النوع'].isin(['دخل', 'الدخل'])]['المبلغ'].sum()
        net_2026 = t_in_2026 - t_out_2026

        cycles = sorted([c for c in df['دورة_الميزانية'].unique() if c.endswith("2026")], key=lambda x: datetime.strptime(x, "%m-%Y"), reverse=True)
        if not cycles:
             st.info("لا توجد دورات مسجلة لعام 2026 بعد. ابدأ بإدخال البيانات.")
             st.stop()
             
        sel_cycle = st.selectbox("📅 اختر شهر الميزانية:", cycles)
        curr_df = df[df['دورة_الميزانية'] == sel_cycle]
        
        m_inc = curr_df[curr_df['النوع'].isin(['دخل', 'الدخل'])]['المبلغ'].sum()
        m_exp = curr_df[~curr_df['النوع'].isin(['دخل', 'الدخل'])]['المبلغ'].sum()
        m_surplus = m_inc - m_exp
        
        st.write("### 💰 الميزانية الحالية")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("إجمالي دخل الشهر", f"{m_inc:,.2f}")
        m2.metric("مصروفات الشهر", f"{m_exp:,.2f}")
        m3.metric("المتبقي الشهري", f"{m_surplus:,.2f}")
        m4.metric("📈 صافي مدخرات 2026", f"{net_2026:,.2f}")

        st.divider()
        st.write("### 🛠️ الخدمات والهدف المالي")
        cw, cg, co, cl = st.columns(4)
        
        w_val = curr_df[curr_df['التصنيف'] == 'ماء']['المبلغ'].sum()
        g_val = curr_df[curr_df['التصنيف'] == 'الغاز']['المبلغ'].sum()
        o_val = curr_df[curr_df['التصنيف'] == 'الزيت']['المبلغ'].sum()

        cw.markdown(f"<div style='text-align:center; padding:15px; background:#1e293b; border-radius:15px; border:2px solid #3b82f6;'><h1>💧</h1><h3>الماء</h3><h2>{w_val:,.2f}</h2></div>", unsafe_allow_html=True)
        cg.markdown(f"<div style='text-align:center; padding:15px; background:#1e293b; border-radius:15px; border:2px solid #3b82f6;'><h1>🔥</h1><h3>الغاز</h3><h2>{g_val:,.2f}</h2></div>", unsafe_allow_html=True)
        co.markdown(f"<div style='text-align:center; padding:15px; background:#1e293b; border-radius:15px; border:2px solid #3b82f6;'><h1>🛢️</h1><h3>الزيت</h3><h2>{o_val:,.2f}</h2></div>", unsafe_allow_html=True)
        
        with cl:
            goal = st.number_input("🎯 هدف الادخار:", value=5000, step=500)
            color = "#10b981" if m_surplus >= goal else "#ef4444"
            st.markdown(f"<div style='text-align:center; padding:15px; background:#0f172a; border-radius:15px; border:3px solid {color};'><h3>تحقيق الهدف</h3><h2 style='color:{color};'>{m_surplus:,.2f} / {goal:,.2f}</h2></div>", unsafe_allow_html=True)

        st.divider()
        st.write(f"### 📊 تحليل مصروفات {sel_cycle}")
        c_pie, c_tab = st.columns([1, 1.5])
        with c_pie:
            exp_df = curr_df[~curr_df['النوع'].isin(['دخل', 'الدخل'])]
            if not exp_df.empty:
                st.plotly_chart(px.pie(exp_df, values='المبلغ', names='التصنيف', hole=0.5), use_container_width=True)
        with c_tab:
            st.write("📝 **سجل عمليات الشهر المختار:**")
            st.dataframe(curr_df[['التاريخ', 'التصنيف', 'المبلغ', 'النوع', 'التفاصيل']].sort_values('التاريخ', ascending=False), use_container_width=True)
    else:
        st.info("النظام جاهز لعام 2026. ابدأ بإدخال مصروفاتك الأولى.")

# --- Tab 5: السجلات والإدارة (التعديل والدمج) ---
with tab5:
    st.subheader("⚙️ إدارة بيانات 2026")
    col_u, col_d = st.columns(2)
    with col_u:
        up = st.file_uploader("📥 استيراد بيانات جديدة لعام 2026", type=['csv', 'xlsx'])
        if up:
            n_df = pd.read_csv(up) if up.name.endswith('.csv') else pd.read_excel(up)
            st.session_state.df = pd.concat([st.session_state.df, n_df], ignore_index=True)
            st.session_state.df['التاريخ'] = pd.to_datetime(st.session_state.df['التاريخ'], errors='coerce')
            st.session_state.df = st.session_state.df[st.session_state.df['التاريخ'] >= '2025-12-26']
            save_data(st.session_state.df); st.success("تم الاستيراد والدمج!"); st.rerun()
    with col_d:
        st.download_button("📤 تصدير بيانات 2026", df.to_csv(index=False).encode('utf-8-sig'), "finance_2026.csv")

    st.divider()
    st.markdown("### 📝 محرر السجلات الشامل")
    edited = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)
    if st.button("💾 تأكيد وحفظ كافة التعديلات"):
        st.session_state.df = edited
        save_data(edited); st.success("تم الحفظ!"); st.rerun()

# تبويبات الإدخال اليدوي
with tab2:
    with st.form("d_2026"):
        st.subheader("🛒 تسجيل مصروف جديد")
        c1, c2, c3, c4 = st.columns(4)
        d_date = c1.date_input("التاريخ", date.today())
        d_cat = c2.selectbox("التصنيف", DAILY_CATS)
        d_amt = c3.number_input("المبلغ", min_value=0.0)
        d_not = c4.text_input("التفاصيل")
        if st.form_submit_button("حفظ"):
            new_r = pd.DataFrame([{"التاريخ": pd.to_datetime(d_date), "اليوم": d_name, "النوع": "مصروف", "التصنيف": d_cat, "المبلغ": d_amt, "التفاصيل": d_not}])
            st.session_state.df = pd.concat([st.session_state.df, new_r], ignore_index=True); save_data(st.session_state.df); st.rerun()

with tab3:
    ci, cf = st.columns(2)
    with ci:
        with st.form("i_2026"):
            st.write("💰 تسجيل دخل")
            i_cat = st.selectbox("المصدر", INCOME_CATS); i_amt = st.number_input("المبلغ")
            if st.form_submit_button("إضافة دخل"):
                new_r = pd.DataFrame([{"التاريخ": pd.to_datetime(date.today()), "اليوم": d_name, "النوع": "دخل", "التصنيف": i_cat, "المبلغ": i_amt}])
                st.session_state.df = pd.concat([st.session_state.df, new_r], ignore_index=True); save_data(st.session_state.df); st.rerun()
    with cf:
        with st.form("f_2026"):
            st.write("🏠 مصروف ثابت")
            f_cat = st.selectbox("النوع", FIXED_CATS); f_amt = st.number_input("المبلغ")
            if st.form_submit_button("حفظ الثابت"):
                new_r = pd.DataFrame([{"التاريخ": pd.to_datetime(date.today()), "اليوم": d_name, "النوع": "مصروفات ثابتة", "التصنيف": f_cat, "المبلغ": f_amt}])
                st.session_state.df = pd.concat([st.session_state.df, new_r], ignore_index=True); save_data(st.session_state.df); st.rerun()