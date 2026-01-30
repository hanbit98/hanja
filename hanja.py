import streamlit as st
import pandas as pd
import random

# 페이지 설정
st.set_page_config(page_title="한자능력검정시험 연습", page_icon="📝")

# 데이터 로드 함수
@st.cache_data
def load_data():
    try:
        # CSV 파일을 읽어옵니다.
        df = pd.read_csv("hanja.csv")
        return df
    except FileNotFoundError:
        st.error("CSV 파일을 찾을 수 없습니다. 파일명을 확인해주세요.")
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
    # 급수에 따른 데이터 필터링 [cite: 116, 43, 79, 74]
    if level == "6급":
        allowed_levels = ["8급", "7급", "6급"]
    else: # 5급
        allowed_levels = ["8급", "7급", "6급", "준5급", "5급"]
    
    # 해당 급수 범위 내의 한자들만 추출
    pool = df[df['급수'].isin(allowed_levels)].to_dict('records')
    
    # 문제 추출
    sample_count = min(len(pool), count)
    st.session_state.questions = random.sample(pool, sample_count)
    st.session_state.current_idx = 0
    st.session_state.score = 0
    st.session_state.wrong_answers = []
    st.session_state.test_started = True
    st.session_state.finished = False
    st.session_state.mode = mode

# 메인 화면
st.title("🏮 한자능력검정시험 대비 테스트")

if not st.session_state.test_started and not st.session_state.finished:
    st.subheader("테스트 설정")
    level = st.selectbox("목표 급수를 선택하세요", ["6급", "5급"])
    mode = st.selectbox("테스트 모드", ["한자 보고 뜻/음 맞히기", "뜻/음 보고 한자 맞히기"])
    count = st.select_slider("문제 개수", options=[20, 30, 40])
    
    if st.button("테스트 시작", type="primary"):
        start_test(level, mode, count)
        st.rerun()

elif st.session_state.test_started and not st.session_state.finished:
    # 진행도 표시
    q_len = len(st.session_state.questions)
    idx = st.session_state.current_idx
    st.progress((idx) / q_len)
    st.write(f"문제 {idx + 1} / {q_len}")

    # 현재 문제 정보
    current_q = st.session_state.questions[idx]
    
    # 모드에 따른 문제 및 정답 설정
    if st.session_state.mode == "한자 보고 뜻/음 맞히기":
        question_text = current_q['한자']
        correct_answer = f"{current_q['훈(뜻)']} {current_q['음']}"
        # 오답 후보군: 현재 급수 범위 내에서 정답을 제외한 나머지
        wrong_pool = [f"{item['훈(뜻)']} {item['음']}" for item in st.session_state.questions if item['한자'] != current_q['한자']]
    else:
        question_text = f"{current_q['훈(뜻)']} {current_q['음']}"
        correct_answer = current_q['한자']
        # 오답 후보군: 현재 급수 범위 내에서 정답을 제외한 나머지
        wrong_pool = [item['한자'] for item in st.session_state.questions if item['한자'] != current_q['한자']]

    # 한자 크게 표시
    st.markdown(f"<h1 style='text-align: center; font-size: 100px; color: #333;'>{question_text}</h1>", unsafe_allow_html=True)

    # 보기 생성 (4지 선다)
    # 오답이 부족할 경우 전체 데이터에서 보충
    if len(wrong_pool) < 3:
        options = list(set(wrong_pool))
    else:
        options = random.sample(list(set(wrong_pool)), 3)
        
    options.append(correct_answer)
    random.shuffle(options)

    # 정답 체크 함수
    def check_ans(picked):
        if picked == correct_answer:
            st.session_state.score += 1
        else:
            st.session_state.wrong_answers.append(current_q)
        
        # 인덱스 변경 등 상태 업데이트만 수행
        if st.session_state.current_idx + 1 < q_len:
            st.session_state.current_idx += 1
        else:
            st.session_state.finished = True
        # st.rerun()을 삭제해도 버튼 클릭 후 자동으로 화면이 갱신됩니다.

    # 보기 버튼 배치
    cols = st.columns(2)
    for i, opt in enumerate(options):
        with cols[i % 2]:
            st.button(opt, key=f"btn_{i}", use_container_width=True, on_click=check_ans, args=(opt,))

elif st.session_state.finished:
    st.balloons()
    st.header("🎉 테스트 결과")
    st.write(f"### 최종 점수: {st.session_state.score} / {len(st.session_state.questions)}")
    
    if st.session_state.wrong_answers:
        st.warning(f"{len(st.session_state.wrong_answers)}문제를 틀렸습니다.")
        if st.button("오답 노트 (틀린 문제만 다시 풀기)"):
            st.session_state.questions = list(st.session_state.wrong_answers)
            st.session_state.wrong_answers = []
            st.session_state.current_idx = 0
            st.session_state.score = 0
            st.session_state.finished = False
            st.rerun()
    else:
        st.success("만점입니다! 다음 단계로 넘어가도 좋겠어요!")

    if st.button("처음으로 돌아가기"):
        st.session_state.test_started = False
        st.session_state.finished = False
        st.rerun()


