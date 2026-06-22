import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime
from PIL import Image

# 1. 페이지 기본 설정 및 테마
st.set_page_config(
    page_title="무비레코드365",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 데이터 및 포스터 저장 경로 설정
DATA_PATH = "data/movies.csv"
POSTER_DIR = "data/posters"
if not os.path.exists(POSTER_DIR):
    os.makedirs(POSTER_DIR, exist_ok=True)

# 2. 전역 스타일링 (아름다운 최신 웹 디자인 적용)
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Noto+Sans+KR:wght@300;400;700&display=swap');
    
    /* 폰트 및 배경 설정 */
    html, body, [class*="css"] {
        font-family: 'Outfit', 'Noto Sans KR', sans-serif;
    }
    
    /* 메인 배경색 조정 (소프트 라이트) */
    .stApp {
        background-color: #f8fafc;
        color: #1e293b;
    }
    
    /* 타이틀 및 헤더 스타일 */
    .cinema-title {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(45deg, #0f172a, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
        letter-spacing: -1px;
    }
    
    .cinema-subtitle {
        font-size: 1.2rem;
        color: #64748b;
        text-align: center;
        margin-bottom: 2.5rem;
    }
    
    /* 카드 스타일 (화이트 카드) */
    .movie-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    }
    
    .movie-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        border: 1px solid #cbd5e1;
    }

    /* 포스터 템플릿 카드 (포스터 없을 때) */
    .poster-placeholder {
        aspect-ratio: 1 / 1.4;
        width: 100%;
        height: auto;
        background: linear-gradient(135deg, #f1f5f9, #e2e8f0);
        border-radius: 12px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        border: 2px dashed #cbd5e1;
        padding: 1rem;
        text-align: center;
    }
    
    .poster-placeholder-title {
        font-weight: 700;
        font-size: 1.1rem;
        color: #334155;
        margin-top: 10px;
    }

    /* 평점 별(Star) 스타일 */
    .star-rating {
        color: #f59e0b;
        font-size: 1.2rem;
        margin-bottom: 0.5rem;
    }
    
    /* 스탯 숫자 스타일 */
    .stat-number {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0f172a;
        line-height: 1;
        margin-bottom: 0.5rem;
        white-space: nowrap;
    }
    
    .stat-label {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        white-space: nowrap;
    }
    
    /* 사이드바 스타일 커스텀 */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    
    /* 헤더 및 차트 주변 링크/앵커 숨기기 */
    a.header-anchor, a[data-testid="stHeaderAnchor"], .st-emotion-cache-1629p8f a,
    h1 a, h2 a, h3 a, h4 a, h5 a, h6 a {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* 기록하기 폼 테두리 선 제거 */
    [data-testid="stForm"] {
        border: none !important;
    }

    /* 텍스트 입력창 Enter 안내 문구 숨기기 */
    div[data-testid="InputInstructions"] {
        display: none !important;
        visibility: hidden !important;
    }
</style>
""", unsafe_allow_html=True)


# 3. 데이터 로딩 및 도우미 함수
def load_data(path):
    if os.path.exists(path):
        df = pd.read_csv(path)
        # 날짜 타입 변환 및 정렬
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values(by='date', ascending=False)
        return df
    else:
        # 빈 DataFrame 반환
        return pd.DataFrame(columns=[
            'title', 'date', 'rating', 'genre', 'review', 
            'poster_path', 'runtime', 'companion', 'award_nominee', 'notes'
        ])

def save_data(df, path):
    df.to_csv(path, index=False)

def get_star_string(rating):
    full_stars = int(rating)
    half_star = 1 if (rating - full_stars) >= 0.5 else 0
    empty_stars = 5 - full_stars - half_star
    
    html = "<span style='color: #eab308; font-size: 0.9rem; letter-spacing: 1px;'>"
    html += "<i class='fa-solid fa-star'></i>" * full_stars
    html += "<i class='fa-solid fa-star-half-stroke'></i>" * half_star
    html += "<i class='fa-regular fa-star' style='color: #cbd5e1;'></i>" * empty_stars
    html += "</span>"
    return html

if 'edit_mode_title' not in st.session_state:
    st.session_state['edit_mode_title'] = None

def delete_movie_callback(title_to_del):
    df_temp = load_data(DATA_PATH)
    df_temp = df_temp[df_temp['title'] != title_to_del]
    save_data(df_temp, DATA_PATH)

def set_edit_mode_callback(title_to_edit):
    st.session_state['edit_mode_title'] = title_to_edit

def cancel_edit_mode_callback():
    st.session_state['edit_mode_title'] = None

# 데이터 불러오기
df = load_data(DATA_PATH)

# 4. 사이드바 구성
with st.sidebar:
    st.markdown("<div style='text-align: center; padding: 1rem 0;'><span style='font-size: 4rem;'>📝</span></div>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #0f172a; margin-bottom: 2rem; font-weight:800;'>무비레코드365</h2>", unsafe_allow_html=True)
    
    menu = st.radio(
        "메뉴 선택",
        ["1년요약표", "영화아카이브", "새 영화 기록하기"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # BGM 플레이어 추가
    st.markdown("<div style='font-size: 0.85rem; font-weight: 600; color: #475569; margin-bottom: 5px;'>🎵 Background Music</div>", unsafe_allow_html=True)
    bgm_url = "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3?filename=lofi-study-112191.mp3"
    try:
        st.audio(bgm_url, format="audio/mp3", loop=True)
    except:
        st.audio(bgm_url, format="audio/mp3")
    st.markdown(
        "<div style='text-align: center; color: #94a3b8; font-size: 0.85rem;'>"
        "나만의 영화 기록장<br>Powered by Streamlit"
        "</div>", 
        unsafe_allow_html=True
    )

# 5. 각 메뉴별 페이지 렌더링

# ----------------- [메뉴 1: 대시보드] -----------------
if menu == "1년요약표":
    
    if df.empty:
        st.info("아직 등록된 영화가 없습니다. '새 영화 기록하기' 메뉴에서 첫 번째 영화를 기록해 보세요!")
    else:
        df['year'] = pd.to_datetime(df['date']).dt.year
        years_list = ["전체"] + sorted(df['year'].unique().tolist(), reverse=False)
        
        col_dummy, col_year = st.columns([4, 1])
        with col_year:
            selected_year = st.selectbox("📅 연도 선택", years_list)
            
        if selected_year != "전체":
            summary_df = df[df['year'] == selected_year].copy()
        else:
            summary_df = df.copy()
            
        if summary_df.empty:
            st.warning(f"선택하신 연도({selected_year}년)에 등록된 영화 기록이 없습니다.")
        else:
            total_movies = len(summary_df)
            avg_rating = summary_df['rating'].mean()
            total_runtime = summary_df['runtime'].sum() if 'runtime' in summary_df.columns else 0
            most_watched_genre = summary_df['genre'].mode()[0] if not summary_df['genre'].empty else "없음"
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="movie-card" style="text-align: center;">
                    <div class="stat-number" style="color:#3b82f6;">{total_movies}편</div>
                    <div class="stat-label">총 관람 영화</div>
                </div>
                """, unsafe_allow_html=True)
                
            with col2:
                st.markdown(f"""
                <div class="movie-card" style="text-align: center;">
                    <div class="stat-number" style="color:#f59e0b;">{avg_rating:.2f}</div>
                    <div class="stat-label">평균 별점 (5.0 만점)</div>
                </div>
                """, unsafe_allow_html=True)
                
            with col3:
                hours = int(total_runtime // 60)
                minutes = int(total_runtime % 60)
                time_str = f"{hours}시간 {minutes}분" if hours > 0 else f"{minutes}분"
                st.markdown(f"""
                <div class="movie-card" style="text-align: center;">
                    <div class="stat-number" style="color:#8b5cf6;">{time_str}</div>
                    <div class="stat-label">스크린 앞의 시간</div>
                </div>
                """, unsafe_allow_html=True)
                
            with col4:
                st.markdown(f"""
                <div class="movie-card" style="text-align: center;">
                    <div class="stat-number" style="color:#10b981;">{most_watched_genre}</div>
                    <div class="stat-label">선호 장르</div>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.markdown("<h3 style='color: #1e293b; font-weight:700;'>📅 월별 영화 관람 트렌드</h3>", unsafe_allow_html=True)
                summary_df['month'] = pd.to_datetime(summary_df['date']).dt.strftime('%m월')
                months_order = [f"{i:02d}월" for i in range(1, 13)]
                monthly_count = summary_df.groupby('month').size().reindex(months_order, fill_value=0).reset_index(name='count')
                
                fig_monthly = px.bar(
                    monthly_count, 
                    x='month', 
                    y='count',
                    labels={'month': '월', 'count': '관람 편수'},
                    color='count',
                    color_continuous_scale=['#fecaca', '#f87171', '#ef4444'],
                    template="plotly_white"
                )
                fig_monthly.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    coloraxis_showscale=False,
                    margin=dict(l=20, r=20, t=10, b=20),
                    height=350
                )
                st.plotly_chart(fig_monthly, use_container_width=True, config={'displayModeBar': False})
                
            with col_right:
                st.markdown("<h3 style='color: #1e293b; font-weight:700;'>📎 장르별 분포도</h3>", unsafe_allow_html=True)
                genre_count = summary_df['genre'].value_counts().reset_index(name='count')
                
                fig_genre = px.pie(
                    genre_count, 
                    values='count', 
                    names='genre',
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                    template="plotly_white"
                )
                fig_genre.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=20, r=20, t=10, b=20),
                    height=350
                )
                fig_genre.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_genre, use_container_width=True, config={'displayModeBar': False})
                
            st.markdown("<br>", unsafe_allow_html=True)
            
            col_b1, col_b2 = st.columns(2)
            
            with col_b1:
                st.markdown("<h3 style='color: #1e293b; font-weight:700;'>⭐ 별점 분포</h3>", unsafe_allow_html=True)
                rating_counts = summary_df['rating'].value_counts().sort_index().reset_index(name='count')
                
                fig_rating = px.line(
                    rating_counts, 
                    x='rating', 
                    y='count',
                    markers=True,
                    labels={'rating': '별점', 'count': '영화 수'},
                    template="plotly_white"
                )
                fig_rating.update_traces(line_color='#f59e0b', marker=dict(size=10, color='#d97706'))
                fig_rating.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=20, r=20, t=10, b=20),
                    height=350,
                    xaxis=dict(dtick=0.5)
                )
                st.plotly_chart(fig_rating, use_container_width=True, config={'displayModeBar': False})
                
            with col_b2:
                st.markdown("<h3 style='color: #1e293b; font-weight:700;'>👥 누구와 함께 보았을까?</h3>", unsafe_allow_html=True)
                companion_count = summary_df['companion'].value_counts().reset_index(name='count')
                
                fig_companion = px.bar(
                    companion_count,
                    x='count',
                    y='companion',
                    orientation='h',
                    labels={'count': '관람 편수', 'companion': '동반자'},
                    template="plotly_white"
                )
                fig_companion.update_traces(marker_color='#cbd5e1')
                fig_companion.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    coloraxis_showscale=False,
                    margin=dict(l=20, r=20, t=10, b=20),
                    height=350,
                    xaxis=dict(dtick=1)
                )
                st.plotly_chart(fig_companion, use_container_width=True, config={'displayModeBar': False})


# ----------------- [메뉴 2: 영화 아카이브] -----------------
elif menu == "영화아카이브":
    st.markdown('<h1 class="cinema-title" style="color: black;">영화아카이브</h1>', unsafe_allow_html=True)
    st.markdown('<p class="cinema-subtitle">기억해두고 싶은 순간들의 기록</p>', unsafe_allow_html=True)
    
    if df.empty:
        st.info("아직 등록된 영화가 없습니다. '새 영화 기록하기' 메뉴에서 첫 번째 영화를 기록해 보세요!")
    else:
        # 연도 컬럼 생성
        df['year'] = pd.to_datetime(df['date']).dt.year
        years_list = ["전체"] + sorted(df['year'].unique().tolist(), reverse=False)
        
        col_search, col_year, col_genre, col_sort = st.columns([2, 1, 1, 1])
        
        with col_search:
            search_query = st.text_input("🔍 제목 또는 한줄평 검색", "")
            
        with col_year:
            selected_year = st.selectbox("📅 연도 필터", years_list)
            
        with col_genre:
            genres_list = ["전체"] + list(df['genre'].unique())
            selected_genre = st.selectbox("🎭 장르 필터", genres_list)
            
        with col_sort:
            sort_option = st.selectbox("⏳ 정렬 기준", ["과거 관람 순", "최신 관람 순", "평점 높은 순", "평점 낮은 순"])
            
        filtered_df = df.copy()
        
        if selected_year != "전체":
            filtered_df = filtered_df[filtered_df['year'] == selected_year]

        
        if search_query:
            filtered_df = filtered_df[
                filtered_df['title'].str.contains(search_query, case=False, na=False) |
                filtered_df['review'].str.contains(search_query, case=False, na=False) |
                filtered_df['notes'].str.contains(search_query, case=False, na=False)
            ]
            
        if selected_genre != "전체":
            filtered_df = filtered_df[filtered_df['genre'] == selected_genre]
            
        if sort_option == "최신 관람 순":
            filtered_df = filtered_df.sort_values(by='date', ascending=False)
        elif sort_option == "과거 관람 순":
            filtered_df = filtered_df.sort_values(by='date', ascending=True)
        elif sort_option == "평점 높은 순":
            filtered_df = filtered_df.sort_values(by='rating', ascending=False)
        elif sort_option == "평점 낮은 순":
            filtered_df = filtered_df.sort_values(by='rating', ascending=True)
        else:
            # 기본 정렬: 날짜 오름차순
            filtered_df['date'] = pd.to_datetime(filtered_df['date'])
            filtered_df = filtered_df.sort_values(by='date', ascending=True)
            
        cols_per_row = 3
        rows = (len(filtered_df) + cols_per_row - 1) // cols_per_row
        
        for r in range(rows):
            cols = st.columns(cols_per_row)
            for c in range(cols_per_row):
                idx = r * cols_per_row + c
                if idx < len(filtered_df):
                    row = filtered_df.iloc[idx]
                    with cols[c]:
                        if st.session_state.get('edit_mode_title') == row['title']:
                            st.markdown(f"<div style='background:#f1f5f9; padding:15px; border-radius:12px; border:2px dashed #94a3b8; margin-bottom: 1rem;'>", unsafe_allow_html=True)
                            st.markdown(f"<span style='font-weight:700; color:#334155;'>✏️ '{row['title']}' 수정 중</span>", unsafe_allow_html=True)
                            with st.form(key=f"edit_form_{row['title']}", clear_on_submit=False):
                                e_title = st.text_input("제목", value=row['title'])
                                genres = ["드라마", "액션/범죄", "SF/판타지", "로맨스/멜로", "스릴러/미스터리", "코미디", "애니메이션", "공포/오컬트", "다큐멘터리"]
                                try: g_idx = genres.index(row['genre'])
                                except: g_idx = 0
                                e_genre = st.selectbox("장르", genres, index=g_idx)
                                e_rating = st.slider("별점", min_value=0.5, max_value=5.0, value=float(row['rating']), step=0.5)
                                e_review = st.text_input("한줄평", value=row['review'])
                                comps = ["혼자", "연인", "친구", "가족", "동료"]
                                try: c_idx = comps.index(row['companion'])
                                except: c_idx = 0
                                e_companion = st.selectbox("동반자", comps, index=c_idx)
                                e_runtime = st.number_input("러닝타임 (분)", min_value=1, max_value=500, value=int(row['runtime']) if pd.notnull(row['runtime']) else 120)
                                
                                c_s, c_c = st.columns(2)
                                with c_s:
                                    submit_save = st.form_submit_button("저장")
                                with c_c:
                                    submit_cancel = st.form_submit_button("취소")
                                    
                                if submit_save:
                                    df_edit = load_data(DATA_PATH)
                                    idx_list = df_edit.index[df_edit['title'] == row['title']].tolist()
                                    if idx_list:
                                        ti = idx_list[0]
                                        df_edit.at[ti, 'title'] = e_title
                                        df_edit.at[ti, 'genre'] = e_genre
                                        df_edit.at[ti, 'rating'] = e_rating
                                        df_edit.at[ti, 'review'] = e_review
                                        df_edit.at[ti, 'companion'] = e_companion
                                        df_edit.at[ti, 'runtime'] = e_runtime
                                        save_data(df_edit, DATA_PATH)
                                    st.session_state['edit_mode_title'] = None
                                    st.rerun()
                                if submit_cancel:
                                    st.session_state['edit_mode_title'] = None
                                    st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)
                            
                        else:
                            has_poster = False
                            if isinstance(row['poster_path'], str) and row['poster_path']:
                                p_path = str(row['poster_path']).strip()
                                if p_path.startswith("data:image"):
                                    st.markdown(f"""
                                    <div style="width: 100%; aspect-ratio: 1 / 1.4; overflow: hidden; border-radius: 12px; margin-bottom: 10px;">
                                        <img src="{p_path}" style="width: 100%; height: 100%; object-fit: cover;" />
                                    </div>
                                    """, unsafe_allow_html=True)
                                    has_poster = True
                                else:
                                    full_poster_path = os.path.join(POSTER_DIR, p_path)
                                    if os.path.exists(full_poster_path):
                                        try:
                                            from PIL import ImageOps
                                            img = Image.open(full_poster_path)
                                            img = ImageOps.fit(img, (600, 840), Image.Resampling.LANCZOS)
                                            st.image(img, use_container_width=True)
                                            has_poster = True
                                        except Exception as e:
                                            pass
                            
                            if not has_poster:
                                st.markdown(f"""
                                <div class="poster-placeholder">
                                    <span style="font-size: 3rem;">🎬</span>
                                    <div class="poster-placeholder-title">{row['title']}</div>
                                    <div style="color: #64748b; font-size:0.8rem; margin-top:5px;">{row['genre']}</div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                            st.markdown(f"""
                            <div style="padding: 0.5rem 0;">
                                <h4 style="margin: 0; color: #0f172a; font-size: 1.1rem; font-weight:700; height: 2.8rem; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">{row['title']}</h4>
                                <div class="star-rating">{get_star_string(row['rating'])} <span style="color:#64748b; font-size:0.85rem;">({row['rating']})</span></div>
                                <div style="font-size: 0.8rem; color: #475569; margin-bottom: 5px;">
                                    📅 {row['date'].strftime('%Y-%m-%d')} | 👥 {row['companion']} | 🎬 {row['genre']} ({row['runtime']}분)
                                </div>
                                <p style="font-style: italic; font-size: 0.85rem; color: #334155; line-height:1.4; height: 2.5rem; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">
                                    "{row['review']}"
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown("<br>", unsafe_allow_html=True)
                            bc1, bc2 = st.columns(2)
                            with bc1:
                                st.button("✏️ 수정", key=f"btn_edit_{row['title']}", on_click=set_edit_mode_callback, args=(row['title'],), use_container_width=True)
                            with bc2:
                                st.button("🗑️ 삭제", key=f"btn_del_{row['title']}", on_click=delete_movie_callback, args=(row['title'],), use_container_width=True)

# ----------------- [메뉴 3: 새 영화 기록하기] -----------------
elif menu == "새 영화 기록하기":
    st.markdown('<h1 class="cinema-title">ADD RECORD</h1>', unsafe_allow_html=True)
    st.markdown('<p class="cinema-subtitle">새로운 영화의 여정을 내 아카이브에 추가하세요</p>', unsafe_allow_html=True)
    
    with st.container():
        with st.form("new_movie_form", clear_on_submit=True):
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                title = st.text_input("🎬 영화 제목", placeholder="예: 아바타: 물의 길")
                genre = st.selectbox("🎭 장르", [
                    "드라마", "액션/범죄", "SF/판타지", "로맨스/멜로", 
                    "스릴러/미스터리", "코미디", "애니메이션", "공포/오컬트", "다큐멘터리"
                ])
                companion = st.selectbox("👥 동반자", ["혼자", "연인", "친구", "가족", "동료"])
                
            with col_t2:
                st.markdown("<div style='font-size: 0.9rem; font-weight: 600; margin-bottom: 0.5rem; color: #334155;'>📅 관람일</div>", unsafe_allow_html=True)
                col_y, col_m, col_d = st.columns([1.5, 1, 1])
                with col_y:
                    year = st.selectbox("연도", range(2000, datetime.today().year + 2), index=datetime.today().year - 2000, label_visibility="collapsed")
                with col_m:
                    month = st.selectbox("월", range(1, 13), index=datetime.today().month - 1, label_visibility="collapsed")
                with col_d:
                    day = st.selectbox("일", range(1, 32), index=datetime.today().day - 1, label_visibility="collapsed")
                date = f"{year}-{month:02d}-{day:02d}"
                
                rating = st.slider("⭐ 별점", min_value=0.5, max_value=5.0, value=4.0, step=0.5)
                runtime = st.number_input("⏳ 러닝타임 (분)", min_value=1, max_value=500, value=120)
                
            review = st.text_input("💬 한줄평", placeholder="영화를 관람한 느낌을 한 줄로 요약해 주세요.")
            
            uploaded_file = st.file_uploader("🖼️ 포스터 이미지 첨부")
            
            submit_btn = st.form_submit_button("📝 레코드 저장하기")
            
            if submit_btn:
                if not title or not review:
                    st.error("영화 제목과 한줄평은 필수 입력 사항입니다.")
                else:
                    poster_val = ""
                    if uploaded_file is not None:
                        try:
                            import base64
                            from io import BytesIO
                            from PIL import ImageOps
                            
                            image = Image.open(uploaded_file)
                            if image.mode != 'RGB':
                                image = image.convert('RGB')
                            
                            image = ImageOps.fit(image, (300, 420), Image.Resampling.LANCZOS)
                            
                            buffered = BytesIO()
                            image.save(buffered, format="JPEG", quality=75)
                            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                            poster_val = f"data:image/jpeg;base64,{img_str}"
                        except Exception as e:
                            st.warning(f"이미지 변환 중 오류 발생: {e}. 포스터 없이 등록됩니다.")
                            poster_val = ""
                    
                    new_row = {
                        'title': title,
                        'date': pd.to_datetime(date),
                        'rating': float(rating),
                        'genre': genre,
                        'review': review,
                        'poster_path': poster_val,
                        'runtime': int(runtime),
                        'companion': companion,
                        'award_nominee': "None",
                        'notes': ""
                    }
                    
                    current_df = load_data(DATA_PATH)
                    new_df = pd.DataFrame([new_row])
                    updated_df = pd.concat([current_df, new_df], ignore_index=True)
                    
                    save_data(updated_df, DATA_PATH)
                    
                    st.success(f"🎉 영화 '{title}'이(가) 기록에 정상적으로 추가되었습니다!")
