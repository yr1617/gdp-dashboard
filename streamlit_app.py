import streamlit as st
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import time

# --------------------------------------------------------------------------
# 1. API 설정 및 데이터 로드 함수 (모든 방어 로직이 포함된 최종판)
# --------------------------------------------------------------------------

API_KEY = "0b594b395a0248a3a0a68f3b79483427"
BASE_URL = f"https://www.career.go.kr/cnet/openapi/getOpenApi?apiKey={API_KEY}&svcType=api&svcCode=SCHOOL&contentType=xml&gubun=high_list"

@st.cache_data(ttl=3600) # 1시간 동안 API 호출 결과를 캐싱
def load_all_school_data_api_definitive():
    """
    재시도, 중복 데이터 감지, 최소 데이터 확인 로직을 모두 포함하여
    불안정한 API에 최대한 안정적으로 대응하는 최종 함수
    """
    all_schools = []
    page = 1
    per_page = 100
    previous_page_content = None # 이전 페이지 내용과 비교하기 위한 변수
    
    # --- 재시도 설정 ---
    MAX_RETRIES = 3 # 최대 3번까지 재시도
    RETRY_DELAY = 1 # 재시도 사이에 1초 대기

    with st.spinner('API 서버로부터 전체 학교 데이터를 불러오는 중입니다...'):
        while True:
            is_successful = False
            
            for attempt in range(MAX_RETRIES):
                try:
                    time.sleep(0.1) # 서버에 부담을 주지 않기 위한 최소한의 지연
                    response = requests.get(f"{BASE_URL}&perPage={per_page}&page={page}")
                    response.raise_for_status()
                    
                    current_page_content = response.content
                    
                    # [핵심 로직 1] 중복 데이터 감지 -> 무한 루프 방지
                    if current_page_content == previous_page_content:
                        # is_successful을 True로 설정하여 정상 종료로 처리
                        is_successful = True
                        contents = [] # 루프를 자연스럽게 종료시키기 위해 빈 리스트로 설정
                        break 
                    
                    root = ET.fromstring(current_page_content)
                    contents = root.findall('.//content')

                    is_successful = True
                    break # 성공 시 재시도 루프 탈출
                
                except requests.exceptions.RequestException:
                    # 실패 시 재시도 전 대기
                    time.sleep(RETRY_DELAY)
            
            if not is_successful:
                st.error(f"페이지 {page}의 데이터를 가져오는 데 최종 실패했습니다. API 서버가 불안정한 것 같습니다.")
                return None

            if not contents:
                break # 데이터가 없으면 정상적으로 종료

            for content in contents:
                all_schools.append({
                    'schoolName': content.findtext('schoolName'), 'region': content.findtext('region'),
                    'major': content.findtext('major'), 'subject': content.findtext('subject'),
                    'chart': content.findtext('chart'), 'cert': content.findtext('cert')
                })
            
            previous_page_content = current_page_content
            page += 1
    
    # [핵심 로직 2] 최소 데이터 개수 확인 -> '1개만 반환' 문제 방어
    MINIMUM_DATA_THRESHOLD = 10 
    if len(all_schools) < MINIMUM_DATA_THRESHOLD:
        st.error(f"API 서버가 비정상적으로 적은 수({len(all_schools)}개)의 데이터만 반환했습니다. 잠시 후 다시 시도해주세요.")
        return None

    return all_schools

# --------------------------------------------------------------------------
# 2. Streamlit 앱 UI 구성 (이전과 동일)
# --------------------------------------------------------------------------

st.set_page_config(page_title="전국 특성화고 학과 검색", page_icon="🏫", layout="wide")

if 'search_history' not in st.session_state:
    st.session_state.search_history = []

st.title("🏫 전국 특성화/특수목적 고등학교 학과 검색")

school_data = load_all_school_data_api_definitive()

if school_data:
    st.success(f"✅ 총 {len(school_data)}개의 학과 데이터를 성공적으로 불러왔습니다.")
    
    search_query = st.text_input(label="궁금한 학과 키워드를 입력하세요", placeholder="예: 디자인, 프로그래밍, 조리")

    if search_query:
        if search_query not in st.session_state.search_history:
            st.session_state.search_history.insert(0, f"[{datetime.now().strftime('%H:%M:%S')}] {search_query}")

        results = [s for s in school_data if s.get('major') and search_query.lower() in s['major'].lower()]

        st.divider()
        if results:
            st.success(f"'{search_query}'에 대한 검색 결과: 총 {len(results)}건")
            for item in results:
                with st.expander(f"**{item.get('schoolName', '정보 없음')}** - {item.get('major', '정보 없음')}"):
                    st.markdown(f"**🏫 학교명:** {item.get('schoolName', '정보 없음')} ({item.get('region', '정보 없음')})")
                    st.markdown(f"**📚 학과명:** {item.get('major', '정보 없음')}")
                    st.markdown(f"**📖 배우는 내용:** {item.get('subject', '정보 없음')}")
                    st.markdown(f"**🎓 졸업 후 진로:** {item.get('chart', '정보 없음')}")
                    st.markdown(f"**📜 취득 가능 자격증:** {item.get('cert', '정보 없음')}")
        else:
            st.warning(f"'{search_query}'에 대한 검색 결과가 없습니다.")

with st.sidebar:
    st.header("🔍 검색 기록")
    st.text_area("기록:", value="\n".join(st.session_state.search_history), height=300, disabled=True)
    st.caption("Powered by Streamlit & CareerNet API")
    