import streamlit as st
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import time # 재시도 사이의 대기 시간을 위해 time 라이브러리 추가

# --------------------------------------------------------------------------
# 1. API 설정 및 데이터 로드 함수 (재시도 및 지연 기능 추가)
# --------------------------------------------------------------------------

API_KEY = "0b594b395a0248a3a0a68f3b79483427"
BASE_URL = f"https://www.career.go.kr/cnet/openapi/getOpenApi?apiKey={API_KEY}&svcType=api&svcCode=SCHOOL&contentType=xml&gubun=high_list"

@st.cache_data(ttl=3600) # 1시간 동안 전체 결과를 캐싱
def load_all_school_data_final():
    """
    재시도(Retry) 로직과 지연(Delay)을 추가하여 서버 오류에 더욱 강력하게 대처하는 최종 함수
    """
    all_schools = []
    page = 1
    per_page = 100
    
    # --- 재시도 설정 ---
    MAX_RETRIES = 3 # 최대 3번까지 재시도
    RETRY_DELAY = 1 # 재시도 사이에 1초 대기

    with st.spinner('전체 학교 데이터를 불러오는 중입니다... (서버 오류 시 자동 재시도)'):
        while True:
            is_successful = False # 현재 페이지 요청 성공 여부
            
            for attempt in range(MAX_RETRIES):
                try:
                    # 각 요청 사이에 짧은 지연시간을 두어 서버 부담 감소
                    time.sleep(0.1) 
                    
                    response = requests.get(f"{BASE_URL}&perPage={per_page}&page={page}")
                    response.raise_for_status() # 오류 발생 시 여기서 예외를 일으킴
                    
                    root = ET.fromstring(response.content)
                    contents = root.findall('.//content')
                    
                    is_successful = True # 성공했으므로 표시
                    break # 재시도 루프 탈출
                
                except requests.exceptions.RequestException as e:
                    # 재시도 전 대기
                    st.warning(f"페이지 {page} 로딩 실패 (시도 {attempt + 1}/{MAX_RETRIES})... {RETRY_DELAY}초 후 재시도합니다. 오류: {e}")
                    time.sleep(RETRY_DELAY)
            
            # 최대 재시도 후에도 실패했다면 전체 프로세스 중단
            if not is_successful:
                st.error(f"페이지 {page}의 데이터를 가져오는 데 최종적으로 실패했습니다. 네트워크 상태를 확인하거나 잠시 후 다시 시도해주세요.")
                return None

            # 만약 content가 하나도 없다면, 마지막 페이지이므로 전체 루프 중단
            if not contents:
                break

            for content in contents:
                school_info = {
                    'schoolName': content.findtext('schoolName'), 'region': content.findtext('region'),
                    'totalCount': content.findtext('totalCount'), 'major': content.findtext('major'),
                    'subject': content.findtext('subject'), 'chart': content.findtext('chart'),
                    'cert': content.findtext('cert')
                }
                all_schools.append(school_info)
            
            page += 1
    
    return all_schools

# --------------------------------------------------------------------------
# 2. Streamlit 앱 UI 구성 (이하 동일)
# --------------------------------------------------------------------------

st.set_page_config(page_title="전국 특성화고 학과 검색", page_icon="🏫", layout="wide")

if 'search_history' not in st.session_state:
    st.session_state.search_history = []

st.title("🏫 전국 특성화/특수목적 고등학교 학과 검색")

school_data = load_all_school_data_final()

if school_data is not None:
    st.success(f"✅ 총 {len(school_data)}개의 학교 데이터를 성공적으로 불러왔습니다.")
    
    search_query = st.text_input(
        label="궁금한 학과 키워드를 입력하세요 (예: 디자인, 프로그래밍, 조리)",
        placeholder="검색어를 입력하고 Enter를 누르세요."
    )

    if search_query:
        if search_query not in st.session_state.search_history:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.search_history.insert(0, f"[{now}] {search_query}")

        results = [school for school in school_data if school['major'] and search_query.lower() in school['major'].lower()]

        st.divider()

        if results:
            st.success(f"'{search_query}'에 대한 검색 결과: 총 {len(results)}건")
            for item in results:
                with st.expander(f"**{item['schoolName']}** - {item['major']}"):
                    st.markdown(f"**🏫 학교명:** {item['schoolName']} ({item['region']})")
                    st.markdown(f"**📚 학과명:** {item['major']}")
                    st.markdown(f"**📖 배우는 내용:** {item['subject']}")
                    st.markdown(f"**🎓 졸업 후 진로:** {item['chart']}")
                    st.markdown(f"**📜 취득 가능 자격증:** {item['cert']}")
        else:
            st.warning(f"'{search_query}'에 대한 검색 결과가 없습니다. 다른 키워드로 검색해보세요.")
else:
    st.error("데이터를 불러오는데 실패했습니다. 네트워크 상태를 확인하거나 잠시 후 다시 시도해주세요.")


with st.sidebar:
    st.header("🔍 검색 기록")
    if st.session_state.search_history:
        for record in st.session_state.search_history:
            st.text(record)
    else:
        st.info("아직 검색 기록이 없습니다.")
    st.divider()
    st.caption("Powered by Streamlit & CareerNet API")
    