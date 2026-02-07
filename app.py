import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from hijri_converter import Gregorian
import io
import os
import json
import streamlit.components.v1 as components

# --- 1. الإعدادات وتصنيفات النظام ---
st.set_page_config(page_title="المستشار المالي 2026 - v33", layout="wide")

DB_FILE = "finance_master_2026.csv"
CONFIG_FILE = "app_config.json"

DAILY_CATS = ["بنزين", "ماء", "الزيت", "الغاز", "السيارة", "تصليح", "فواتير", "مقاضي البيت", "مقاهي", "خضاروفواكهه", "مخالفات", "مقاضي البنات", "المستشفيات والصيدليات", "مطاعم", "ترفيه وحجوزات", "خدمات خارجية", "قطات", "عناية", "أخرى"]
INCOME_CATS = ["الراتب", "حساب المواطن", "الدعم السكني", "الاسهم", "مسترجعات", "حقوق خاصة", "العمالة", "انتداب", "اركابات", "أخرى"]
# التعديل رقم 1: استعادة القرض الشخصي في القائمة
FIXED_CATS = ["القرض الشخصي", "القرض العقاري", "امي", "كفالة", "الاعاشة"]

# وظائف حفظ الإعدادات (للهدف والبيانات المستمرة)
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {"goal": 5000}

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f)

config = load_config()

# --- 2. نظام الحماية (33550) ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align:center;'>🔒 نظام الإدارة المالية 2026</h1>", unsafe_allow_html=True)
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
        if wd == 4: return 26
        if wd == 5: return 28
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
        try:
            df = pd.read_csv(DB_FILE)
            df['التاريخ'] = pd.to_datetime(df['التاريخ'], errors='coerce')
            df = df[df['التاريخ'] >= '2025-12-26']
            df['المبلغ'] = pd.to_numeric(df['المبلغ'], errors='coerce').fillna(0)
            return df.dropna(subset=['التاريخ']).reset_index(drop=True)
        except: pass
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

# --- 4. التنسيقات البصرية والهيدر ---
d_name, d_full = get_hijri()
st.markdown(f"""
    <style>
    .stat-card-max {{
        background: linear-gradient(135deg, #450a0a 0%, #7f1d1d 100%);
        border: 2px solid #ef4444; color: white; padding: 20px; border-radius: 15px; text-align: center;
        box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3);
    }}
    .stat-card-min {{
        background: linear-gradient(135deg, #064e3b 0%, #065f46 100%);
        border: 2px solid #10b981; color: white; padding: 20px; border-radius: 15px; text-align: center;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
    }}
    .metric-container {{
        background-color: #1e293b; padding: 15px; border-radius: 12px; border: 1px solid #334155; text-align: center;
    }}
    </style>
    <div style="background-color:#0f172a; padding:20px; border-radius:15px; text-align:center; color:white; border-bottom: 5px solid #3b82f6;">
        <h1 style="margin:0; font-size: 55px; font-weight: 900;">{d_name}</h1>
        <div id="live_clock_v33" style="font-size: 45px; color: #3b82f6; font-weight: bold; font-family: monospace; margin: 10px 0;">00:00:00</div>
        <h3 style="margin:0; opacity:0.8;">{d_full}</h3>
    </div>
""", unsafe_allow_html=True)

components.html("""
    <script>
    function update() {
        const now = new Date();
        window.parent.document.getElementById('live_clock_v33').innerHTML = now.toLocaleTimeString('en-GB', { hour12: false });
    }
    setInterval(update, 1000); update();
    </script>
""", height=0)

# --- 5. منطق البيانات والتبويبات ---
df = st.session_state.df
if not df.empty:
    df['دورة_الميزانية'] = df['التاريخ'].apply(get_fiscal_cycle)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 الرئيسية والشهرية", "🛒 مصروف يومي", "💰 دخل وثوابت", "🔄 المقارنات اليومية", "⚙️ السجلات والإدارة"])

# --- Tab 1: الرئيسية (ملخص وتحليل) ---
with tab1:
    if not df.empty:
        total_in_all = df[df['النوع'].isin(['دخل', 'الدخل'])]['المبلغ'].sum()
        total_out_all = df[~df['النوع'].isin(['دخل', 'الدخل'])]['المبلغ'].sum()
        actual_net_surplus = total_in_all - total_out_all

        cycles = sorted([c for c in df['دورة_الميزانية'].unique() if c != "None"], key=lambda x: datetime.strptime(x, "%m-%Y"), reverse=True)
        sel_cycle = st.selectbox("📅 اختر الشهر للعرض والتحليل:", cycles)
        curr_df = df[df['دورة_الميزانية'] == sel_cycle]
        
        m_inc = curr_df[curr_df['النوع'].isin(['دخل', 'الدخل'])]['المبلغ'].sum()
        m_exp = curr_df[~curr_df['النوع'].isin(['دخل', 'الدخل'])]['المبلغ'].sum()
        m_surplus = m_inc - m_exp
        
        # التعديل رقم 2: وضوح النصوص والألوان التفاعلية
        color_surplus = "#10b981" if m_surplus >= 0 else "#ef4444"
        color_net = "#10b981" if actual_net_surplus >= 0 else "#ef4444"

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"<div class='metric-container'><p style='margin:0; font-size:16px; color:#94a3b8;'>إجمالي دخل الشهر</p><h2 style='color:white; margin:0;'>{m_inc:,.2f}</h2></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='metric-container'><p style='margin:0; font-size:16px; color:#94a3b8;'>مصروفات الشهر</p><h2 style='color:white; margin:0;'>{m_exp:,.2f}</h2></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='metric-container'><p style='margin:0; font-size:16px; color:#94a3b8;'>المتبقي الشهري</p><h2 style='color:{color_surplus}; margin:0; font-weight:900;'>{m_surplus:,.2f}</h2></div>", unsafe_allow_html=True)
        with c4:
            st.markdown(f"<div class='metric-container'><p style='margin:0; font-size:16px; color:#94a3b8;'>📈 صافي مدخرات 2026</p><h2 style='color:{color_net}; margin:0; font-weight:900;'>{actual_net_surplus:,.2f}</h2></div>", unsafe_allow_html=True)

        st.divider()
        st.write("### 📈 إحصائيات الذروة لهذا الشهر")
        c_high, c_low = st.columns(2)
        daily_spend = curr_df[~curr_df['النوع'].isin(['دخل', 'الدخل'])].groupby(curr_df['التاريخ'].dt.date)['المبلغ'].sum()
        
        if not daily_spend.empty:
            max_day = daily_spend.idxmax()
            min_day = daily_spend.idxmin()
            with c_high:
                st.markdown(f"<div class='stat-card-max'><h1 style='margin:0;'>🔺</h1><h3>أعلى صرف يومي</h3><h2>{daily_spend.max():,.2f} ر.س</h2><p>بتاريخ: {max_day}</p></div>", unsafe_allow_html=True)
            with c_low:
                st.markdown(f"<div class='stat-card-min'><h1 style='margin:0;'>🔻</h1><h3>أدنى صرف يومي</h3><h2>{daily_spend.min():,.2f} ر.س</h2><p>بتاريخ: {min_day}</p></div>", unsafe_allow_html=True)

        st.divider()
        # التعديل رقم 5: إظهار التاريخ داخل الأيقونة بالأسفل
        st.write("### 🛠️ الخدمات والهدف المالي")
        col_w, col_g, col_o, col_goal = st.columns(4)
        
        for name, icon, col in [("ماء", "💧", col_w), ("الغاز", "🔥", col_g), ("الزيت", "🛢️", col_o)]:
            item_entries = curr_df[curr_df['التصنيف'] == name].sort_values('التاريخ', ascending=False)
            val = item_entries['المبلغ'].sum()
            last_date = item_entries.iloc[0]['التاريخ'].strftime('%Y-%m-%d') if not item_entries.empty else "---"
            
            with col:
                st.markdown(f"""
                    <div style='text-align:center; padding:15px; background:#1e293b; border-radius:15px; border:3px solid #3b82f6;'>
                        <h1 style='font-size: 50px; margin:0;'>{icon}</h1>
                        <h3 style='color:#3b82f6; margin:5px 0;'>{name}</h3>
                        <h2 style='color:white; margin:0;'>{val:,.2f}</h2>
                        <div style='background:rgba(59, 130, 246, 0.1); margin-top:10px; border-radius:5px; padding:2px;'>
                            <p style='color:#94a3b8; font-size:12px; margin:0;'>📅 {last_date}</p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                with st.popover(f"إضافة {name}"):
                    e_d = st.date_input(f"تاريخ {name}", date.today(), key=f"d_{name}")
                    e_a = st.number_input(f"المبلغ", key=f"a_{name}")
                    e_n = st.text_input("تفاصيل", key=f"n_{name}")
                    if st.button(f"تأكيد {name}", key=f"b_{name}"):
                        new = pd.DataFrame([{"التاريخ": pd.to_datetime(e_d), "اليوم": d_name, "النوع": "مصروف", "التصنيف": name, "المبلغ": e_a, "التفاصيل": e_n}])
                        st.session_state.df = pd.concat([st.session_state.df, new], ignore_index=True); save_data(st.session_state.df); st.rerun()

        with col_goal:
            # التعديل رقم 4: أيقونة حفظ الهدف الادخاري
            current_goal = config.get("goal", 5000)
            c_g_1, c_g_2 = st.columns([4, 1])
            with c_g_1:
                new_goal = st.number_input("🎯 حدد هدف الادخار:", value=current_goal, step=500, label_visibility="collapsed")
            with c_g_2:
                if st.button("💾", help="حفظ الهدف بشكل دائم"):
                    config["goal"] = new_goal
                    save_config(config)
                    st.toast("تم حفظ الهدف الادخاري!")
            
            goal_color = "#10b981" if m_surplus >= current_goal else "#ef4444"
            st.markdown(f"<div style='text-align:center; padding:10px; background:#0f172a; border-radius:15px; border:4px solid {goal_color};'><h3 style='margin:0; font-size:14px; color:white;'>تحقيق الهدف</h3><h2 style='color:{goal_color}; margin:0;'>{m_surplus:,.2f} / {current_goal:,.2f}</h2></div>", unsafe_allow_html=True)

        st.divider()
        st.write(f"### 📊 تحليل وتفاصيل {sel_cycle}")
        cp, cl = st.columns([1, 1.5])
        with cp:
            exp_only = curr_df[~curr_df['النوع'].isin(['دخل', 'الدخل'])]
            if not exp_only.empty:
                st.plotly_chart(px.pie(exp_only, values='المبلغ', names='التصنيف', hole=0.5, template="plotly_dark"), use_container_width=True)
        with cl:
            st.write("📑 سجل العمليات للشهر:")
            st.dataframe(curr_df[['التاريخ', 'التصنيف', 'النوع', 'المبلغ', 'التفاصيل']].sort_values('التاريخ', ascending=False), use_container_width=True)
    else:
        st.info("ابدأ بإضافة بياناتك الأولى لعام 2026.")

# --- Tab 4: المقارنات اليومية ---
with tab4:
    if not df.empty:
        st.subheader("🔄 تتبع تغير العناصر")
        exp_all = df[~df['النوع'].isin(['دخل', 'الدخل'])].copy()
        target_cat = st.selectbox("اختر العنصر للتتبع:", sorted(exp_all['التصنيف'].unique()))
        
        item_df = exp_all[exp_all['التصنيف'] == target_cat].copy().sort_values('التاريخ')
        if not item_df.empty:
            # التعديل رقم 3: شارت خطي متصل مع علامات القمة والقاع
            fig_daily = px.line(item_df, x='التاريخ', y='المبلغ', color='دورة_الميزانية',
                                markers=True, line_shape="spline", title=f"📈 مسار صرف {target_cat} الزمني",
                                template="plotly_dark")
            
            # تحديد أعلى قمة وأدنى قاع
            max_val = item_df['المبلغ'].max()
            min_val = item_df['المبلغ'].min()
            max_pts = item_df[item_df['المبلغ'] == max_val]
            min_pts = item_df[item_df['المبلغ'] == min_val]
            
            fig_daily.add_scatter(x=max_pts['التاريخ'], y=max_pts['المبلغ'], mode='markers', marker=dict(color='yellow', size=15, symbol='star'), name='أعلى قمة')
            fig_daily.add_scatter(x=min_pts['التاريخ'], y=min_pts['المبلغ'], mode='markers', marker=dict(color='orange', size=15, symbol='triangle-down'), name='أدنى قاع')

            st.plotly_chart(fig_daily, use_container_width=True)
        else:
            st.warning("لا توجد بيانات كافية.")

# --- Tab 3: دخل وثوابت ---
with tab3:
    ci, cf = st.columns(2)
    with ci:
        with st.form("inc_v33"):
            st.subheader("💰 تسجيل دخل")
            i_date = st.date_input("تاريخ الاستلام", date.today())
            i_cat = st.selectbox("المصدر", INCOME_CATS)
            i_amt = st.number_input("المبلغ")
            if st.form_submit_button("حفظ"):
                new = pd.DataFrame([{"التاريخ": pd.to_datetime(i_date), "اليوم": d_name, "النوع": "دخل", "التصنيف": i_cat, "المبلغ": i_amt}])
                st.session_state.df = pd.concat([st.session_state.df, new], ignore_index=True); save_data(st.session_state.df); st.rerun()
    with cf:
        with st.form("fix_v33"):
            st.subheader("🏠 مصروف ثابت")
            f_date = st.date_input("تاريخ المصروف", date.today())
            f_cat = st.selectbox("النوع", FIXED_CATS)
            f_amt = st.number_input("المبلغ")
            if st.form_submit_button("حفظ"):
                new = pd.DataFrame([{"التاريخ": pd.to_datetime(f_date), "اليوم": d_name, "النوع": "مصروفات ثابتة", "التصنيف": f_cat, "المبلغ": f_amt}])
                st.session_state.df = pd.concat([st.session_state.df, new], ignore_index=True); save_data(st.session_state.df); st.rerun()

# --- Tab 5: السجلات ---
with tab5:
    st.subheader("⚙️ إدارة السجلات")
    col_u, col_d = st.columns(2)
    with col_u:
        up = st.file_uploader("📥 استيراد ودمج ملفات", type=['csv', 'xlsx'])
        if up:
            try:
                n_df = pd.read_csv(up) if up.name.endswith('.csv') else pd.read_excel(up)
                st.session_state.df = pd.concat([st.session_state.df, n_df], ignore_index=True)
                st.session_state.df['التاريخ'] = pd.to_datetime(st.session_state.df['التاريخ'], errors='coerce')
                st.session_state.df = st.session_state.df[st.session_state.df['التاريخ'] >= '2025-12-26']
                save_data(st.session_state.df); st.success("تم الدمج بنجاح!"); st.rerun()
            except: st.error("خطأ في قراءة الملف!")
    with col_d:
        st.download_button("📤 تصدير بيانات 2026", df.to_csv(index=False).encode('utf-8-sig'), "finance_v33_final.csv")

    st.divider()
    edited = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True, key="ed_v33")
    if st.button("💾 حفظ كافة التعديلات"):
        st.session_state.df = edited
        save_data(edited); st.success("تم التحديث والحفظ!"); st.rerun()

with tab2:
    with st.form("d_v33"):
        st.subheader("🛒 تسجيل مصروف يومي")
        c1, c2, c3, c4 = st.columns(4)
        d_date = c1.date_input("التاريخ", date.today())
        d_cat = c2.selectbox("التصنيف", DAILY_CATS)
        d_amt = c3.number_input("المبلغ")
        d_not = c4.text_input("التفاصيل")
        if st.form_submit_button("حفظ"):
            new = pd.DataFrame([{"التاريخ": pd.to_datetime(d_date), "اليوم": d_name, "النوع": "مصروف", "التصنيف": d_cat, "المبلغ": d_amt, "التفاصيل": d_not}])
            st.session_state.df = pd.concat([st.session_state.df, new], ignore_index=True); save_data(st.session_state.df); st.rerun()