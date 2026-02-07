import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from hijri_converter import Gregorian
import io
import os
import streamlit.components.v1 as components

# --- 1. الإعدادات وتصنيفات النظام ---
st.set_page_config(page_title="المستشار المالي 2026 v31", layout="wide")

DB_FILE = "finance_master_2026.csv"

DAILY_CATS = ["بنزين", "ماء", "الالزيت", "الغاز", "السيارة", "تصليح", "فواتير", "مقاضي البيت", "مقاهي", "خضاروفواكهه", "مخالفات", "مقاضي البنات", "المستشفيات والصيدليات", "مطاعم", "ترفيه وحجوزات", "خدمات خارجية", "قطات", "عناية", "أخرى"]
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

# --- 3. محرك الميزانية (قاعدة 27) ---
def get_salary_day(year, month):
    try:
        t_27 = date(int(year), int(month), 27)
        wd = t_27.weekday() 
        if wd == 4: return 26 # الجمعة
        if wd == 5: return 28 # السبت
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
        <div id="live_clock_v31" style="font-size: 45px; color: #3b82f6; font-weight: bold; font-family: monospace; margin: 10px 0;">00:00:00</div>
        <h3 style="margin:0; opacity:0.8;">{d_full}</h3>
    </div>
""", unsafe_allow_html=True)

components.html("""
    <script>
    function update() {
        const now = new Date();
        window.parent.document.getElementById('live_clock_v31').innerHTML = now.toLocaleTimeString('en-GB', { hour12: false });
    }
    setInterval(update, 1000); update();
    </script>
""", height=0)

# --- 5. منطق البيانات والتبويبات ---
df = st.session_state.df
if not df.empty:
    df['دورة_الميزانية'] = df['التاريخ'].apply(get_fiscal_cycle)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 الرئيسية والشهرية", "🛒 مصروف يومي", "💰 دخل وثوابت", "🔄 المقارنات اليومية", "⚙️ السجلات والإدارة"])

# --- Tab 1: الرئيسية ---
with tab1:
    if not df.empty:
        total_in = df[df['النوع'].isin(['دخل', 'الدخل'])]['المبلغ'].sum()
        total_out = df[~df['النوع'].isin(['دخل', 'الدخل'])]['المبلغ'].sum()
        actual_net_surplus = total_in - total_out

        cycles = sorted([c for c in df['دورة_الميزانية'].unique() if c.endswith("2026")], key=lambda x: datetime.strptime(x, "%m-%Y"), reverse=True)
        if not cycles: cycles = ["None"]
        sel_cycle = st.selectbox("📅 اختر الشهر للعرض والتحليل:", cycles)
        curr_df = df[df['دورة_الميزانية'] == sel_cycle]
        
        m_inc = curr_df[curr_df['النوع'].isin(['دخل', 'الدخل'])]['المبلغ'].sum()
        m_exp = curr_df[~curr_df['النوع'].isin(['دخل', 'الدخل'])]['المبلغ'].sum()
        m_surplus = m_inc - m_exp
        
        # 1. كروت المقاييس المالية
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("إجمالي دخل الشهر", f"{m_inc:,.2f}")
        m2.metric("مصروفات (ثابتة+يومية)", f"{m_exp:,.2f}")
        m3.metric("المتبقي من الدخل", f"{m_surplus:,.2f}")
        m4.metric("📈 الصافي العام 2026", f"{actual_net_surplus:,.2f}")

        st.divider()
        # 2. أعلى وأدنى صرف
        st.write("### 📈 إحصائيات الصرف اليومي")
        c_high, c_low = st.columns(2)
        daily_spend = curr_df[~curr_df['النوع'].isin(['دخل', 'الدخل'])].groupby(curr_df['التاريخ'].dt.date)['المبلغ'].sum()
        if not daily_spend.empty:
            max_day = daily_spend.idxmax()
            min_day = daily_spend.idxmin()
            c_high.markdown(f"<div style='text-align:center; padding:15px; background:#1e293b; border-radius:15px; border:2px solid #ef4444;'><h3>🔺 أعلى صرف</h3><h2>{daily_spend.max():,.2f}</h2><p>{max_day}</p></div>", unsafe_allow_html=True)
            c_low.markdown(f"<div style='text-align:center; padding:15px; background:#1e293b; border-radius:15px; border:2px solid #10b981;'><h3>🔻 أدنى صرف</h3><h2>{daily_spend.min():,.2f}</h2><p>{min_day}</p></div>", unsafe_allow_html=True)

        st.divider()
        # 3. أيقونات الخدمات والهدف
        st.write("### 🛠️ الخدمات والهدف المالي")
        col_w, col_g, col_o, col_goal = st.columns(4)
        
        for name, icon, col in [("ماء", "💧", col_w), ("الغاز", "🔥", col_g), ("الزيت", "🛢️", col_o)]:
            val = curr_df[curr_df['التصنيف'] == name]['المبلغ'].sum()
            with col:
                st.markdown(f"<div style='text-align:center; padding:15px; background:#1e293b; border-radius:15px; border:2px solid #3b82f6;'><h1>{icon}</h1><h3>{name}</h3><h2>{val:,.2f}</h2></div>", unsafe_allow_html=True)
                with st.popover("+ إضافة"):
                    e_d = st.date_input(f"تاريخ {name}", date.today(), key=f"d_{name}")
                    e_a = st.number_input(f"المبلغ", key=f"a_{name}")
                    e_n = st.text_input("التفاصيل", key=f"n_{name}")
                    if st.button(f"حفظ {name}", key=f"b_{name}"):
                        new = pd.DataFrame([{"التاريخ": pd.to_datetime(e_d), "اليوم": d_name, "النوع": "مصروف", "التصنيف": name, "المبلغ": e_a, "التفاصيل": e_n}])
                        st.session_state.df = pd.concat([st.session_state.df, new], ignore_index=True); save_data(st.session_state.df); st.rerun()

        with col_goal:
            goal_target = st.number_input("🎯 حدد هدف الادخار:", value=5000, step=500)
            status_color = "#10b981" if m_surplus >= goal_target else "#ef4444"
            st.markdown(f"<div style='text-align:center; padding:15px; background:#0f172a; border-radius:15px; border:3px solid {status_color};'><h3>تحقيق الهدف</h3><h2 style='color:{status_color};'>{m_surplus:,.2f} / {goal_target:,.2f}</h2></div>", unsafe_allow_html=True)

        st.divider()
        col_p, col_l = st.columns([1, 1.5])
        with col_p:
            exp_only = curr_df[~curr_df['النوع'].isin(['دخل', 'الدخل'])]
            if not exp_only.empty:
                st.plotly_chart(px.pie(exp_only, values='المبلغ', names='التصنيف', hole=0.5, title="توزيع المصاريف"), use_container_width=True)
        with col_l:
            st.write("📝 **سجل العمليات للشهر:**")
            st.dataframe(curr_df[['التاريخ', 'التصنيف', 'المبلغ', 'النوع', 'التفاصيل']].sort_values('التاريخ', ascending=False), use_container_width=True)
    else:
        st.info("ابدأ بإضافة بياناتك المالية لعام 2026.")

# --- Tab 4: مركز المقارنات اليومية ---
with tab4:
    if not df.empty:
        st.subheader("🔄 تتبع تغير العناصر (يومياً وشهرياً)")
        exp_df = df[~df['النوع'].isin(['دخل', 'الدخل'])].copy()
        target_cat = st.selectbox("اختر العنصر للتحليل (مثال: بنزين):", sorted(exp_df['التصنيف'].unique()))
        
        item_data = exp_df[exp_df['التصنيف'] == target_cat].copy()
        item_data['اليوم_من_الشهر'] = item_data['التاريخ'].dt.day
        
        # رسم بياني للتغير اليومي
        fig_daily = px.scatter(item_data, x='اليوم_من_الشهر', y='المبلغ', color='دورة_الميزانية', size='المبلغ',
                               title=f"📈 تتبع صرف {target_cat} خلال أيام الشهر", labels={'اليوم_من_الشهر': 'يوم في الشهر'})
        st.plotly_chart(fig_daily, use_container_width=True)
        
        st.write("🔢 **التفاصيل الزمنية للعنصر:**")
        st.dataframe(item_data[['التاريخ', 'دورة_الميزانية', 'المبلغ', 'التفاصيل']].sort_values('التاريخ', ascending=False), use_container_width=True)

# --- Tab 3: دخل وثوابت ---
with tab3:
    col_i, col_f = st.columns(2)
    with col_i:
        with st.form("inc_2026"):
            st.subheader("💰 تسجيل دخل")
            i_date = st.date_input("تاريخ الاستلام", date.today())
            i_cat = st.selectbox("المصدر", INCOME_CATS)
            i_amt = st.number_input("المبلغ", min_value=0.0)
            if st.form_submit_button("حفظ الدخل"):
                new = pd.DataFrame([{"التاريخ": pd.to_datetime(i_date), "اليوم": d_name, "النوع": "دخل", "التصنيف": i_cat, "المبلغ": i_amt}])
                st.session_state.df = pd.concat([st.session_state.df, new], ignore_index=True); save_data(st.session_state.df); st.rerun()
    with col_f:
        with st.form("fix_2026"):
            st.subheader("🏠 مصروف ثابت")
            f_date = st.date_input("تاريخ المصروف", date.today())
            f_cat = st.selectbox("النوع", FIXED_CATS)
            f_amt = st.number_input("المبلغ", min_value=0.0)
            if st.form_submit_button("حفظ الثابت"):
                new = pd.DataFrame([{"التاريخ": pd.to_datetime(f_date), "اليوم": d_name, "النوع": "مصروفات ثابتة", "التصنيف": f_cat, "المبلغ": f_amt}])
                st.session_state.df = pd.concat([st.session_state.df, new], ignore_index=True); save_data(st.session_state.df); st.rerun()

# --- Tab 5: السجلات والإدارة ---
with tab5:
    st.subheader("⚙️ إدارة سجلات 2026")
    col_u, col_d = st.columns(2)
    with col_u:
        up = st.file_uploader("📥 استيراد ودمج ملفات", type=['csv', 'xlsx'])
        if up:
            n_df = pd.read_csv(up) if up.name.endswith('.csv') else pd.read_excel(up)
            st.session_state.df = pd.concat([st.session_state.df, n_df], ignore_index=True)
            st.session_state.df['التاريخ'] = pd.to_datetime(st.session_state.df['التاريخ'], errors='coerce')
            st.session_state.df = st.session_state.df[st.session_state.df['التاريخ'] >= '2025-12-26']
            save_data(st.session_state.df); st.success("تم دمج البيانات!"); st.rerun()
    with col_d:
        st.download_button("📤 تصدير البيانات (CSV)", df.to_csv(index=False).encode('utf-8-sig'), "finance_2026_master.csv")

    st.divider()
    edited = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True, key="master_ed_v31")
    if st.button("💾 تأكيد وحفظ كافة التعديلات"):
        st.session_state.df = edited
        save_data(edited); st.success("تم التحديث بنجاح!"); st.rerun()

with tab2:
    with st.form("d_2026"):
        st.subheader("🛒 تسجيل مصروف يومي")
        c1, c2, c3, c4 = st.columns(4)
        d_date = c1.date_input("التاريخ", date.today())
        d_cat = c2.selectbox("التصنيف", DAILY_CATS)
        d_amt = c3.number_input("المبلغ", min_value=0.0)
        d_not = c4.text_input("التفاصيل")
        if st.form_submit_button("حفظ"):
            new = pd.DataFrame([{"التاريخ": pd.to_datetime(d_date), "اليوم": d_name, "النوع": "مصروف", "التصنيف": d_cat, "المبلغ": d_amt, "التفاصيل": d_not}])
            st.session_state.df = pd.concat([st.session_state.df, new], ignore_index=True); save_data(st.session_state.df); st.rerun()