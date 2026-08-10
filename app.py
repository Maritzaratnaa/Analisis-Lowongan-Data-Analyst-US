import streamlit as st
import pandas as pd
import plotly.express as px
import io

st.set_page_config(
    page_title="Dashboard Analisis Pasar Kerja Data Analyst AS",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_data():
    df = pd.read_csv("data_norm.csv")
    df['job_id'] = df.index
    df['tahun'] = pd.to_numeric(df['tahun'], errors='coerce').fillna(0).astype(int)
    df['pengalaman'] = pd.to_numeric(df['pengalaman'], errors='coerce').fillna(-1)
    df['deskripsi_len'] = pd.to_numeric(df['deskripsi_len'], errors='coerce').fillna(0).astype(int)
    
    str_cols = ['posisi', 'perusahaan', 'lokasi', 'pendidikan', 'jurusan', 'level', 'hard_skill', 'soft_skill', 'deskripsi']
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].fillna("Unspecified").astype(str)
            
    return df

def explode_column(df_subset, col_name, exclude_unspecified=True):
    if col_name not in df_subset.columns or df_subset.empty:
        return pd.DataFrame(columns=['job_id', col_name])
    
    temp = df_subset[['job_id', col_name]].copy()
    temp[col_name] = temp[col_name].astype(str).str.split(r'\s*,\s*')
    exploded = temp.explode(col_name)
    exploded[col_name] = exploded[col_name].str.strip()
    
    invalid_vals = ['', 'nan', 'None', 'none', 'null', 'NaN']
    if exclude_unspecified:
        invalid_vals.extend(['Unspecified', 'Other'])
        
    exploded = exploded[~exploded[col_name].isin(invalid_vals)]
    return exploded

def compute_year_normalized_props(df_subset, col_name, top_n=None, exclude_unspecified=True):
    if df_subset.empty or col_name not in df_subset.columns:
        return pd.DataFrame(columns=['tahun', col_name, 'unique_jobs', 'total_year_jobs', 'persentase'])
    
    year_totals = df_subset.groupby('tahun')['job_id'].nunique().to_dict()
    
    temp = df_subset[['job_id', 'tahun', col_name]].copy()
    temp[col_name] = temp[col_name].astype(str).str.split(r'\s*,\s*')
    exploded = temp.explode(col_name)
    exploded[col_name] = exploded[col_name].str.strip()
    
    invalid_vals = ['', 'nan', 'None', 'none', 'null', 'NaN']
    if exclude_unspecified:
        invalid_vals.extend(['Unspecified', 'Other'])
    exploded = exploded[~exploded[col_name].isin(invalid_vals)]
    
    if exploded.empty:
        return pd.DataFrame(columns=['tahun', col_name, 'unique_jobs', 'total_year_jobs', 'persentase'])
        
    if top_n is not None:
        top_cats = exploded[col_name].value_counts().head(top_n).index.tolist()
        exploded = exploded[exploded[col_name].isin(top_cats)]
        
    grouped = exploded.groupby(['tahun', col_name])['job_id'].nunique().reset_index(name='unique_jobs')
    grouped['total_year_jobs'] = grouped['tahun'].map(year_totals)
    grouped['persentase'] = (grouped['unique_jobs'] / grouped['total_year_jobs'] * 100).round(1)
    
    return grouped

def style_chart(fig, height=380):
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=30, b=35, l=30, r=20),
        height=height,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='rgba(0,0,0,0)'
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.15)',
            zeroline=False
        )
    )
    return fig

df_raw = load_data()

st.title("Dashboard Analisis Pasar Kerja Data Analyst")
st.caption("Analisis Kualifikasi Pendidikan, Kebutuhan Keterampilan, dan Demografi Lowongan (Pasar AS)")
st.divider()

st.info(
    "Volume data lowongan bervariasi antar tahun sehingga grafik perbandingan tren antar tahun disajikan dalam "
    "persentase / proporsi yang dinormalisasi (% dari total lowongan pada tahun tersebut) untuk memberikan perbandingan yang adil dan objektif."
)

# Sidebar 
st.sidebar.header("Filter Data")

# Filter Tahun
all_years = sorted([int(y) for y in df_raw['tahun'].unique() if y > 0])
all_years_check = st.sidebar.checkbox("Pilih Semua Tahun", value=True)
if all_years_check:
    selected_years = all_years
else:
    selected_years = st.sidebar.multiselect(
        "Tahun Publikasi",
        options=all_years,
        default=all_years
    )

# Filter Level Posisi
all_levels = sorted([str(l) for l in df_raw['level'].unique()])
all_levels_check = st.sidebar.checkbox("Pilih Semua Level Senioritas", value=True)
if all_levels_check:
    selected_levels = all_levels
else:
    selected_levels = st.sidebar.multiselect(
        "Tingkat Senioritas Posisi",
        options=all_levels,
        default=all_levels
    )

# Filter Lokasi
all_locations = sorted([str(loc) for loc in df_raw['lokasi'].unique()])
all_locs_check = st.sidebar.checkbox("Pilih Semua Lokasi", value=True)
if all_locs_check:
    selected_locations = all_locations
else:
    selected_locations = st.sidebar.multiselect(
        "Lokasi Negara Bagian",
        options=all_locations,
        default=all_locations
    )

# Filter Rentang Pengalaman
valid_exp_series = df_raw[df_raw['pengalaman'] >= 0]['pengalaman']
min_exp = float(valid_exp_series.min()) if not valid_exp_series.empty else 0.0
max_exp = float(df_raw['pengalaman'].max()) if not df_raw.empty else 10.0

exp_range = st.sidebar.slider(
    "Rentang Pengalaman Kerja (Tahun)",
    min_value=0.0,
    max_value=max_exp,
    value=(0.0, max_exp),
    step=0.5
)

include_unspecified_exp = st.sidebar.checkbox("Sertakan Pengalaman Tidak Dinyatakan (-1)", value=True)

filtered_df = df_raw.copy()

if not all_years_check:
    filtered_df = filtered_df[filtered_df['tahun'].isin(selected_years)]

if not all_levels_check:
    filtered_df = filtered_df[filtered_df['level'].isin(selected_levels)]

if not all_locs_check:
    filtered_df = filtered_df[filtered_df['lokasi'].isin(selected_locations)]

if include_unspecified_exp:
    filtered_df = filtered_df[
        (filtered_df['pengalaman'] == -1) | 
        ((filtered_df['pengalaman'] >= exp_range[0]) & (filtered_df['pengalaman'] <= exp_range[1]))
    ]
else:
    filtered_df = filtered_df[
        (filtered_df['pengalaman'] >= exp_range[0]) & (filtered_df['pengalaman'] <= exp_range[1])
    ]

if filtered_df.empty:
    st.error("Tidak terdapat data yang memenuhi kombinasi kriteria filter. Silakan perbarui parameter filter Anda.")
    st.stop()

# KPI
total_jobs = len(filtered_df)
total_companies = filtered_df['perusahaan'].nunique()
total_locations = filtered_df['lokasi'].nunique()

valid_exp = filtered_df[filtered_df['pengalaman'] >= 0]['pengalaman']
avg_exp = valid_exp.mean() if not valid_exp.empty else 0.0

col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

def render_kpi_card(col, label, value, sublabel, border_color="#2563eb"):
    with col:
        st.markdown(
            f"""
            <div style="
                background-color: var(--background-secondary, rgba(128, 128, 128, 0.05));
                border: 1px solid var(--border-color, rgba(128, 128, 128, 0.2));
                border-left: 4px solid {border_color};
                border-radius: 8px;
                padding: 14px 18px;
                margin-bottom: 12px;
            ">
                <div style="font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.8;">{label}</div>
                <div style="font-size: 1.8rem; font-weight: 800; margin: 4px 0;">{value}</div>
                <div style="font-size: 0.8rem; color: {border_color}; font-weight: 600;">{sublabel}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

render_kpi_card(col_kpi1, "Total Lowongan Unik", f"{total_jobs:,}", "Postings Aktif", "#2563eb")
render_kpi_card(col_kpi2, "Jumlah Perusahaan", f"{total_companies:,}", "Entitas Merekrut", "#0d9488")
render_kpi_card(col_kpi3, "Cakupan Wilayah", f"{total_locations}", "Negara Bagian", "#7c3aed")
render_kpi_card(col_kpi4, "Rata-Rata Pengalaman", f"{avg_exp:.1f} Tahun", "Syarat Minimal", "#db2777")

st.divider()

# Tabs
tab_overview, tab_edu, tab_skills, tab_desc, tab_explorer = st.tabs([
    "Ringkasan Data",
    "Kualifikasi Pendidikan",
    "Analisis Keterampilan",
    "Struktur Deskripsi",
    "Eksplorasi Data"
])

# TAB 1: RINGKASAN Data
with tab_overview:
    col_ov1, col_ov2 = st.columns(2)
    
    with col_ov1:
        st.subheader("Volume Sampel Lowongan per Tahun")
        st.caption("Jumlah lowongan sampel dan persentase terhadap total data terfilter")
        
        year_counts = filtered_df['tahun'].value_counts().reset_index()
        year_counts.columns = ['tahun', 'jumlah']
        year_counts = year_counts.sort_values('tahun')
        year_counts['persentase'] = (year_counts['jumlah'] / total_jobs * 100).round(1)
        
        if not year_counts.empty:
            fig_year = px.bar(
                year_counts,
                x='tahun',
                y='jumlah',
                text=year_counts.apply(lambda r: f"{r['jumlah']:,} ({r['persentase']}%)", axis=1),
                labels={'tahun': 'Tahun Publikasi', 'jumlah': 'Jumlah Lowongan'},
                color='jumlah',
                color_continuous_scale='Blues'
            )
            fig_year.update_traces(textposition='outside')
            fig_year.update_layout(xaxis_type='category', coloraxis_showscale=False)
            st.plotly_chart(style_chart(fig_year, height=360), use_container_width=True)
        else:
            st.info("Tidak ada data volume lowongan.")
        
    with col_ov2:
        st.subheader("Distribusi Senioritas Posisi")
        st.caption("Proporsi tingkat senioritas lowongan dalam dataset terfilter")
        
        level_counts = filtered_df['level'].value_counts().reset_index()
        level_counts.columns = ['level', 'jumlah']
        
        if not level_counts.empty:
            fig_level = px.pie(
                level_counts,
                names='level',
                values='jumlah',
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Blues_r
            )
            fig_level.update_traces(textinfo='percent+label')
            fig_level.update_layout(showlegend=False)
            st.plotly_chart(style_chart(fig_level, height=360), use_container_width=True)
        else:
            st.info("Tidak ada data tingkat senioritas.")

    st.divider()
    
    st.subheader("Tren Proporsi Level Senioritas")
    st.caption("Komposisi senioritas ter-normalisasi terhadap total lowongan pada masing-masing tahun")
    
    level_yr_counts = filtered_df.groupby(['tahun', 'level']).size().reset_index(name='jumlah')
    year_totals_dict = filtered_df.groupby('tahun').size().to_dict()
    level_yr_counts['total_tahun'] = level_yr_counts['tahun'].map(year_totals_dict)
    level_yr_counts['persentase'] = (level_yr_counts['jumlah'] / level_yr_counts['total_tahun'] * 100).round(1)
    
    if not level_yr_counts.empty:
        fig_lvl_trend = px.bar(
            level_yr_counts,
            x='tahun',
            y='persentase',
            color='level',
            barmode='group',
            text=level_yr_counts['persentase'].apply(lambda v: f"{v}%"),
            labels={'tahun': 'Tahun Publikasi', 'persentase': '% Lowongan di Tahun Tersebut', 'level': 'Level Senioritas'},
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        fig_lvl_trend.update_traces(textposition='outside')
        fig_lvl_trend.update_layout(xaxis_type='category', yaxis_title="% dari Total Lowongan di Tahun Tersebut")
        st.plotly_chart(style_chart(fig_lvl_trend, height=400), use_container_width=True)
    else:
        st.info("Tidak ada data tren senioritas antar tahun.")

    st.divider()
    
    col_ov3, col_ov4 = st.columns(2)
    
    with col_ov3:
        st.subheader("10 Perusahaan dengan Rekrutmen Tertinggi")
        st.caption("Perusahaan yang paling aktif membuka lowongan Data Analyst")
        
        top_companies = filtered_df['perusahaan'].value_counts().head(10).reset_index()
        top_companies.columns = ['perusahaan', 'jumlah']
        top_companies = top_companies.sort_values('jumlah', ascending=True)
        top_companies['pct'] = (top_companies['jumlah'] / total_jobs * 100).round(1)
        
        if not top_companies.empty:
            fig_comp = px.bar(
                top_companies,
                x='jumlah',
                y='perusahaan',
                orientation='h',
                text=top_companies.apply(lambda r: f"{r['jumlah']:,} ({r['pct']}%)", axis=1),
                labels={'jumlah': 'Jumlah Lowongan', 'perusahaan': 'Nama Perusahaan'},
                color='jumlah',
                color_continuous_scale='Purples'
            )
            fig_comp.update_traces(textposition='outside')
            fig_comp.update_layout(coloraxis_showscale=False)
            st.plotly_chart(style_chart(fig_comp, height=420), use_container_width=True)
        else:
            st.info("Tidak ada data perusahaan.")

    with col_ov4:
        st.subheader("10 Konsentrasi Lokasi Lowongan Terbanyak")
        st.caption("Negara bagian / wilayah dengan jumlah lowongan tertinggi")
        
        top_locs = filtered_df['lokasi'].value_counts().head(10).reset_index()
        top_locs.columns = ['lokasi', 'jumlah']
        top_locs = top_locs.sort_values('jumlah', ascending=True)
        top_locs['pct'] = (top_locs['jumlah'] / total_jobs * 100).round(1)
        
        if not top_locs.empty:
            fig_loc = px.bar(
                top_locs,
                x='jumlah',
                y='lokasi',
                orientation='h',
                text=top_locs.apply(lambda r: f"{r['jumlah']:,} ({r['pct']}%)", axis=1),
                labels={'jumlah': 'Jumlah Lowongan', 'lokasi': 'Lokasi / Negara Bagian'},
                color='jumlah',
                color_continuous_scale='Teal'
            )
            fig_loc.update_traces(textposition='outside')
            fig_loc.update_layout(coloraxis_showscale=False)
            st.plotly_chart(style_chart(fig_loc, height=420), use_container_width=True)
        else:
            st.info("Tidak ada data lokasi.")

# TAB 2: KUALIFIKASI PENDIDIKAN
with tab_edu:
    exclude_unspec_edu = st.checkbox("Keluarkan Kategori 'Unspecified' dan 'Other' dari Visualisasi Pendidikan", value=False)
    
    col_ed1, col_ed2 = st.columns(2)
    
    with col_ed1:
        st.subheader("Distribusi Tingkat Pendidikan")
        st.caption("Frekuensi dan persentase kualifikasi tingkat pendidikan")
        
        df_edu_exp = explode_column(filtered_df, 'pendidikan', exclude_unspecified=exclude_unspec_edu)
        
        if not df_edu_exp.empty:
            edu_counts = df_edu_exp['pendidikan'].value_counts().reset_index()
            edu_counts.columns = ['pendidikan', 'jumlah']
            edu_counts['persentase'] = (edu_counts['jumlah'] / total_jobs * 100).round(1)
            
            fig_edu = px.bar(
                edu_counts,
                x='pendidikan',
                y='jumlah',
                text=edu_counts.apply(lambda r: f"{r['jumlah']:,} ({r['persentase']}%)", axis=1),
                labels={'pendidikan': 'Tingkat Pendidikan', 'jumlah': 'Frekuensi Kemunculan'},
                color='jumlah',
                color_continuous_scale='Blues'
            )
            fig_edu.update_traces(textposition='outside')
            fig_edu.update_layout(coloraxis_showscale=False)
            st.plotly_chart(style_chart(fig_edu, height=380), use_container_width=True)
        else:
            st.info("Tidak ada data kualifikasi pendidikan yang tersedia.")
            
    with col_ed2:
        st.subheader("15 Bidang Studi Paling Banyak Disyaratkan")
        st.caption("Jurusan akademik yang paling sering dicari pemberi kerja")
        
        df_jur_exp = explode_column(filtered_df, 'jurusan', exclude_unspecified=exclude_unspec_edu)
        
        if not df_jur_exp.empty:
            jur_counts = df_jur_exp['jurusan'].value_counts().head(15).reset_index()
            jur_counts.columns = ['jurusan', 'jumlah']
            jur_counts = jur_counts.sort_values('jumlah', ascending=True)
            jur_counts['persentase'] = (jur_counts['jumlah'] / total_jobs * 100).round(1)
            
            fig_jur = px.bar(
                jur_counts,
                x='jumlah',
                y='jurusan',
                orientation='h',
                text=jur_counts.apply(lambda r: f"{r['jumlah']:,} ({r['persentase']}%)", axis=1),
                labels={'jumlah': 'Frekuensi Kemunculan', 'jurusan': 'Bidang Studi / Jurusan'},
                color='jumlah',
                color_continuous_scale='Viridis'
            )
            fig_jur.update_traces(textposition='outside')
            fig_jur.update_layout(coloraxis_showscale=False)
            st.plotly_chart(style_chart(fig_jur, height=380), use_container_width=True)
        else:
            st.info("Tidak ada data bidang studi yang tersedia.")

    st.divider()

    st.subheader("Tren Proporsi Kualifikasi Pendidikan")
    st.caption("Perubahan proporsi syarat pendidikan berdasarkan total lowongan pada tiap tahun")
    
    edu_year_df = compute_year_normalized_props(filtered_df, 'pendidikan', exclude_unspecified=exclude_unspec_edu)
    
    if not edu_year_df.empty:
        fig_edu_trend = px.bar(
            edu_year_df,
            x='tahun',
            y='persentase',
            color='pendidikan',
            barmode='group',
            text=edu_year_df['persentase'].apply(lambda v: f"{v}%"),
            labels={'tahun': 'Tahun Publikasi', 'persentase': '% Lowongan di Tahun Tersebut', 'pendidikan': 'Tingkat Pendidikan'},
            color_discrete_sequence=px.colors.qualitative.Plotly
        )
        fig_edu_trend.update_traces(textposition='outside')
        fig_edu_trend.update_layout(xaxis_type='category', yaxis_title="% dari Total Lowongan di Tahun Tersebut")
        st.plotly_chart(style_chart(fig_edu_trend, height=420), use_container_width=True)
    else:
        st.info("Tidak ada data tren pendidikan antar tahun.")

    st.divider()

    st.subheader("Tren Proporsi Top 10 Bidang Studi")
    st.caption("Dinamika kebutuhan jurusan spesifik dalam skala persentase ter-normalisasi per tahun")
    
    jur_year_df = compute_year_normalized_props(filtered_df, 'jurusan', top_n=10, exclude_unspecified=exclude_unspec_edu)
    
    if not jur_year_df.empty:
        fig_jur_trend = px.line(
            jur_year_df,
            x='tahun',
            y='persentase',
            color='jurusan',
            markers=True,
            labels={'tahun': 'Tahun Publikasi', 'persentase': '% Lowongan di Tahun Tersebut', 'jurusan': 'Bidang Studi / Jurusan'}
        )
        fig_jur_trend.update_layout(xaxis_type='category', yaxis_title="% dari Total Lowongan di Tahun Tersebut")
        st.plotly_chart(style_chart(fig_jur_trend, height=450), use_container_width=True)
    else:
        st.info("Tidak ada data tren jurusan antar tahun.")

# TAB 3: ANALISIS KETERAMPILAN 
with tab_skills:
    col_sk_ctl1, col_sk_ctl2 = st.columns(2)
    with col_sk_ctl1:
        top_n_skills = st.slider("Jumlah Keterampilan Utama yang Ditampilkan", min_value=5, max_value=25, value=12)
    with col_sk_ctl2:
        exclude_unspec_skills = st.checkbox("Keluarkan Kategori 'Other' dan 'Unspecified' dari Keterampilan", value=True)
        
    col_sk1, col_sk2 = st.columns(2)
    
    df_hard_exp = explode_column(filtered_df, 'hard_skill', exclude_unspecified=exclude_unspec_skills)
    df_soft_exp = explode_column(filtered_df, 'soft_skill', exclude_unspecified=exclude_unspec_skills)
    
    with col_sk1:
        st.subheader(f"Top {top_n_skills} Hard Skills Paling Banyak Dicari")
        st.caption("Teknologi, alat, dan kemampuan teknis utama")
        
        if not df_hard_exp.empty:
            hard_counts = df_hard_exp['hard_skill'].value_counts().head(top_n_skills).reset_index()
            hard_counts.columns = ['hard_skill', 'jumlah']
            hard_counts['pct'] = (hard_counts['jumlah'] / total_jobs * 100).round(1)
            hard_counts = hard_counts.sort_values('jumlah', ascending=True)
            
            fig_hard = px.bar(
                hard_counts,
                x='jumlah',
                y='hard_skill',
                orientation='h',
                text=hard_counts.apply(lambda r: f"{r['jumlah']:,} ({r['pct']}%)", axis=1),
                labels={'jumlah': 'Jumlah Lowongan', 'hard_skill': 'Hard Skill'},
                color='jumlah',
                color_continuous_scale='Plasma'
            )
            fig_hard.update_traces(textposition='outside')
            fig_hard.update_layout(coloraxis_showscale=False)
            st.plotly_chart(style_chart(fig_hard, height=460), use_container_width=True)
        else:
            st.info("Tidak ada data Hard Skill yang memenuhi filter.")

    with col_sk2:
        st.subheader(f"Top {top_n_skills} Soft Skills Paling Banyak Dicari")
        st.caption("Keterampilan interpersonal dan profesionalisme")
        
        if not df_soft_exp.empty:
            soft_counts = df_soft_exp['soft_skill'].value_counts().head(top_n_skills).reset_index()
            soft_counts.columns = ['soft_skill', 'jumlah']
            soft_counts['pct'] = (soft_counts['jumlah'] / total_jobs * 100).round(1)
            soft_counts = soft_counts.sort_values('jumlah', ascending=True)
            
            fig_soft = px.bar(
                soft_counts,
                x='jumlah',
                y='soft_skill',
                orientation='h',
                text=soft_counts.apply(lambda r: f"{r['jumlah']:,} ({r['pct']}%)", axis=1),
                labels={'jumlah': 'Jumlah Lowongan', 'soft_skill': 'Soft Skill'},
                color='jumlah',
                color_continuous_scale='Cividis'
            )
            fig_soft.update_traces(textposition='outside')
            fig_soft.update_layout(coloraxis_showscale=False)
            st.plotly_chart(style_chart(fig_soft, height=460), use_container_width=True)
        else:
            st.info("Tidak ada data Soft Skill yang memenuhi filter.")

    st.divider()

    st.subheader(f"Tren Kebutuhan Top {top_n_skills} Hard Skills")
    st.caption("Perkembangan proporsi kebutuhan teknologi dan alat teknis dari tahun 2020 hingga 2025")
    
    hard_year_df = compute_year_normalized_props(filtered_df, 'hard_skill', top_n=top_n_skills, exclude_unspecified=exclude_unspec_skills)
    
    if not hard_year_df.empty:
        fig_hard_trend = px.line(
            hard_year_df,
            x='tahun',
            y='persentase',
            color='hard_skill',
            markers=True,
            labels={'tahun': 'Tahun Publikasi', 'persentase': '% Lowongan di Tahun Tersebut', 'hard_skill': 'Hard Skill'}
        )
        fig_hard_trend.update_layout(xaxis_type='category', yaxis_title="% dari Total Lowongan di Tahun Tersebut")
        st.plotly_chart(style_chart(fig_hard_trend, height=480), use_container_width=True)
    else:
        st.info("Tidak ada data tren Hard Skill antar tahun.")

    st.divider()

    st.subheader(f"Tren Kebutuhan Top {top_n_skills} Soft Skills")
    st.caption("Perkembangan proporsi kebutuhan soft skills dari tahun 2020 hingga 2025")
    
    soft_year_df = compute_year_normalized_props(filtered_df, 'soft_skill', top_n=top_n_skills, exclude_unspecified=exclude_unspec_skills)
    
    if not soft_year_df.empty:
        fig_soft_trend = px.line(
            soft_year_df,
            x='tahun',
            y='persentase',
            color='soft_skill',
            markers=True,
            labels={'tahun': 'Tahun Publikasi', 'persentase': '% Lowongan di Tahun Tersebut', 'soft_skill': 'Soft Skill'}
        )
        fig_soft_trend.update_layout(xaxis_type='category', yaxis_title="% dari Total Lowongan di Tahun Tersebut")
        st.plotly_chart(style_chart(fig_soft_trend, height=480), use_container_width=True)
    else:
        st.info("Tidak ada data tren Soft Skill antar tahun.")

# TAB 4: STRUKTUR DESKRIPSI 
with tab_desc:
    col_ds1, col_ds2 = st.columns(2)
    
    with col_ds1:
        st.subheader("Distribusi Panjang Deskripsi Pekerjaan (Karakter)")
        st.caption("Sebaran jumlah karakter teks deskripsi lowongan")
        
        fig_hist = px.histogram(
            filtered_df,
            x='deskripsi_len',
            nbins=35,
            labels={'deskripsi_len': 'Jumlah Karakter Teks Deskripsi'},
            color_discrete_sequence=['#3b82f6']
        )
        fig_hist.update_layout(yaxis_title="Frekuensi Lowongan")
        st.plotly_chart(style_chart(fig_hist, height=380), use_container_width=True)

    with col_ds2:
        st.subheader("Rata-Rata Panjang Deskripsi per Senioritas")
        st.caption("Kedalaman informasi deskripsi berdasarkan level jabatan")
        
        desc_by_level = filtered_df.groupby('level')['deskripsi_len'].mean().reset_index()
        desc_by_level.columns = ['level', 'avg_len']
        desc_by_level['avg_len'] = desc_by_level['avg_len'].round(0)
        desc_by_level = desc_by_level.sort_values('avg_len', ascending=False)
        
        if not desc_by_level.empty:
            fig_desc_lvl = px.bar(
                desc_by_level,
                x='level',
                y='avg_len',
                text='avg_len',
                labels={'level': 'Tingkat Senioritas Posisi', 'avg_len': 'Rata-Rata Karakter'},
                color='avg_len',
                color_continuous_scale='Darkmint'
            )
            fig_desc_lvl.update_traces(textposition='outside')
            fig_desc_lvl.update_layout(coloraxis_showscale=False)
            st.plotly_chart(style_chart(fig_desc_lvl, height=380), use_container_width=True)
        else:
            st.info("Tidak ada data panjang deskripsi berdasarkan level.")

    st.divider()

    st.subheader("Tren Rata-Rata Panjang Deskripsi Pekerjaan Antar Tahun (Karakter)")
    st.caption("Evaluasi dinamika kelengkapan deskripsi pekerjaan dari tahun ke tahun")
    
    desc_by_year = filtered_df.groupby('tahun')['deskripsi_len'].mean().reset_index()
    desc_by_year.columns = ['tahun', 'avg_len']
    desc_by_year['avg_len'] = desc_by_year['avg_len'].round(0)
    desc_by_year = desc_by_year.sort_values('tahun')
    
    if not desc_by_year.empty:
        fig_desc_yr = px.bar(
            desc_by_year,
            x='tahun',
            y='avg_len',
            text='avg_len',
            labels={'tahun': 'Tahun Publikasi', 'avg_len': 'Rata-Rata Karakter Deskripsi'},
            color='avg_len',
            color_continuous_scale='Blues'
        )
        fig_desc_yr.update_traces(textposition='outside')
        fig_desc_yr.update_layout(xaxis_type='category', coloraxis_showscale=False)
        st.plotly_chart(style_chart(fig_desc_yr, height=380), use_container_width=True)
    else:
        st.info("Tidak ada data tren deskripsi antar tahun.")

    st.divider()

    st.subheader("Inspeksi Detail Dokumen Lowongan Pekerjaan")
    st.caption("Pilih entri lowongan untuk memeriksa metadata dan teks deskripsi lengkap")
    
    sample_options = list(filtered_df.index)
    if sample_options:
        sample_job = st.selectbox(
            "Pilih Entri Lowongan untuk Menampilkan Teks Deskripsi Lengkap:",
            options=sample_options,
            format_func=lambda i: (
                f"{filtered_df.loc[i, 'posisi'].iloc[0] if isinstance(filtered_df.loc[i, 'posisi'], pd.Series) else filtered_df.loc[i, 'posisi']} - "
                f"{filtered_df.loc[i, 'perusahaan'].iloc[0] if isinstance(filtered_df.loc[i, 'perusahaan'], pd.Series) else filtered_df.loc[i, 'perusahaan']} "
                f"({filtered_df.loc[i, 'lokasi'].iloc[0] if isinstance(filtered_df.loc[i, 'lokasi'], pd.Series) else filtered_df.loc[i, 'lokasi']})"
            ) if i in filtered_df.index else f"Entri #{i}"
        )
        
        if sample_job is not None and sample_job in filtered_df.index:
            job_detail = filtered_df.loc[sample_job]
            if isinstance(job_detail, pd.DataFrame):
                job_detail = job_detail.iloc[0]
                
            st.markdown(f"#### Posisi: {job_detail['posisi']}")
            st.markdown(f"**Perusahaan:** {job_detail['perusahaan']} | **Lokasi:** {job_detail['lokasi']} | **Tahun:** {job_detail['tahun']}")
            st.markdown(f"**Tingkat Senioritas:** {job_detail['level']} | **Pengalaman:** {job_detail['pengalaman']} Tahun | **Panjang Karakter:** {job_detail['deskripsi_len']:,}")
            st.markdown(f"**Hard Skill:** {job_detail['hard_skill']}")
            st.markdown(f"**Soft Skill:** {job_detail['soft_skill']}")
            st.markdown(f"**Kualifikasi Pendidikan:** {job_detail['pendidikan']} (Jurusan: {job_detail['jurusan']})")
            
            with st.expander("Tampilkan Teks Deskripsi Lengkap", expanded=True):
                st.write(job_detail['deskripsi'])
    else:
        st.info("Tidak ada data lowongan untuk ditampilkan.")

# TAB 5: EKSPLORAS DATA
with tab_explorer:
    st.subheader("Tabel Eksplorasi Data & Ekspor CSV")
    st.caption("Inspeksi data mentah terfilter dan unduh dalam format CSV")
    
    st.write(f"Menampilkan **{len(filtered_df):,}** entri data lowongan pekerjaan sesuai dengan parameter filter aktif.")
    
    all_display_cols = ['posisi', 'perusahaan', 'lokasi', 'tahun', 'level', 'pengalaman', 'pendidikan', 'jurusan', 'hard_skill', 'soft_skill', 'deskripsi_len']
    selected_cols = st.multiselect(
        "Pilih Kolom Tabel yang Ditampilkan:",
        options=df_raw.columns.tolist(),
        default=all_display_cols
    )
    
    if not selected_cols:
        st.warning("Silakan pilih setidaknya satu kolom untuk ditampilkan dan diunduh.")
    else:
        st.dataframe(filtered_df[selected_cols], use_container_width=True, height=450)
        
        csv_buffer = io.BytesIO()
        filtered_df[selected_cols].to_csv(csv_buffer, index=False, encoding='utf-8')
        csv_bytes = csv_buffer.getvalue()
        
        st.download_button(
            label="Unduh Data Terfilter (Format CSV)",
            data=csv_bytes,
            file_name="lowongan_data_analyst_terfilter.csv",
            mime="text/csv"
        )

st.divider()
st.caption("Dashboard Analisis Lowongan Data Analyst AS")
