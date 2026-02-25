import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from hijri_converter import Gregorian
import io, os, json
import streamlit.components.v1 as components

# --- 1. الإعدادات ---
st.set_page_config(page_title="المستشار المالي 2026 - v68", layout="wide")

DB_FILE = "finance_master_2026.csv"
CONFIG_FILE = "app_config_persistent.json"

DAILY_CATS = ["بنزين", "ماء", "الزيت", "الغاز", "السيارة", "تصليح", "فواتير", "مقاضي البيت", "مقاهي", "خضاروفواكهه", "مخالفات", "مقاضي البنات", "المستشفيات والصيدليات", "مطاعم", "ترفيه وحجوزات", "خدمات خارجية", "قطات", "عناية", "أخرى"]
INCOME_CATS = ["الراتب", "حساب المواطن", "الدعم السكني", "الاسهم", "مسترجعات", "حقوق خاصة", "العمالة", "انتداب", "اركابات", "أخرى"]
FIXED_CATS = ["القرض الشخصي", "القرض", "القرض العقاري", "امي", "كفالة", "الاعاشة"]

CUSTOM_COMPARE_LIST = ["أمي", "الاعاشة", "اركابات", "الاسهم", "الدعم السكني", "الراتب", "السيارة", "العمالة", "القرض الشخصي", "القرض العقاري", "المستشفيات والصيدليات", "بنزين", "ترفيه وحجوزات", "تصليح", "انتداب", "حساب المواطن", "خدمات خارجية", "خضار وفواكه", "ديون", "زكاة", "عناية", "فواتير", "قطات", "كفالة", "مخالفات", "مسترجعات", "مطاعم", "مقاضي البيت", "مقاضي البنات", "مقاهي وكفيهات"]

# --- دوال الحفظ والتحميل ---
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"goal": 5000, "services": {}}
    return {"goal": 5000, "services": {}}

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"حدث خطأ أثناء حفظ الإعدادات: {e}")

if 'app_config' not in st.session_state:
    st.session_state.app_config = load_config()

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

def get_cycle_range(cycle_str):
    try:
        month, year = map(int, cycle_str.split('-'))
        curr_month_start = date(year, month, 1)
        prev_month_end = curr_month_start - timedelta(days=1)
        start_day = get_salary_day(prev_month_end.year, prev_month_end.month)
        start_date = date(prev_month_end.year, prev_month_end.month, start_day)
        end_day = get_salary_day(year, month)
        end_date = date(year, month, end_day) - timedelta(days=1)
        return start_date, end_date
    except: return None, None

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

# --- 4. الستايل ---
st.markdown("""
<style>
    .card-container {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        border-radius: 15px; padding: 15px; display: flex;
        flex-direction: row-reverse; align-items: center; justify-content: space-between;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: 2px solid #cbd5e1;
        height: 140px; overflow: hidden;
    }
    .card-icon { font-size: 35px; margin-left: 10px; width: 50px; text-align: center; }
    .text-content { text-align: left; width: 100%; }
    .card-title { color: #000000; font-size: 16px; font-weight: 900; margin-bottom: 2px; text-transform: uppercase; }
    
    .val-stroke-white { 
        color: #ffffff !important; font-size: 32px !important; font-weight: 900 !important;
        text-shadow: 2px 2px 0 #000, -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000;
    }
    .val-stroke-green { 
        color: #22c55e !important; font-size: 32px !important; font-weight: 900 !important;
        text-shadow: 1.5px 1.5px 0 #000, -1px -1px 0 #000;
    }
    .val-stroke-red { 
        color: #ef4444 !important; font-size: 32px !important; font-weight: 900 !important;
        text-shadow: 1.5px 1.5px 0 #000, -1px -1px 0 #000;
    }

    .warn-badge {
        background-color: #ef4444; color: white; padding: 2px 6px; 
        border-radius: 4px; font-size: 11px; font-weight: bold;
        animation: blink 1s infinite; display: inline-block; margin-top: 2px;
    }
    @keyframes blink { 50% { opacity: 0; } }

    .svc-box { 
        background: #1e293b; padding: 10px; border-radius: 15px; 
        border: 2px solid #3b82f6; text-align: center; 
        height: 140px;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
    }
    .note-text { color: #ffffff; font-weight: 900; font-size: 14px; margin-top: 5px; line-height: 1.2; }
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

tabs = st.tabs(["📊 الرئيسية", "🛒 إضافة مصروفات (شامل)", "💰 دخل وثوابت", "🔄 مقارنات وترند", "⚙️ النسخ الاحتياطي"])

# --- Tab 1: الرئيسية ---
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
        
        with c1:
            st.markdown(f"""<div class='card-container' style='background:#bfdbfe;'><div class='card-icon'>💰</div><div class='text-content'><div class='card-title'>إجمالي الدخل</div><div class='val-stroke-white'>{m_inc:,.2f}</div></div></div>""", unsafe_allow_html=True)
            
        with c2:
            st.markdown(f"""<div class='card-container' style='background:#e9d5ff;'><div class='card-icon'>💸</div><div class='text-content'><div class='card-title'>مصروفات الشهر</div><div class='val-stroke-white'>{m_exp:,.2f}</div></div></div>""", unsafe_allow_html=True)
            
        with c3:
            cls = "val-stroke-green" if m_rem >= 0 else "val-stroke-red"
            if m_rem < 0:
                st.markdown(f"""<div class='card-container'><div class='card-icon'>⚖️</div><div class='text-content'><div class='card-title'>المتبقي الشهري</div><div class='{cls}'>{m_rem:,.2f}</div><div class='warn-badge'>⚠️ عجز!</div></div></div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div class='card-container'><div class='card-icon'>⚖️</div><div class='text-content'><div class='card-title'>المتبقي الشهري</div><div class='{cls}'>{m_rem:,.2f}</div></div></div>""", unsafe_allow_html=True)
            
        with c4:
            cls_n = "val-stroke-green" if net_savings >= 0 else "val-stroke-red"
            if net_savings < 0:
                st.markdown(f"""<div class='card-container'><div class='card-icon'>🏦</div><div class='text-content'><div class='card-title'>صافي المدخرات</div><div class='{cls_n}'>{net_savings:,.2f}</div><div class='warn-badge'>⚠️ سالب!</div></div></div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div class='card-container'><div class='card-icon'>🏦</div><div class='text-content'><div class='card-title'>صافي المدخرات</div><div class='{cls_n}'>{net_savings:,.2f}</div></div></div>""", unsafe_allow_html=True)

        st.divider()
        cw, cg, co, cgl = st.columns(4)
        for name, icon, col in [("ماء", "💧", cw), ("الغاز", "🔥", cg), ("الزيت", "🛢️", co)]:
            svc_data = st.session_state.app_config.get("services", {}).get(name, {"date": "---", "note": "---"})
            with col:
                st.markdown(f"""<div class='svc-box'><h2 style='color:white; margin:0;'>{icon} {name}</h2><div class='note-text'>📅 {svc_data['date']}<br>📝 {svc_data['note']}</div></div>""", unsafe_allow_html=True)
                with st.popover(f"تعديل {name}"):
                    d_n = st.date_input("التاريخ", date.today(), key=f"d_{name}")
                    n_n = st.text_input("تفاصيل", value=svc_data['note'], key=f"n_{name}")
                    if st.button("حفظ الملحوظة", key=f"b_{name}"):
                        if "services" not in st.session_state.app_config: st.session_state.app_config["services"] = {}
                        st.session_state.app_config["services"][name] = {"date": d_n.strftime('%Y-%m-%d'), "note": n_n}
                        save_config(st.session_state.app_config); st.rerun()
        
        with cgl:
            cur_g = st.session_state.app_config.get("goal", 5000)
            g_clr = "#22c55e" if m_rem >= cur_g else "#ef4444"
            st.markdown(f"""<div class='svc-box' style='border-color:{g_clr};'><h2 style='color:white; margin:0;'>🎯 الهدف</h2><h2 style='color:{g_clr}; margin:5px 0;'>{m_rem:,.0f} / {cur_g:,.0f}</h2></div>""", unsafe_allow_html=True)
            with st.popover("تعديل الهدف"):
                new_g = st.number_input("الهدف الجديد", value=cur_g, step=500)
                if st.button("حفظ الهدف"): st.session_state.app_config["goal"] = new_g; save_config(st.session_state.app_config); st.rerun()

        st.divider()
        daily_spend = curr_df[~curr_df['النوع'].isin(['دخل', 'الدخل'])].groupby(curr_df['التاريخ'].dt.date)['المبلغ'].sum()
        ch, cl, cz = st.columns(3)
        start_d, end_d = get_cycle_range(sel_cycle)
        zero_days = 0
        if start_d and end_d:
            total_days = (end_d - start_d).days + 1
            zero_days = max(0, total_days - len(daily_spend))

        if not daily_spend.empty:
            with ch: st.markdown(f"<div style='background:linear-gradient(45deg, #991b1b, #ef4444); padding:10px; border-radius:10px; text-align:center; color:white;'>🔺 الأعلى صرفاً<br><b>{daily_spend.max():,.2f}</b> ({daily_spend.idxmax()})</div>", unsafe_allow_html=True)
            with cl: st.markdown(f"<div style='background:linear-gradient(45deg, #065f46, #10b981); padding:10px; border-radius:10px; text-align:center; color:white;'>🔻 الأدنى صرفاً<br><b>{daily_spend.min():,.2f}</b> ({daily_spend.idxmin()})</div>", unsafe_allow_html=True)
        with cz: st.markdown(f"<div style='background:linear-gradient(45deg, #1e40af, #3b82f6); padding:10px; border-radius:10px; text-align:center; color:white;'>✨ أيام بلا صرف<br><b>{zero_days}</b> يوم</div>", unsafe_allow_html=True)

        st.divider()
        st.write(f"### 📊 إحصائيات {sel_cycle}")
        cp, cl = st.columns([1, 1.5])
        with cp:
            if not curr_df[~curr_df['النوع'].isin(['دخل', 'الدخل'])].empty:
                st.plotly_chart(px.pie(curr_df[~curr_df['النوع'].isin(['دخل', 'الدخل'])], values='المبلغ', names='التصنيف', hole=0.5, template="plotly_dark"), use_container_width=True)
        with cl: st.dataframe(curr_df.sort_values('التاريخ', ascending=False), use_container_width=True)

# --- Tab 2: إضافة مصروفات متعددة ---
with tabs[1]:
    st.subheader("🛒 تسجيل مصروفات متعددة (شامل)")
    with st.form("bulk_expense_form", clear_on_submit=True):
        col_date, col_submit = st.columns([1, 3])
        with col_date: entry_date = st.date_input("تاريخ العمليات", date.today())
        st.divider()
        inputs = {}
        cols = st.columns(4)
        for i, cat in enumerate(DAILY_CATS):
            with cols[i % 4]: inputs[cat] = st.number_input(f"{cat}", min_value=0.0, step=1.0, key=f"bulk_{cat}")
        st.divider()
        if st.form_submit_button("💾 حفظ الكل"):
            new_rows = []
            for cat, amount in inputs.items():
                if amount > 0:
                    new_rows.append({"التاريخ": pd.to_datetime(entry_date), "اليوم": d_name, "النوع": "مصروف", "التصنيف": cat, "المبلغ": amount, "التفاصيل": "إدخال متعدد"})
            if new_rows:
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame(new_rows)], ignore_index=True)
                save_data(st.session_state.df); st.success(f"✅ تم إضافة {len(new_rows)} عمليات بنجاح! وتم تصفير الخانات."); st.rerun()
            else: st.warning("⚠️ الرجاء تعبئة خانة واحدة على الأقل.")

# --- Tab 4: المقارنات والترند ---
with tabs[3]:
    if not df.empty:
        st.subheader("📈 مسار الترند")
        
        col_t1, col_t2 = st.columns(2)
        with col_t1: target = st.selectbox("🔍 اختر البند:", CUSTOM_COMPARE_LIST)
        with col_t2: chart_type = st.selectbox("📊 شكل الرسم البياني:", ["خطي انسيابي", "أعمدة (Bar)", "مساحي (Area)", "خطي متدرج (Step)", "نقاط (Scatter)"])
            
        item_df = df[df['التصنيف'] == target].copy().sort_values('التاريخ')
        if not item_df.empty:
            fig = go.Figure()
            
            if chart_type == "خطي انسيابي":
                fig.add_trace(go.Scatter(x=item_df['التاريخ'], y=item_df['المبلغ'], mode='lines+markers', line=dict(color='#3b82f6', width=5, shape='spline'), marker=dict(size=10, color='white', line=dict(width=2, color='#3b82f6'))))
            elif chart_type == "أعمدة (Bar)":
                fig.add_trace(go.Bar(x=item_df['التاريخ'], y=item_df['المبلغ'], marker_color='#3b82f6'))
            elif chart_type == "مساحي (Area)":
                fig.add_trace(go.Scatter(x=item_df['التاريخ'], y=item_df['المبلغ'], mode='lines+markers', fill='tozeroy', line=dict(color='#3b82f6', width=3), marker=dict(size=8, color='white', line=dict(width=2, color='#3b82f6'))))
            elif chart_type == "خطي متدرج (Step)":
                fig.add_trace(go.Scatter(x=item_df['التاريخ'], y=item_df['المبلغ'], mode='lines+markers', line=dict(color='#3b82f6', width=4, shape='hv'), marker=dict(size=8, color='white', line=dict(width=2, color='#3b82f6'))))
            elif chart_type == "نقاط (Scatter)":
                fig.add_trace(go.Scatter(x=item_df['التاريخ'], y=item_df['المبلغ'], mode='markers', marker=dict(size=14, color='#3b82f6', line=dict(width=2, color='white'))))
            
            mx = item_df['المبلغ'].max(); mn = item_df['المبلغ'].min()
            mx_row = item_df[item_df['المبلغ'] == mx].iloc[0]; mn_row = item_df[item_df['المبلغ'] == mn].iloc[0]
            
            fig.add_annotation(x=mx_row['التاريخ'], y=mx, text=f"<b>قمة: {mx:,.2f}</b>", showarrow=True, arrowhead=2, arrowsize=1.5, arrowwidth=3, arrowcolor="black", ax=0, ay=-60, font=dict(color="black", size=16, family="Arial Black"), bgcolor="white", bordercolor="black", borderwidth=2)
            fig.add_annotation(x=mn_row['التاريخ'], y=mn, text=f"<b>قاع: {mn:,.2f}</b>", showarrow=True, arrowhead=2, arrowsize=1.5, arrowwidth=3, arrowcolor="black", ax=0, ay=60, font=dict(color="black", size=16, family="Arial Black"), bgcolor="white", bordercolor="black", borderwidth=2)
            
            fig.update_layout(template="plotly_dark", height=500)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"لا توجد بيانات مسجلة للبند: {target}")

        st.divider()
        st.subheader("📋 جدول المقارنة")
        pivot = df.pivot_table(index='التصنيف', columns='دورة_الميزانية', values='المبلغ', aggfunc='sum').fillna(0)
        
        # فلترة الأشهر وإنشاء أعمدة جديدة تلقائياً
        all_months = sorted(list(pivot.columns), key=lambda x: datetime.strptime(x, "%m-%Y") if x != "None" else datetime.min)
        avail_items = [c for c in CUSTOM_COMPARE_LIST if c in pivot.index]
        
        col_m1, col_m2 = st.columns(2)
        with col_m1: sel_items = st.multiselect("حدد العناصر:", CUSTOM_COMPARE_LIST, default=avail_items[:10])
        with col_m2: sel_months = st.multiselect("📅 حدد الأشهر للمقارنة:", all_months, default=all_months)
        
        valid_sel = [x for x in sel_items if x in pivot.index]
        
        if valid_sel and sel_months: 
            display_df = pivot.loc[valid_sel, sel_months]
            st.dataframe(display_df.style.format("{:,.2f}"), use_container_width=True)
        elif not sel_months:
            st.warning("الرجاء تحديد شهر واحد على الأقل للعرض.")
        elif sel_items:
            st.warning("العناصر المحددة ليس لها بيانات مسجلة في الجداول حتى الآن.")

# --- Tab 5: النسخ الاحتياطي ---
with tabs[4]:
    st.subheader("⚙️ النسخ الاحتياطي والاستعادة")
    st.markdown("""<div style='background:rgba(255, 193, 7, 0.1); padding:15px; border-radius:10px; border:1px solid #ffc107; margin-bottom:20px;'>
    ⚠️ <b>هام جداً:</b> لحفظ بياناتك من الضياع، قم بتحميل ملفات النسخ الاحتياطي (CSV و JSON) بشكل دوري.</div>""", unsafe_allow_html=True)
    
    col_d1, col_d2 = st.columns(2)
    
    with col_d1:
        st.markdown("### 1️⃣ بيانات الأموال")
        if not df.empty:
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 تحميل سجل الأموال (CSV)", data=csv, file_name=f"finance_data_{date.today()}.csv", mime="text/csv")
        
        up_file = st.file_uploader("استعادة نسخة الأموال (CSV)", type=['csv', 'xlsx'], key="up_csv")
        if up_file:
            try:
                n_df = pd.read_csv(up_file) if up_file.name.endswith('.csv') else pd.read_excel(up_file)
                n_df['التاريخ'] = pd.to_datetime(n_df['التاريخ'], errors='coerce')
                st.session_state.df = n_df
                save_data(n_df)
                st.success("تم استعادة الأموال!")
                st.rerun()
            except: st.error("خطأ في الملف")

    with col_d2:
        st.markdown("### 2️⃣ الملحوظات والأهداف (الزيت، الغاز...)")
        json_str = json.dumps(st.session_state.app_config, indent=4, ensure_ascii=False)
        st.download_button("📥 تحميل الملحوظات (JSON)", data=json_str, file_name=f"notes_goals_{date.today()}.json", mime="application/json")
        
        up_json = st.file_uploader("استعادة نسخة الملحوظات (JSON)", type=['json'], key="up_json")
        if up_json:
            try:
                loaded_config = json.load(up_json)
                st.session_state.app_config = loaded_config
                save_config(loaded_config)
                st.success("تم استعادة (الهدف، الزيت، الغاز، الماء)!")
                st.rerun()
            except Exception as e: st.error(f"خطأ: {e}")

    st.divider()
    st.write("### ✏️ تعديل الجدول يدوياً")
    ed = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)
    if st.button("💾 حفظ تعديلات الجدول"): st.session_state.df = ed; save_data(ed); st.success("تم!"); st.rerun()

# --- إدخال الدخل والثابت ---
with tabs[2]:
    c1, c2 = st.columns(2)
    with c1:
        with st.form("i", clear_on_submit=True):
            st.subheader("💰 دخل"); d=st.date_input("تاريخ"); c=st.selectbox("مصدر", INCOME_CATS); a=st.number_input("مبلغ")
            if st.form_submit_button("حفظ"): st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([{"التاريخ":pd.to_datetime(d),"اليوم":d_name,"النوع":"دخل","التصنيف":c,"المبلغ":a}])], ignore_index=True); save_data(st.session_state.df); st.rerun()
    with c2:
        with st.form("f", clear_on_submit=True):
            st.subheader("🏠 ثابت"); d=st.date_input("تاريخ"); c=st.selectbox("نوع", FIXED_CATS); a=st.number_input("مبلغ")
            if st.form_submit_button("حفظ"): st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([{"التاريخ":pd.to_datetime(d),"اليوم":d_name,"النوع":"مصروفات ثابتة","التصنيف":c,"المبلغ":a}])], ignore_index=True); save_data(st.session_state.df); st.rerun()