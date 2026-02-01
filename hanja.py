import streamlit as st
import pandas as pd
import random
import os

# 페이지 설정
st.set_page_config(page_title="한자능력검정시험 연습", page_icon="📝")

# 데이터 로드 함수
@st.cache_data
def load_data():
    file_name = "hanja.csv"
    if not os.path.exists(file_name):
        st.error(f"❌ '{file_name}' 파일을 찾을 수 없습니다. 같은 폴더에 파일을 넣어주세요.")
        return None
    try:
        df = pd.read_csv(file_name, encoding='utf-8-sig')
        return df
    except Exception as e:
        st.error(f"❌ 파일을 읽는 중 오류가 발생했습니다: {e}")
        return None

df = load_data()

# 세션 상태 초기화
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = 0
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'wrong_answers' not in st.session_state:
    st.session_state.wrong_answers = []
if 'test_started' not in st.session_state:
    st.session_state.test_started = False
if 'finished' not in st.session_state:
    st.session_state.finished = False

def start_test(level, mode, count):
    if df is None: return
    # 급수별 범위 필터링
    allowed_levels = ["8급", "7급", "6급"] if level == "6급" else ["8급", "7급", "6급", "준5급", "5급"]
    pool = df[df['급수'].isin(allowed_levels)].to_dict('records')
    
    # 문제 무작위 추출
    sample_count = min(len(pool), count)
    st.session_state.questions = random.sample(pool, sample_count)
    st.session_state.current_idx = 0
    st.session_state.score = 0
    st.session_state.wrong_answers = []
    st.session_state.test_started = True
    st.session_state.finished = False
    st.session_state.mode = mode

# 메인 UI
st.title("🏮 한자능력검정시험 연습")

if df is not None:
    # 1. 설정 화면
    if not st.session_state.test_started and not st.session_state.finished:
        st.subheader("📋 시험 설정")
        level = st.selectbox("목표 급수 선택", ["6급", "5급"])
        mode = st.selectbox("문제 유형 선택", ["한자 보고 뜻/음 맞히기", "뜻/음 보고 한자 맞히기"])
        count = st.select_slider("문제 수 설정", options=[20, 30, 40])
        
        if st.button("시험 시작", type="primary", use_container_width=True):
            start_test(level, mode, count)
            st.rerun()

    # 2. 시험 진행 화면
    elif st.session_state.test_started and not st.session_state.finished:
        q_len = len(st.session_state.questions)
        idx = st.session_state.current_idx
        current_q = st.session_state.questions[idx]
        
        st.progress((idx) / q_len)
        st.write(f"**문제 {idx + 1} / {q_len}**")

        # 정답 체크 콜백 (st.rerun 제거)
        def check_ans(picked, correct):
            if picked == correct:
                st.session_state.score += 1
            else:
                st.session_state.wrong_answers.append(current_q)
            
            if st.session_state.current_idx + 1 < q_len:
                st.session_state.current_idx += 1
            else:
                st.session_state.finished = True

        # 모드별 디자인 설정
        if st.session_state.mode == "한자 보고 뜻/음 맞히기":
            # 한자가 문제로 나옴 (크게)
            question_html = f"<h1 style='text-align: center; font-size: 150px; margin-bottom: 0;'>{current_q['한자']}</h1>"
            correct_answer = f"{current_q['훈(뜻)']} {current_q['음']}"
            all_wrong = [f"{item['훈(뜻)']} {item['음']}" for _, item in df.iterrows() if item['한자'] != current_q['한자']]
            btn_font_size = "25px" # 보기는 한글이라 적당히
        else:
            # 뜻/음이 문제로 나옴 (적당히)
            question_html = f"<h2 style='text-align: center; font-size: 50px; color: #444; margin-bottom: 40px;'>{current_q['훈(뜻)']} {current_q['음']}</h2>"
            correct_answer = current_q['한자']
            all_wrong = [item['한자'] for _, item in df.iterrows() if item['한자'] != current_q['한자']]
            btn_font_size = "80px" # 한자 보기를 아주 크게!

        st.markdown(question_html, unsafe_allow_html=True)

        # 보기 4개 생성
        options = random.sample(list(set(all_wrong)), 3)
        options.append(correct_answer)
        random.shuffle(options)

        # 버튼 글자 크기 CSS 적용
        st.markdown(f"""
            <style>
                div.stButton > button p {{
                    font-size: {btn_font_size} !important;
                    font-weight: bold;
                }}
                div.stButton > button {{
                    height: 120px;
                    border-radius: 15px;
                }}
            </style>
        """, unsafe_allow_html=True)

        cols = st.columns(2)
        for i, opt in enumerate(options):
            with cols[i % 2]:
                st.button(opt, key=f"q_{idx}_opt_{i}", use_container_width=True, 
                          on_click=check_ans, args=(opt, correct_answer))

    # 3. 결과 화면
    elif st.session_state.finished:
        st.balloons()
        st.header("🎯 시험 결과")
        total = len(st.session_state.questions)
        score = st.session_state.score
        
        st.write(f"### 점수: **{score}** / {total} (정답률: {int(score/total*100)}%)")
        
        if st.session_state.wrong_answers:
            st.warning(f"틀린 문제가 {len(st.session_state.wrong_answers)}개 있습니다.")
            
            # 틀린 문제만 다시 풀기 버튼
            if st.button("🔥 틀린 문제만 다시 풀기", type="primary", use_container_width=True):
                st.session_state.questions = list(st.session_state.wrong_answers)
                st.session_state.wrong_answers = [] # 초기화
                st.session_state.current_idx = 0
                st.session_state.score = 0
                st.session_state.finished = False
                st.rerun()
        else:
            st.success("✨ 와우! 모든 문제를 다 맞혔어요! 완벽합니다!")

        if st.button("🏠 처음 화면으로", use_container_width=True):
            st.session_state.test_started = False
            st.session_state.finished = False
            st.rerun()