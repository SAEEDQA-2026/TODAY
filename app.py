import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from hijri_converter import Gregorian
import io
import os
import streamlit.components.v1 as components

# --- 1. الإعدادات وتصنيفات النظام ---
st.set_page_config(page_title="المستشار المالي v28", layout="wide")

DB_FILE = "مصروفات_نهائية_معدلة.csv"

# التصنيفات
DAILY_CATS = ["بنزين", "ماء", "الزيت", "الغاز", "السيارة", "تصليح", "فواتير", "مقاضي البيت", "مقاهي", "خضاروفواكهه", "مخالفات", "مقاضي البنات", "المستشفيات والصيدليات", "مطاعم", "ترفيه وحجوزات", "خدمات خارجية", "قطات", "عناية", "أخرى"]
INCOME_CATS = ["الراتب", "حساب المواطن", "الدعم السكني", "الاسهم", "مسترجعات", "حقوق خاصة", "العمالة", "انتداب", "اركابات", "أخرى"]
FIXED_CATS = ["القرض الشخصي", "القرض العقاري", "امي", "كفالة", "الاعاشة", "قرض شخصي", "القرض"]

# --- 2. نظام الحماية (33550) ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align:center;'>🔒 نظام الإدارة المالية</h1>", unsafe_allow_html=True)
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
        df['النوع'] = df['النوع'].str.strip()
        return df.dropna(subset=['التاريخ'])
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
        <div id="live_clock_v28" style="font-size: 45px; color: #3b82f6; font-weight: bold; font-family: monospace; margin: 10px 0;">00:00:00</div>
        <h3 style="margin:0; opacity:0.8;">{d_full}</h3>
    </div>
""", unsafe_allow_html=True)

components.html("""
    <script>
    function update() {
        const now = new Date();
        window.parent.document.getElementById('live_clock_v28').innerHTML = now.toLocaleTimeString('en-GB', { hour12: false });
    }
    setInterval(update, 1000); update();
    </script>
""", height=0)

# --- 5. منطق البيانات ---
df = st.session_state.df
if not df.empty:
    df['دورة_الميزانية'] = df['التاريخ'].apply(get_fiscal_cycle)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 الرئيسية والشهرية", "🛒 مصروف يومي", "💰 دخل وثوابت", "🔄 مركز المقارنات", "⚙️ السجلات والإدارة"])

# --- Tab 1: الرئيسية (الحسابات الدقيقة) ---
with tab1:
    if not df.empty:
        # حساب المتبقي العام لجميع الأشهر (الواقعي)
        total_income_all = df[df['النوع'] == 'دخل']['المبلغ'].sum()
        total_expense_all = df[df['النوع'] != 'دخل']['المبلغ'].sum()
        general_remaining = total_income_all - total_expense_all

        cycles = sorted([c for c in df['دورة_الميزانية'].unique() if c != "None"], key=lambda x: datetime.strptime(x, "%m-%Y"), reverse=True)
        sel_cycle = st.selectbox("📅 اختر الدورة المالية للتحليل:", cycles)
        curr_df = df[df['دورة_الميزانية'] == sel_cycle]
        
        # موازين الدورة المختارة
        m_income = curr_df[curr_df['النوع'] == 'دخل']['المبلغ'].sum()
        m_expense = curr_df[curr_df['النوع'] != 'دخل']['المبلغ'].sum()
        m_remaining = m_income - m_expense
        
        # كروت المقاييس المالية
        st.write("### 💰 ملخص الميزانية (دقيق)")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("إجمالي دخل الشهر", f"{m_income:,.2f}")
        m2.metric("إجمالي صرف الشهر", f"{m_expense:,.2f}")
        m3.metric("المتبقي الشهري", f"{m_remaining:,.2f}")
        m4.metric("📈 المتبقي العام (التراكمي)", f"{general_remaining:,.2f}")

        st.divider()
        # أيقونات الخدمات (تصميم واضح)
        st.write("### 🛠️ الخدمات والضروريات")
        c_water, c_gas, c_oil, c_goal = st.columns(4)
        
        services = [("ماء", "💧", c_water), ("الغاز", "🔥", c_gas), ("الزيت", "🛢️", c_oil)]
        for name, icon, col in services:
            item_data = curr_df[curr_df['التصنيف'] == name].sort_values('التاريخ', ascending=False)
            val = item_data['المبلغ'].sum()
            with col:
                st.markdown(f"""
                    <div style='text-align:center; padding:15px; background:#1e293b; border-radius:15px; border:2px solid #3b82f6;'>
                        <h1 style='font-size: 55px; margin:0;'>{icon}</h1>
                        <h2 style='color:#3b82f6; font-weight: bold;'>{name}</h2>
                        <h1 style='color:white; margin:0;'>{val:,.2f}</h1>
                    </div>
                """, unsafe_allow_html=True)
                with st.expander("تفاصيل / إضافة"):
                    if not item_data.empty:
                        st.write(f"📅 آخر تاريخ: {item_data.iloc[0]['التاريخ'].date()}")
                        st.write(f"📝 ملاحظة: {item_data.iloc[0].get('التفاصيل', 'لا يوجد')}")
                    # نموذج إضافة سريع
                    with st.popover(f"إضافة {name} جديدة"):
                        ed_d = st.date_input(f"تاريخ {name}", date.today(), key=f"d_{name}")
                        ed_a = st.number_input(f"المبلغ", key=f"a_{name}")
                        ed_n = st.text_input("التفاصيل", key=f"n_{name}")
                        if st.button(f"تأكيد {name}", key=f"b_{name}"):
                            new_r = pd.DataFrame([{"التاريخ": pd.to_datetime(ed_d), "اليوم": d_name, "النوع": "مصروف", "التصنيف": name, "المبلغ": ed_a, "التفاصيل": ed_n}])
                            st.session_state.df = pd.concat([st.session_state.df, new_r], ignore_index=True); save_data(st.session_state.df); st.rerun()

        with c_goal:
            goal_val = st.number_input("🎯 هدف الادخار:", value=5000)
            status_c = "#10b981" if m_remaining >= goal_val else "#ef4444"
            st.markdown(f"""
                <div style='text-align:center; padding:15px; background:#0f172a; border-radius:15px; border:4px solid {status_c};'>
                    <h3>تحقيق الهدف</h3>
                    <h2 style='color:{status_c};'>{m_remaining:,.2f} / {goal_val:,.2f}</h2>
                </div>
            """, unsafe_allow_html=True)

        st.divider()
        st.write("### 📊 تحليل وتفاصيل مصروفات الدورة")
        col_pie, col_tab = st.columns([1, 1])
        with col_pie:
            exp_df = curr_df[curr_df['النوع'] != 'دخل']
            if not exp_df.empty:
                fig = px.pie(exp_df, values='المبلغ', names='التصنيف', hole=0.5, title=f"تحليل مصاريف {sel_cycle}")
                st.plotly_chart(fig, use_container_width=True)
        with col_tab:
            st.write("📑 **سجل العمليات للشهر المختار:**")
            st.dataframe(curr_df[['التاريخ', 'التصنيف', 'المبلغ', 'النوع', 'التفاصيل']].sort_values('التاريخ', ascending=False), use_container_width=True)

# --- Tab 4: المقارنات ---
with tab4:
    if not df.empty:
        st.subheader("🔄 مقارنة الأداء المالي التاريخي")
        comp_df = df.copy()
        comp_df['الفئة'] = comp_df['النوع'].apply(lambda x: 'دخل' if x == 'دخل' else 'صرف')
        summary = comp_df.pivot_table(index='دورة_الميزانية', columns='الفئة', values='المبلغ', aggfunc='sum').fillna(0)
        
        if 'دخل' not in summary.columns: summary['دخل'] = 0
        if 'صرف' not in summary.columns: summary['صرف'] = 0
        summary['الفائض'] = summary['دخل'] - summary['صرف']
        summary = summary.sort_index(key=lambda x: pd.to_datetime(x, format="%m-%Y", errors='coerce'))

        st.plotly_chart(px.bar(summary.reset_index(), x='دورة_الميزانية', y=['دخل', 'صرف'], barmode='group', title="📈 الدخل مقابل الصرف شهرياً"), use_container_width=True)
        st.dataframe(summary.style.format("{:,.2f}"), use_container_width=True)

# --- Tab 5: السجلات والإدارة ---
with tab5:
    st.subheader("⚙️ إدارة السجلات والبيانات")
    col_up, col_down = st.columns(2)
    with col_up:
        up = st.file_uploader("📥 استيراد بيانات ودمجها نهائياً (CSV/Excel)", type=['csv', 'xlsx'])
        if up:
            new_data = pd.read_csv(up) if up.name.endswith('.csv') else pd.read_excel(up)
            st.session_state.df = pd.concat([st.session_state.df, new_data], ignore_index=True)
            st.session_state.df['التاريخ'] = pd.to_datetime(st.session_state.df['التاريخ'], errors='coerce')
            st.session_state.df = st.session_state.df.dropna(subset=['التاريخ'])
            save_data(st.session_state.df); st.success("✅ تم دمج البيانات وحفظها بنجاح."); st.rerun()
    with col_down:
        st.download_button("📤 تصدير قاعدة البيانات (CSV)", df.to_csv(index=False).encode('utf-8-sig'), "finance_master_backup.csv")

    st.divider()
    st.markdown("### 📝 محرر السجلات الشامل (تعديل وحذف)")
    edited = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True, key="master_editor_v28")
    if st.button("💾 تأكيد وحفظ كافة التعديلات"):
        st.session_state.df = edited
        save_data(edited); st.success("تم التحديث بنجاح!"); st.rerun()

# تبويبات الإدخال اليدوي
with tab2:
    with st.form("d_v28"):
        st.subheader("🛒 تسجيل مصروف يومي")
        cl1, cl2, cl3 = st.columns(3)
        d_date = cl1.date_input("التاريخ", date.today())
        d_cat = cl2.selectbox("التصنيف", DAILY_CATS)
        d_amt = cl3.number_input("المبلغ", min_value=0.0)
        d_not = st.text_input("تفاصيل إضافية")
        if st.form_submit_button("حفظ"):
            new_r = pd.DataFrame([{"التاريخ": pd.to_datetime(d_date), "اليوم": d_name, "النوع": "مصروف", "التصنيف": d_cat, "المبلغ": d_amt, "التفاصيل": d_not}])
            st.session_state.df = pd.concat([st.session_state.df, new_r], ignore_index=True); save_data(st.session_state.df); st.rerun()

with tab3:
    col_i, col_fx = st.columns(2)
    with col_i:
        with st.form("i_v28"):
            st.write("💰 تسجيل دخل")
            i_cat = st.selectbox("المصدر", INCOME_CATS); i_amt = st.number_input("المبلغ")
            if st.form_submit_button("إضافة دخل"):
                new_r = pd.DataFrame([{"التاريخ": pd.to_datetime(date.today()), "اليوم": d_name, "النوع": "دخل", "التصنيف": i_cat, "المبلغ": i_amt}])
                st.session_state.df = pd.concat([st.session_state.df, new_r], ignore_index=True); save_data(st.session_state.df); st.rerun()
    with col_fx:
        with st.form("f_v28"):
            st.write("🏠 مصروف ثابت")
            f_cat = st.selectbox("النوع", FIXED_CATS); f_amt = st.number_input("المبلغ")
            if st.form_submit_button("حفظ الثابت"):
                new_r = pd.DataFrame([{"التاريخ": pd.to_datetime(date.today()), "اليوم": d_name, "النوع": "مصروفات ثابتة", "التصنيف": f_cat, "المبلغ": f_amt}])
                st.session_state.df = pd.concat([st.session_state.df, new_r], ignore_index=True); save_data(st.session_state.df); st.rerun()