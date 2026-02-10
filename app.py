import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from hijri_converter import Gregorian
import io, os, json
import streamlit.components.v1 as components

# --- 1. الإعدادات ---
st.set_page_config(page_title="المستشار المالي 2026 - v56", layout="wide")

DB_FILE = "finance_master_2026.csv"
CONFIG_FILE = "app_config_persistent.json"

DAILY_CATS = ["بنزين", "ماء", "الزيت", "الغاز", "السيارة", "تصليح", "فواتير", "مقاضي البيت", "مقاهي", "خضاروفواكهه", "مخالفات", "مقاضي البنات", "المستشفيات والصيدليات", "مطاعم", "ترفيه وحجوزات", "خدمات خارجية", "قطات", "عناية", "أخرى"]
INCOME_CATS = ["الراتب", "حساب المواطن", "الدعم السكني", "الاسهم", "مسترجعات", "حقوق خاصة", "العمالة", "انتداب", "اركابات", "أخرى"]
FIXED_CATS = ["القرض الشخصي", "القرض", "القرض العقاري", "امي", "كفالة", "الاعاشة"]

# --- تصحيح الخطأ هنا (فصل الأسطر) ---
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"goal": 5000, "services": {}}

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f)

config = load_config()

# --- 2. الحماية ---
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align:center;'>🔒 نظام الإدارة المالية 2026</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        if st.text_input("أدخل رمز الدخول", type="password") == "33550":
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

# --- 3. المحرك ---
def get_salary_day(year, month):
    try:
        t_27 = date(int(year), int(month), 27)
        return 26 if t_27.weekday() == 4 else (28 if t_27.weekday() == 5 else 27)
    except: return 27

def get_fiscal_cycle(dt):
    if pd.isna(dt): return "None"
    sd = get_salary_day(dt.year, dt.month)
    if dt.day >= sd: return (dt + pd.DateOffset(months=1)).strftime("%m-%Y")
    return dt.strftime("%m-%Y")

def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            df['التاريخ'] = pd.to_datetime(df['التاريخ'], errors='coerce')
            df['المبلغ'] = pd.to_numeric(df['المبلغ'], errors='coerce').fillna(0)
            return df.dropna(subset=['التاريخ']).reset_index(drop=True)
        except: pass
    return pd.DataFrame(columns=['التاريخ', 'اليوم', 'النوع', 'التصنيف', 'المبلغ', 'التفاصيل'])

def save_data(df): df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')

if 'df' not in st.session_state: st.session_state.df = load_data()

# --- 4. الستايل (CSS) ---
st.markdown("""
<style>
    /* بطاقات زرقاء شفافة */
    .glass-card {
        background: rgba(30, 58, 138, 0.4);
        border-radius: 15px; padding: 20px; text-align: center;
        border: 1px solid #3b82f6; margin-bottom: 10px; height: 180px;
    }
    .lbl { color: #bfdbfe; font-size: 16px; font-weight: bold; margin-bottom: 5px; }
    
    /* قيم رقمية ضخمة */
    .val-pos { color: #22c55e !important; font-size: 42px !important; font-weight: 900 !important; text-shadow: 0 0 10px rgba(34,197,94,0.3); }
    .val-neg { color: #ef4444 !important; font-size: 42px !important; font-weight: 900 !important; text-shadow: 0 0 10px rgba(239,68,68,0.3); }
    .val-neu { color: #ffffff !important; font-size: 42px !important; font-weight: 900 !important; }
    
    /* صندوق التحذير */
    .warn-box {
        background-color: #7f1d1d; color: white; padding: 5px; border-radius: 5px;
        font-weight: bold; font-size: 13px; margin-top: 10px; animation: flash 1.5s infinite;
    }
    @keyframes flash { 0% {opacity: 1;} 50% {opacity: 0.5;} 100% {opacity: 1;} }
    
    /* صندوق الملحوظات */
    .note-display {
        background: rgba(255,255,255,0.1); padding: 8px; border-radius: 8px;
        margin-top: 10px; font-size: 13px; color: #e2e8f0; font-weight: normal;
        border-right: 3px solid #f59e0b; text-align: right;
    }
</style>
""", unsafe_allow_html=True)

def get_hijri():
    t = date.today()
    h = Gregorian(t.year, t.month, t.day).to_hijri()
    days = {"Saturday":"السبت", "Sunday":"الأحد", "Monday":"الإثنين", "Tuesday":"الثلاثاء", "Wednesday":"الأربعاء", "Thursday":"الخميس", "Friday":"الجمعة"}
    return days.get(t.strftime("%A"),""), f"{t.year}/{t.month:02d}/{t.day:02d} | {h.year}/{h.month:02d}/{h.day:02d}"

d_name, d_full = get_hijri()
st.markdown(f"""<div style="background:#0f172a; padding:20px; border-radius:15px; text-align:center; border-bottom:4px solid #3b82f6;">
<h1 style='color:white; margin:0;'>{d_name}</h1><h2 style='color:#3b82f6; margin:0;'>{d_full}</h2></div>""", unsafe_allow_html=True)

# --- 5. المنطق ---
df = st.session_state.df
if not df.empty: df['دورة_الميزانية'] = df['التاريخ'].apply(get_fiscal_cycle)

tabs = st.tabs(["📊 الرئيسية", "🛒 مصروف", "💰 دخل", "🔄 مقارنات", "⚙️ إدارة"])

with tabs[0]:
    if not df.empty:
        in_all = df[df['النوع'].isin(['دخل', 'الدخل'])]['المبلغ'].sum()
        out_all = df[~df['النوع'].isin(['دخل', 'الدخل'])]['المبلغ'].sum()
        net_savings = in_all - out_all
        
        cycles = sorted([c for c in df['دورة_الميزانية'].unique() if c != "None"], key=lambda x: datetime.strptime(x, "%m-%Y"), reverse=True)
        sel_cycle = st.selectbox("📅 الدورة الشهرية:", cycles)
        curr_df = df[df['دورة_الميزانية'] == sel_cycle]
        
        m_inc = curr_df[curr_df['النوع'].isin(['دخل', 'الدخل'])]['المبلغ'].sum()
        m_exp = curr_df[~curr_df['النوع'].isin(['دخل', 'الدخل'])]['المبلغ'].sum()
        m_rem = m_inc - m_exp

        c1, c2, c3, c4 = st.columns(4)
        
        # 1. إجمالي الدخل
        with c1:
            st.markdown(f"""<div class='glass-card'>
            <div style='font-size:30px;'>💰</div><div class='lbl'>إجمالي الدخل</div>
            <div class='val-neu' style='color:#1e40af !important;'>{m_inc:,.2f}</div></div>""", unsafe_allow_html=True)
            
        # 2. المصروفات
        with c2:
            st.markdown(f"""<div class='glass-card'>
            <div style='font-size:30px;'>💸</div><div class='lbl'>مصروفات الشهر</div>
            <div class='val-neu' style='color:#7c3aed !important;'>{m_exp:,.2f}</div></div>""", unsafe_allow_html=True)
            
        # 3. المتبقي
        with c3:
            cls = "val-pos" if m_rem >= 0 else "val-neg"
            warn = "" if m_rem >= 0 else "<div class='warn-box'>⚠️ تحذير: عجز مالي!</div>"
            st.markdown(f"""<div class='glass-card'>
            <div style='font-size:30px;'>⚖️</div><div class='lbl'>المتبقي الشهري</div>
            <div class='{cls}'>{m_rem:,.2f}</div>{warn}</div>""", unsafe_allow_html=True)
            
        # 4. صافي المدخرات
        with c4:
            cls_n = "val-pos" if net_savings >= 0 else "val-neg"
            warn_n = "" if net_savings >= 0 else "<div class='warn-box'>⚠️ تحذير: رصيد سالب!</div>"
            st.markdown(f"""<div class='glass-card'>
            <div style='font-size:30px;'>🏦</div><div class='lbl'>صافي المدخرات</div>
            <div class='{cls_n}'>{net_savings:,.2f}</div>{warn_n}</div>""", unsafe_allow_html=True)

        st.divider()
        st.write("### 🛠️ الخدمات")
        
        col_w, col_g, col_o, col_goal = st.columns(4)
        
        for name, icon, col in [("ماء", "💧", col_w), ("الغاز", "🔥", col_g), ("الزيت", "🛢️", col_o)]:
            svc_data = config.get("services", {}).get(name, {"date": "---", "note": "لا توجد ملحوظة"})
            val = curr_df[curr_df['التصنيف'] == name]['المبلغ'].sum()
            
            with col:
                st.markdown(f"""<div style='background:#1e293b; padding:15px; border-radius:15px; text-align:center; border:2px solid #3b82f6;'>
                    <h2>{icon} {name}</h2>
                    <h2 style='color:white; margin:5px 0;'>{val:,.2f}</h2>
                    <div class='note-display'>📅 {svc_data['date']}<br>📝 {svc_data['note']}</div>
                </div>""", unsafe_allow_html=True)
                
                with st.popover(f"تعديل {name}"):
                    st.write("تحديث الملحوظة فقط (لا يضيف مبلغ):")
                    d_new = st.date_input("تاريخ", date.today(), key=f"d_{name}")
                    n_new = st.text_input("التفاصيل", value=svc_data['note'], key=f"n_{name}")
                    if st.button(f"حفظ", key=f"btn_{name}"):
                        if "services" not in config: config["services"] = {}
                        config["services"][name] = {"date": d_new.strftime('%Y-%m-%d'), "note": n_new}
                        save_config(config)
                        st.success("تم!")
                        st.rerun()
        
        with col_goal:
            cur_g = config.get("goal", 5000)
            g1, g2 = st.columns([3,1])
            new_g = g1.number_input("الهدف", value=cur_g, step=500, label_visibility="collapsed")
            if g2.button("💾"): config["goal"] = new_g; save_config(config); st.toast("حفظ")
            g_clr = "#22c55e" if m_rem >= cur_g else "#ef4444"
            st.markdown(f"""<div style='background:#1e293b; padding:15px; border-radius:15px; text-align:center; border:2px solid {g_clr};'>
                <h2>🎯 الهدف</h2>
                <h2 style='color:{g_clr};'>{m_rem:,.2f} / {cur_g:,.2f}</h2>
            </div>""", unsafe_allow_html=True)

        st.divider()
        st.write(f"### 📊 إحصائيات {sel_cycle}")
        cp, cl = st.columns([1, 1.5])
        with cp:
            exp_only = curr_df[~curr_df['النوع'].isin(['دخل', 'الدخل'])]
            if not exp_only.empty: st.plotly_chart(px.pie(exp_only, values='المبلغ', names='التصنيف', hole=0.5, template="plotly_dark"), use_container_width=True)
        with cl: st.dataframe(curr_df[['التاريخ', 'التصنيف', 'النوع', 'المبلغ', 'التفاصيل']].sort_values('التاريخ', ascending=False), use_container_width=True, height=400)

# --- Tab 4: المقارنات ---
with tabs[3]:
    if not df.empty:
        st.subheader("📈 مسار الترند (Trend Line)")
        target = st.selectbox("🔍 اختر البند:", sorted(df['التصنيف'].unique()))
        item_df = df[df['التصنيف'] == target].copy().sort_values('التاريخ')
        if not item_df.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=item_df['التاريخ'], y=item_df['المبلغ'], mode='lines+markers',
                                    line=dict(color='#3b82f6', width=5, shape='spline'),
                                    marker=dict(size=10, color='white', line=dict(width=2, color='#3b82f6'))))
            
            mx = item_df['المبلغ'].max(); mn = item_df['المبلغ'].min()
            mx_row = item_df[item_df['المبلغ'] == mx].iloc[0]; mn_row = item_df[item_df['المبلغ'] == mn].iloc[0]
            fig.add_annotation(x=mx_row['التاريخ'], y=mx, text=f"⬆ {mx:,.2f}", showarrow=True, arrowhead=2, ax=0, ay=-40, font=dict(color="red"))
            fig.add_annotation(x=mn_row['التاريخ'], y=mn, text=f"⬇ {mn:,.2f}", showarrow=True, arrowhead=2, ax=0, ay=40, font=dict(color="#22c55e"))
            fig.update_layout(template="plotly_dark", height=500)
            st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.subheader("📋 جدول المقارنة")
        pivot = df.pivot_table(index='التصنيف', columns='دورة_الميزانية', values='المبلغ', aggfunc='sum').fillna(0)
        sel_items = st.multiselect("حدد العناصر:", pivot.index.tolist(), default=pivot.index.tolist()[:10])
        if sel_items:
            st.dataframe(pivot.loc[sel_items].style.format("{:,.2f}"), use_container_width=True)

# --- Tab 5: السجلات ---
with tabs[4]:
    st.subheader("⚙️ إدارة السجلات")
    up = st.file_uploader("📥 استيراد ملف")
    if up:
        try:
            n_df = pd.read_csv(up) if up.name.endswith('.csv') else pd.read_excel(up)
            n_df['التاريخ'] = pd.to_datetime(n_df['التاريخ'], errors='coerce')
            combined = pd.concat([st.session_state.df, n_df], ignore_index=True)
            clean_df = combined.drop_duplicates(subset=['التاريخ', 'التصنيف', 'المبلغ', 'النوع', 'التفاصيل'], keep='first')
            st.session_state.df = clean_df.reset_index(drop=True); save_data(st.session_state.df); st.success("تم!")
            st.rerun()
        except Exception as e: st.error(f"خطأ: {e}")
    st.divider()
    edited = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)
    if st.button("💾 حفظ"): st.session_state.df = edited; save_data(edited); st.success("تم!"); st.rerun()

# --- إدخال البيانات ---
with tabs[2]:
    c1, c2 = st.columns(2)
    with c1:
        with st.form("i_f"):
            st.subheader("💰 دخل"); d = st.date_input("تاريخ"); c = st.selectbox("مصدر", INCOME_CATS); a = st.number_input("مبلغ")
            if st.form_submit_button("حفظ"):
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([{"التاريخ":pd.to_datetime(d),"اليوم":d_name,"النوع":"دخل","التصنيف":c,"المبلغ":a}])], ignore_index=True); save_data(st.session_state.df); st.rerun()
    with c2:
        with st.form("f_f"):
            st.subheader("🏠 ثابت"); d = st.date_input("تاريخ"); c = st.selectbox("نوع", FIXED_CATS); a = st.number_input("مبلغ")
            if st.form_submit_button("حفظ"):
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([{"التاريخ":pd.to_datetime(d),"اليوم":d_name,"النوع":"مصروفات ثابتة","التصنيف":c,"المبلغ":a}])], ignore_index=True); save_data(st.session_state.df); st.rerun()

with tabs[1]:
    with st.form("d_f"):
        st.subheader("🛒 مصروف"); c1,c2,c3,c4 = st.columns(4)
        d = c1.date_input("تاريخ"); c = c2.selectbox("تصنيف", DAILY_CATS); a = c3.number_input("مبلغ"); n = c4.text_input("تفاصيل")
        if st.form_submit_button("حفظ"):
            st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([{"التاريخ":pd.to_datetime(d),"اليوم":d_name,"النوع":"مصروف","التصنيف":c,"المبلغ":a,"التفاصيل":n}])], ignore_index=True); save_data(st.session_state.df); st.rerun()