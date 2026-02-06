import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from hijri_converter import Gregorian
import io
import os
import streamlit.components.v1 as components

# --- 1. الإعدادات وتصنيفات النظام ---
st.set_page_config(page_title="المستشار المالي v27", layout="wide")

DB_FILE = "finance_master_data_v27.csv"

# التصنيفات
DAILY_CATS = ["بنزين", "ماء", "الزيت", "الغاز", "السيارة", "تصليح", "فواتير", "مقاضي البيت", "مقاهي", "خضاروفواكهه", "مخالفات", "مقاضي البنات", "المستشفيات والصيدليات", "مطاعم", "ترفيه وحجوزات", "خدمات خارجية", "قطات", "عناية", "أخرى"]
INCOME_CATS = ["الراتب", "حساب المواطن", "الدعم السكني", "الاسهم", "مسترجعات", "حقوق خاصة", "العمالة", "انتداب", "اركابات", "أخرى"]
FIXED_CATS = ["القرض الشخصي", "القرض العقاري", "امي", "كفالة", "الاعاشة", "قرض شخصي", "القرض"]

# --- 2. نظام الحماية (33550) ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align:center;'>🔒 نظام الإدارة المالية المحمي</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        pwd = st.text_input("أدخل رمز الدخول واضغط Enter", type="password")
        if pwd == "33550":
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

# --- 3. محرك الميزانية (قاعدة 27 المرنة) ---
def get_salary_day(year, month):
    try:
        t_27 = date(int(year), int(month), 27)
        wd = t_27.weekday() 
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
        <div id="live_clock_v27" style="font-size: 45px; color: #3b82f6; font-weight: bold; font-family: monospace; margin: 10px 0;">00:00:00</div>
        <h3 style="margin:0; opacity:0.8;">{d_full}</h3>
    </div>
""", unsafe_allow_html=True)

components.html("""
    <script>
    function update() {
        const now = new Date();
        window.parent.document.getElementById('live_clock_v27').innerHTML = now.toLocaleTimeString('en-GB', { hour12: false });
    }
    setInterval(update, 1000); update();
    </script>
""", height=0)

# --- 5. منطق البيانات والتبويبات ---
df = st.session_state.df
if not df.empty:
    df['دورة_الميزانية'] = df['التاريخ'].apply(get_fiscal_cycle)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 الرئيسية والشهرية", "🛒 مصروف يومي", "💰 دخل وثوابت", "🔄 مركز المقارنات", "⚙️ السجلات والإدارة"])

# --- Tab 1: الرئيسية (كل المتطلبات في مكان واحد) ---
with tab1:
    if not df.empty:
        # حساب المتبقي العام الصافي
        t_in_all = df[df['النوع'].isin(['دخل', 'الدخل'])]['المبلغ'].sum()
        t_out_all = df[~df['النوع'].isin(['دخل', 'الدخل'])]['المبلغ'].sum()
        actual_general_surplus = t_in_all - t_out_all

        cycles = sorted([c for c in df['دورة_الميزانية'].unique() if c != "None"], key=lambda x: datetime.strptime(x, "%m-%Y"), reverse=True)
        sel_cycle = st.selectbox("📅 اختر الشهر للعرض والتحليل الفوري:", cycles)
        curr_df = df[df['دورة_الميزانية'] == sel_cycle]
        
        # موازين الدورة الحالية
        m_income = curr_df[curr_df['النوع'].isin(['دخل', 'الدخل'])]['المبلغ'].sum()
        m_expense = curr_df[~curr_df['النوع'].isin(['دخل', 'الدخل'])]['المبلغ'].sum()
        m_surplus = m_income - m_expense
        
        # 1. المقاييس المالية العلوية
        st.write("### 💰 الميزانية الحالية")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("إجمالي الدخل الشهري", f"{m_income:,.2f}")
        m2.metric("المصروفات (ثابتة+يومية)", f"{m_expense:,.2f}")
        m3.metric("المتبقي من الدخل", f"{m_surplus:,.2f}")
        m4.metric("📈 الصافي التراكمي العام", f"{actual_total_surplus if 'actual_total_surplus' in locals() else actual_general_surplus:,.2f}")

        st.divider()
        # 2. أيقونات الخدمات والهدف الادخاري
        st.write("### 🛠️ الخدمات والضروريات")
        col_w, col_g, col_o, col_goal = st.columns(4)
        
        water_val = curr_df[curr_df['التصنيف'] == 'ماء']['المبلغ'].sum()
        gas_val = curr_df[curr_df['التصنيف'] == 'الغاز']['المبلغ'].sum()
        oil_val = curr_df[curr_df['التصنيف'] == 'الزيت']['المبلغ'].sum()

        with col_w:
            st.markdown(f"<div style='text-align:center; padding:15px; background:#1e293b; border-radius:15px; border:2px solid #3b82f6;'><h1>💧</h1><h3>الماء</h3><h2>{water_val:,.2f}</h2></div>", unsafe_allow_html=True)
            with st.popover("+"):
                date_w = st.date_input("التاريخ", date.today(), key="dw_v27")
                amt_w = st.number_input("المبلغ", min_value=0.0, key="aw_v27")
                not_w = st.text_input("تفاصيل", key="nw_v27")
                if st.button("حفظ الماء", key="bw_v27"):
                    new = pd.DataFrame([{"التاريخ": pd.to_datetime(date_w), "اليوم": d_name, "النوع": "مصروف", "التصنيف": "ماء", "المبلغ": amt_w, "التفاصيل": not_w}])
                    st.session_state.df = pd.concat([st.session_state.df, new], ignore_index=True); save_data(st.session_state.df); st.rerun()

        with col_g:
            st.markdown(f"<div style='text-align:center; padding:15px; background:#1e293b; border-radius:15px; border:2px solid #3b82f6;'><h1>🔥</h1><h3>الغاز</h3><h2>{gas_val:,.2f}</h2></div>", unsafe_allow_html=True)
            with st.popover("+"):
                date_g = st.date_input("التاريخ", date.today(), key="dg_v27")
                amt_g = st.number_input("المبلغ", min_value=0.0, key="ag_v27")
                if st.button("حفظ الغاز", key="bg_v27"):
                    new = pd.DataFrame([{"التاريخ": pd.to_datetime(date_g), "اليوم": d_name, "النوع": "مصروف", "التصنيف": "الغاز", "المبلغ": amt_g}])
                    st.session_state.df = pd.concat([st.session_state.df, new], ignore_index=True); save_data(st.session_state.df); st.rerun()

        with col_o:
            st.markdown(f"<div style='text-align:center; padding:15px; background:#1e293b; border-radius:15px; border:2px solid #3b82f6;'><h1>🛢️</h1><h3>الزيت</h3><h2>{oil_val:,.2f}</h2></div>", unsafe_allow_html=True)
            with st.popover("+"):
                date_o = st.date_input("التاريخ", date.today(), key="do_v27")
                amt_o = st.number_input("المبلغ", min_value=0.0, key="ao_v27")
                if st.button("حفظ الزيت", key="bo_v27"):
                    new = pd.DataFrame([{"التاريخ": pd.to_datetime(date_o), "اليوم": d_name, "النوع": "مصروف", "التصنيف": "الزيت", "المبلغ": amt_o}])
                    st.session_state.df = pd.concat([st.session_state.df, new], ignore_index=True); save_data(st.session_state.df); st.rerun()

        with col_goal:
            goal_target = st.number_input("🎯 هدف الادخار:", value=5000, step=500)
            status_c = "#10b981" if m_surplus >= goal_target else "#ef4444"
            st.markdown(f"<div style='text-align:center; padding:15px; background:#0f172a; border-radius:15px; border:3px solid {status_c};'><h3>تحقيق الهدف</h3><h2 style='color:{status_c};'>{m_surplus:,.2f} / {goal_target:,.2f}</h2></div>", unsafe_allow_html=True)

        st.divider()
        # 3. الرسم البياني وتفاصيل مصروفات الشهر
        st.write("### 📊 تحليل وتفاصيل مصروفات الشهر")
        c_pie, c_table = st.columns([1, 1])
        with c_pie:
            exp_df = curr_df[~curr_df['النوع'].isin(['دخل', 'الدخل'])]
            if not exp_df.empty:
                fig = px.pie(exp_df, values='المبلغ', names='التصنيف', hole=0.5, title=f"تحليل مصاريف {sel_cycle}")
                st.plotly_chart(fig, use_container_width=True)
            else: st.info("لا توجد مصاريف.")
        with c_table:
            st.write("📝 **سجل عمليات الشهر:**")
            st.dataframe(curr_df[['التاريخ', 'التصنيف', 'المبلغ', 'النوع', 'التفاصيل']].sort_values('التاريخ', ascending=False), use_container_width=True)
    else:
        st.info("بانتظار إضافة بياناتك أو استيراد ملفك المالي.")

# --- Tab 4: مركز المقارنات ---
with tab4:
    if not df.empty:
        st.subheader("🔄 مقارنة الأداء المالي التاريخي")
        comp_df = df.copy()
        comp_df['الفئة'] = comp_df['النوع'].apply(lambda x: 'دخل' if x in ['دخل', 'الدخل'] else 'صرف')
        summary = comp_df.pivot_table(index='دورة_الميزانية', columns='الفئة', values='المبلغ', aggfunc='sum').fillna(0)
        
        # التأكد من وجود الأعمدة
        if 'دخل' not in summary.columns: summary['دخل'] = 0
        if 'صرف' not in summary.columns: summary['صرف'] = 0
        summary['الفائض'] = summary['دخل'] - summary['صرف']
        summary = summary.sort_index(key=lambda x: pd.to_datetime(x, format="%m-%Y", errors='coerce'))

        st.plotly_chart(px.bar(summary.reset_index(), x='دورة_الميزانية', y=['دخل', 'صرف'], barmode='group', title="📈 الدخل مقابل الصرف شهرياً"), use_container_width=True)
        st.dataframe(summary.style.format("{:,.2f}"), use_container_width=True)

# --- Tab 5: السجلات والإدارة (الدمج الدائم) ---
with tab5:
    st.subheader("⚙️ إدارة السجلات ودمج الإكسل")
    col_u, col_d = st.columns(2)
    with col_u:
        up = st.file_uploader("📥 استيراد بيانات ودمجها مع سجلاتك (Excel/CSV)", type=['csv', 'xlsx'])
        if up:
            new_data = pd.read_csv(up) if up.name.endswith('.csv') else pd.read_excel(up)
            # دمج وحفظ فوري
            st.session_state.df = pd.concat([st.session_state.df, new_data], ignore_index=True)
            st.session_state.df['التاريخ'] = pd.to_datetime(st.session_state.df['التاريخ'], errors='coerce')
            st.session_state.df = st.session_state.df.dropna(subset=['التاريخ'])
            save_data(st.session_state.df)
            st.success("✅ تم دمج البيانات وحفظها نهائياً كجزء من السجلات الأصلية.")
            st.rerun()
            
    with col_d:
        st.download_button("📤 تصدير قاعدة البيانات (CSV)", df.to_csv(index=False).encode('utf-8-sig'), "finance_master_backup.csv")

    st.divider()
    st.markdown("### 📝 محرر السجلات الشامل (تعديل وحذف)")
    edited = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True, key="master_editor_v27")
    if st.button("💾 تأكيد وحفظ كافة التعديلات"):
        st.session_state.df = edited
        save_data(edited)
        st.success("تم تحديث قاعدة البيانات بنجاح!")
        st.rerun()

# تبويبات الإدخال اليدوي
with tab2:
    with st.form("d_form_v27"):
        st.subheader("🛒 تسجيل مصروف يومي")
        cl1, cl2, cl3, cl4 = st.columns(4)
        d_date = cl1.date_input("التاريخ", date.today())
        d_cat = cl2.selectbox("التصنيف", DAILY_CATS)
        d_amt = cl3.number_input("المبلغ", min_value=0.0)
        d_not = cl4.text_input("التفاصيل")
        if st.form_submit_button("حفظ"):
            new_r = pd.DataFrame([{"التاريخ": pd.to_datetime(d_date), "اليوم": d_name, "النوع": "مصروف", "التصنيف": d_cat, "المبلغ": d_amt, "التفاصيل": d_not}])
            st.session_state.df = pd.concat([st.session_state.df, new_r], ignore_index=True); save_data(st.session_state.df); st.rerun()

with tab3:
    col_i, col_fx = st.columns(2)
    with col_i:
        with st.form("i_form_v27"):
            st.write("💰 تسجيل دخل")
            i_cat = st.selectbox("المصدر", INCOME_CATS); i_amt = st.number_input("المبلغ")
            if st.form_submit_button("إضافة دخل"):
                new_r = pd.DataFrame([{"التاريخ": pd.to_datetime(date.today()), "اليوم": d_name, "النوع": "دخل", "التصنيف": i_cat, "المبلغ": i_amt}])
                st.session_state.df = pd.concat([st.session_state.df, new_r], ignore_index=True); save_data(st.session_state.df); st.rerun()
    with col_fx:
        with st.form("f_form_v27"):
            st.write("🏠 مصروف ثابت")
            f_cat = st.selectbox("النوع", FIXED_CATS); f_amt = st.number_input("المبلغ")
            if st.form_submit_button("حفظ الثابت"):
                new_r = pd.DataFrame([{"التاريخ": pd.to_datetime(date.today()), "اليوم": d_name, "النوع": "مصروفات ثابتة", "التصنيف": f_cat, "المبلغ": f_amt}])
                st.session_state.df = pd.concat([st.session_state.df, new_r], ignore_index=True); save_data(st.session_state.df); st.rerun()