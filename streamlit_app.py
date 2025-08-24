import streamlit as st
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import time

# --------------------------------------------------------------------------
# 1. API 설정 및 데이터 로드 함수 (서울 지역 한정)
# --------------------------------------------------------------------------

API_KEY = "0b594b395a0248a3a0a68f3b79483427"
# [변경점!] 서울 지역으로 범위를 좁히는 파라미터(searchRegion=100260)를 추가했습니다.
BASE_URL = f"https://www.career.go.kr/cnet/openapi/getOpenApi?apiKey={API_KEY}&svcType=api&svcCode=SCHOOL&contentType=xml&gubun=high_list&searchRegion=100260"

@st.cache_data(ttl=3600)
def load_all_school_data_api_definitive():
    # 내부 로직은 이전의 최종 API 코드와 동일합니다.
    all_schools = []
    page = 1
    per_page = 100
    previous_page_content = None

    MAX_RETRIES = 3
    RETRY_DELAY = 1

    with st.spinner('API 서버로부터 [서울 지역] 학교 데이터를 불러오는 중입니다...'):
        while True:
            is_successful = False
            for attempt in range(MAX_RETRIES):
                try:
                    time.sleep(0.1)
                    response = requests.get(f"{BASE_URL}&perPage={per_page}&page={page}")
                    response.raise_for_status()
                    
                    current_page_content = response.content
                    
                    if current_page_content == previous_page_content:
                        is_successful = True
                        contents = []
                        break
                    
                    root = ET.fromstring(current_page_content)
                    contents = root.findall('.//content')

                    is_successful = True
                    break
                
                except requests.exceptions.RequestException:
                    time.sleep(RETRY_DELAY)
            
            if not is_successful:
                st.error(f"페이지 {page}의 데이터를 가져오는 데 최종 실패했습니다.")
                return None

            if not contents:
                break

            for content in contents:
                all_schools.append({
                    'schoolName': content.findtext('schoolName'), 'region': content.findtext('region'),
                    'major': content.findtext('major'), 'subject': content.findtext('subject'),
                    'chart': content.findtext('chart'), 'cert': content.findtext('cert')
                })
            
            previous_page_content = current_page_content
            page += 1
    
    MINIMUM_DATA_THRESHOLD = 5 # 서울 지역은 데이터가 적으므로 기준치를 5로 낮춥니다.
    if 0 < len(all_schools) < MINIMUM_DATA_THRESHOLD:
        st.error(f"API 서버가 비정상적으로 적은 수({len(all_schools)}개)의 데이터만 반환했습니다. 잠시 후 다시 시도해주세요.")
        return None

    return all_schools

# --------------------------------------------------------------------------
# 2. Streamlit 앱 UI 구성 (이하 동일)
# --------------------------------------------------------------------------
# ... (이하 UI 코드는 이전과 동일하므로 생략합니다. 그대로 두시면 됩니다)
st.set_page_config(page_title="전국 특성화고 학과 검색", page_icon="🏫", layout="wide")

if 'search_history' not in st.session_state:
    st.session_state.search_history = []

st.title("🏫 서울 특성화/특수목적 고등학교 학과 검색")

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
elif school_data is None:
     # load_all_school_data_api_definitive 함수에서 None을 반환했을 때 (오류 발생 시)
     st.warning("데이터 로딩에 실패했습니다. API 서버 상태가 불안정할 수 있습니다.")

with st.sidebar:
    st.header("🔍 검색 기록")
    if 'search_history' in st.session_state and st.session_state.search_history:
        st.text_area("기록:", value="\n".join(st.session_state.search_history), height=300, disabled=True)
    else:
        st.info("검색 기록이 없습니다.")
    st.caption("Powered by Streamlit & CareerNet API")