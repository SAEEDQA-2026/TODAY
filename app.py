import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from hijri_converter import Gregorian
import io
import os
import streamlit.components.v1 as components

# --- 1. الإعدادات العامة والتصنيفات ---
st.set_page_config(page_title="تطبيق دورة الراتب الذكية - النسخة الاحترافية", layout="wide")

DB_FILE = "financial_salary_cycle_v4.csv"

DAILY_CATS = ["بنزين", "ماء", "السيارة", "تصليح", "فواتير", "مقاضي البيت", "مقاهي", "خضاروفواكهه", "مخالفات", "مقاضي البنات", "المستشفيات والصيدليات", "مطاعم", "ترفيه وحجوزات", "خدمات خارجية", "قطات", "عناية", "أخرى"]
INCOME_CATS = ["الراتب", "حساب المواطن", "الدعم السكني", "الاسهم", "مسترجعات", "حقوق خاصة", "العمالة", "انتداب", "اركابات", "أخرى"]
FIXED_CATS = ["القرض الشخصي", "القرض العقاري", "امي", "كفالة", "الاعاشة"]
ALL_TYPES = ["دخل", "يومي", "ثابت"]
ALL_EXP_CATS = FIXED_CATS + DAILY_CATS

# --- 2. نظام الحماية ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def check_pwd():
    if st.session_state.get("pwd_field") == "33550":
        st.session_state.authenticated = True
    else:
        st.error("❌ رمز الدخول غير صحيح")

if not st.session_state.authenticated:
    st.markdown("<br><br><h1 style='text-align:center; color:#1e3a8a;'>🔒 نظام الإدارة المالية</h1>", unsafe_allow_html=True)
    col_p1, col_p2, col_p3 = st.columns([1,2,1])
    with col_p2:
        st.text_input("أدخل كلمة المرور واضغط Enter", type="password", key="pwd_field", on_change=check_pwd)
    st.stop()

# --- 3. محرك البيانات والدورة المالية ---
def get_fiscal_month(dt, start_day=27):
    if pd.isna(dt): return "غير محدد"
    if dt.day >= start_day:
        target_date = dt + pd.DateOffset(months=1)
        return target_date.strftime("%Y-%m")
    return dt.strftime("%Y-%m")

def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            df['التاريخ'] = pd.to_datetime(df['التاريخ'], errors='coerce')
            return df.dropna(subset=['التاريخ'])
        except: return pd.DataFrame(columns=['التاريخ', 'اليوم', 'النوع', 'التصنيف', 'المبلغ', 'دورة_الميزانية'])
    return pd.DataFrame(columns=['التاريخ', 'اليوم', 'النوع', 'التصنيف', 'المبلغ', 'دورة_الميزانية'])

def save_data(df):
    df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')

if 'df' not in st.session_state:
    st.session_state.df = load_data()

def get_hijri_now():
    today = date.today()
    h = Gregorian(today.year, today.month, today.day).to_hijri()
    days_ar = {"Saturday": "السبت", "Sunday": "الأحد", "Monday": "الإثنين", "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء", "Thursday": "الخميس", "Friday": "الجمعة"}
    day_name = days_ar.get(today.strftime("%A"), "")
    return day_name, f"{today.year}/{today.month:02d}/{today.day:02d} --- {h.year}/{h.month:02d}/{h.day:02d}"

# --- 4. الهيدر المطور ---
day_name, full_date_str = get_hijri_now()
st.markdown(f"""
    <div style="background-color:#0f172a; padding:30px; border-radius:20px; text-align:center; color:white; border-bottom: 6px solid #3b82f6; margin-bottom:10px;">
        <div style="display: flex; justify-content: center; align-items: center; gap: 40px; flex-wrap: wrap;">
            <h1 style="margin:0; font-size: 70px; font-weight: 900; color: #3b82f6;">{day_name}</h1>
            <div id="live_clock_app" style="font-size: 55px; color: #94a3b8; font-weight: 900; font-family: monospace; border-right: 5px solid #3b82f6; padding-right: 25px;">00:00:00</div>
        </div>
        <h3 style="margin:15px 0; opacity:0.8; letter-spacing: 2px;">{full_date_str}</h3>
    </div>
""", unsafe_allow_html=True)

components.html("""
    <script>
    function updateClock() {
        const now = new Date();
        const timeStr = now.toLocaleTimeString('en-GB', { hour12: false });
        window.parent.document.getElementById('live_clock_app').innerHTML = timeStr;
    }
    setInterval(updateClock, 1000);
    updateClock();
    </script>
""", height=0)

# --- 5. ألسنة التبويب ---
tab_main, tab_deep_dive, tab_compare, tab_daily, tab_inc_fix, tab_mgmt = st.tabs([
    "📊 تحليل الدورة الحالية", "🔍 تحليل الأصناف", "🔄 مقارنات الفترات", "🛒 مصروف يومي", "💰 دخل وثوابت", "⚙️ الإدارة"
])

# تحديث بيانات الدورة لكل السجلات
df = st.session_state.df
if not df.empty:
    df['التاريخ'] = pd.to_datetime(df['التاريخ'], errors='coerce')
    df['دورة_الميزانية'] = df['التاريخ'].apply(lambda x: get_fiscal_month(x))

# --- Tab 1: التحليل الرئيسي ---
with tab_main:
    if not df.empty:
        all_cycles = sorted(df['دورة_الميزانية'].unique(), reverse=True)
        selected_cycle = st.selectbox("📅 اختر الدورة المالية للعرض:", all_cycles, key="main_cycle_sel")
        
        curr_df = df[df['دورة_الميزانية'] == selected_cycle]
        income = curr_df[curr_df['النوع'] == 'دخل']['المبلغ'].sum()
        expenses = curr_df[curr_df['النوع'].isin(['يومي', 'ثابت'])]['المبلغ'].sum()
        net = income - expenses
        
        m1, m2, m3 = st.columns(3)
        m1.metric(f"صافي السيولة", f"{net:,.2f} ر.س")
        m2.metric("إجمالي الدخل", f"{income:,.2f}")
        m3.metric("إجمالي المصاريف", f"{expenses:,.2f}")

        # تحليل القمم والقيعان بـ "أمان"
        daily_exp = curr_df[curr_df['النوع'] == 'يومي'].groupby('التاريخ')['المبلغ'].sum()
        if not daily_exp.empty:
            st.divider()
            c_high, c_low = st.columns(2)
            with c_high:
                st.markdown(f"""<div style='background-color:#fee2e2; padding:15px; border-radius:10px; border-right:5px solid #ef4444;'>
                    <h4 style='color:#b91c1c; margin:0;'>📈 أعلى صرف يومي</h4>
                    <p style='font-size:24px; font-weight:bold; margin:0;'>{daily_exp.max():,.2f} ر.س</p>
                    <small>بتاريخ: {daily_exp.idxmax().strftime('%Y-%m-%d')}</small>
                </div>""", unsafe_allow_html=True)
            with c_low:
                st.markdown(f"""<div style='background-color:#dcfce7; padding:15px; border-radius:10px; border-right:5px solid #22c55e;'>
                    <h4 style='color:#15803d; margin:0;'>📉 أقل صرف يومي</h4>
                    <p style='font-size:24px; font-weight:bold; margin:0;'>{daily_exp.min():,.2f} ر.س</p>
                    <small>بتاريخ: {daily_exp.idxmin().strftime('%Y-%m-%d')}</small>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("💡 لا يوجد مصروفات (يومي) في هذه الدورة لعرض التحليل اليومي.")
    else: st.info("ابدأ بإضافة العمليات المالية لتفعيل التحليل.")

# --- Tab Deep Dive: تحليل كل صنف على حده ---
with tab_deep_dive:
    if not df.empty:
        st.subheader("🔍 تتبع تاريخ صنف معين")
        col_s1, col_s2 = st.columns(2)
        target_type = col_s1.selectbox("فلترة حسب النوع:", ["الكل"] + ALL_TYPES)
        
        cats_to_show = ALL_EXP_CATS + INCOME_CATS
        if target_type != "الكل":
            cats_to_show = df[df['النوع'] == target_type]['التصنيف'].unique().tolist()
        
        target_cat = col_s2.selectbox("اختر التصنيف:", ["الكل"] + cats_to_show)
        
        f_df = df.copy()
        if target_type != "الكل": f_df = f_df[f_df['النوع'] == target_type]
        if target_cat != "الكل": f_df = f_df[f_df['التصنيف'] == target_cat]
        
        if not f_df.empty:
            trend = f_df.groupby('دورة_الميزانية')['المبلغ'].sum().reset_index()
            st.plotly_chart(px.line(trend, x='دورة_الميزانية', y='المبلغ', markers=True, title=f"تغير صرف {target_cat} عبر الزمن"), use_container_width=True)
        else: st.warning("لا توجد بيانات لهذا التصنيف.")

# --- Tab Compare: قياس التغيرات ---
with tab_compare:
    if not df.empty and len(df['دورة_الميزانية'].unique()) > 0:
        st.subheader("🔄 مقارنة النمو والانخفاض")
        pivot_df = df.groupby(['دورة_الميزانية', 'التصنيف'])['المبلغ'].sum().unstack(fill_value=0)
        
        if len(pivot_df) >= 1:
            comp_cat = st.selectbox("صنف المقارنة:", ALL_EXP_CATS + INCOME_CATS)
            if comp_cat in pivot_df.columns:
                curr_val = pivot_df.iloc[-1][comp_cat]
                
                cols = st.columns(4)
                # فترات: شهر، 3 أشهر، 6 أشهر، سنة
                intervals = [("شهر", 2), ("3 أشهر", 4), ("6 أشهر", 7), ("سنة", 13)]
                for i, (lab, dist) in enumerate(intervals):
                    with cols[i]:
                        if len(pivot_df) >= dist:
                            prev_val = pivot_df.iloc[-dist][comp_cat]
                            change = ((curr_val - prev_val)/prev_val*100) if prev_val != 0 else 0
                            st.metric(lab, f"{prev_val:,.0f} ر.س", f"{change:+.1f}%")
                        else: st.metric(lab, "قيد الجمع")
            st.bar_chart(pivot_df[comp_cat] if comp_cat in pivot_df.columns else [])
    else: st.info("تحتاج لبيانات شهرين على الأقل للمقارنة.")

# --- Tab Mgmt: الإدارة والاستيراد المصلح ---
with tab_mgmt:
    st.subheader("📥 استيراد وتصدير البيانات")
    up_file = st.file_uploader("ارفع ملف الإكسل (يجب أن يحتوي على عمود التاريخ، التصنيف، النوع، المبلغ)", type=['xlsx', 'csv'])
    if up_file:
        try:
            new_df = pd.read_csv(up_file) if up_file.name.endswith('.csv') else pd.read_excel(up_file)
            # تنظيف التواريخ
            new_df['التاريخ'] = pd.to_datetime(new_df['التاريخ'], errors='coerce')
            new_df = new_df.dropna(subset=['التاريخ'])
            new_df['دورة_الميزانية'] = new_df['التاريخ'].apply(lambda x: get_fiscal_month(x))
            
            if st.button("تأكيد دمج البيانات المرفوعة"):
                st.session_state.df = pd.concat([st.session_state.df, new_df], ignore_index=True)
                save_data(st.session_state.df)
                st.success("✅ تم الاستيراد بنجاح!")
                st.rerun()
        except Exception as e: st.error(f"خطأ في تنسيق الملف: {e}")

    st.divider()
    st.subheader("⚙️ تعديل السجلات يدوياً")
    edited = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)
    if st.button("💾 حفظ التعديلات"):
        st.session_state.df = edited
        save_data(edited)
        st.rerun()

# --- تبويبات الإدخال المعتادة ---
with tab_daily:
    with st.form("f_daily"):
        c1, c2, c3 = st.columns(3)
        d_date = c1.date_input("التاريخ", date.today())
        d_cat = c2.selectbox("التصنيف", DAILY_CATS)
        d_amt = c3.number_input("المبلغ", min_value=0.0)
        if st.form_submit_button("حفظ المصروف"):
            new_row = pd.DataFrame([{"التاريخ": pd.to_datetime(d_date), "اليوم": day_name, "النوع": "يومي", "التصنيف": d_cat, "المبلغ": d_amt, "دورة_الميزانية": get_fiscal_month(pd.to_datetime(d_date))}])
            st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
            save_data(st.session_state.df); st.rerun()

with tab_inc_fix:
    ci, cf = st.columns(2)
    with ci:
        with st.form("f_inc"):
            i_cat = st.selectbox("المصدر", INCOME_CATS)
            i_amt = st.number_input("المبلغ")
            if st.form_submit_button("إضافة دخل"):
                new_row = pd.DataFrame([{"التاريخ": pd.to_datetime(date.today()), "اليوم": day_name, "النوع": "دخل", "التصنيف": i_cat, "المبلغ": i_amt, "دورة_الميزانية": get_fiscal_month(pd.to_datetime(date.today()))}])
                st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True); save_data(st.session_state.df); st.rerun()
    with cf:
        with st.form("f_fix"):
            f_cat = st.selectbox("النوع الثابت", FIXED_CATS)
            f_amt = st.number_input("المبلغ")
            if st.form_submit_button("حفظ ثابت"):
                new_row = pd.DataFrame([{"التاريخ": pd.to_datetime(date.today()), "اليوم": day_name, "النوع": "ثابت", "التصنيف": f_cat, "المبلغ": f_amt, "دورة_الميزانية": get_fiscal_month(pd.to_datetime(date.today()))}])
                st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True); save_data(st.session_state.df); st.rerun()