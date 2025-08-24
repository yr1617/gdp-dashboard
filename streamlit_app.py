import streamlit as st
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import math # 페이지 계산을 위해 math 라이브러리 추가

# --------------------------------------------------------------------------
# 1. API 설정 및 데이터 로드 함수 (페이지네이션 적용)
# --------------------------------------------------------------------------

API_KEY = "0b594b395a0248a3a0a68f3b79483427"
BASE_URL = f"https://www.career.go.kr/cnet/openapi/getOpenApi?apiKey={API_KEY}&svcType=api&svcCode=SCHOOL&contentType=xml&gubun=high_list"

# @st.cache_data는 여러 페이지를 로드할 때 매번 새로 실행되어야 하므로, 여기서는 함수 내부에서 캐시 대신 전체 결과를 캐시합니다.
@st.cache_data(ttl=3600) # 1시간 동안 전체 결과를 캐싱
def load_all_school_data():
    """
    페이지네이션을 통해 모든 학교 데이터를 가져오는 함수
    """
    all_schools = []
    page = 1
    per_page = 100 # 한 번에 100개씩 요청하는 것이 안정적입니다.
    
    try:
        # 1. 첫 페이지를 요청하여 전체 데이터 수를 파악합니다.
        first_response = requests.get(f"{BASE_URL}&perPage={per_page}&page={page}")
        first_response.raise_for_status()
        root = ET.fromstring(first_response.content)
        
        total_count_element = root.find('.//totalCount')
        if total_count_element is None:
            st.error("API 응답에서 전체 데이터 수를 찾을 수 없습니다.")
            return None
        
        total_count = int(total_count_element.text)
        if total_count == 0:
            return []

        # 2. 전체 페이지 수를 계산합니다.
        total_pages = math.ceil(total_count / per_page)
        
        st.info(f"총 {total_count}개 데이터를 {total_pages} 페이지에 걸쳐 불러옵니다...")
        progress_bar = st.progress(0, text="데이터 로딩 중...")

        # 3. 모든 페이지를 순회하며 데이터를 가져옵니다.
        for page in range(1, total_pages + 1):
            response = requests.get(f"{BASE_URL}&perPage={per_page}&page={page}")
            response.raise_for_status()
            root = ET.fromstring(response.content)
            
            for content in root.findall('.//content'):
                school_info = {
                    'schoolName': content.findtext('schoolName'), 'region': content.findtext('region'),
                    'totalCount': content.findtext('totalCount'), 'major': content.findtext('major'),
                    'subject': content.findtext('subject'), 'chart': content.findtext('chart'),
                    'cert': content.findtext('cert')
                }
                all_schools.append(school_info)
            
            # 진행 상황 업데이트
            progress_bar.progress(page / total_pages, text=f"데이터 로딩 중... ({page}/{total_pages} 페이지)")

        progress_bar.empty() # 로딩 완료 후 프로그레스 바 제거
        return all_schools

    except requests.exceptions.RequestException as e:
        st.error(f"API 요청 중 오류가 발생했습니다: {e}")
        return None
    except (ET.ParseError, TypeError, ValueError) as e:
        st.error(f"데이터를 처리하는 중 오류가 발생했습니다: {e}")
        return None

# --------------------------------------------------------------------------
# 2. Streamlit 앱 UI 구성 (이하 동일)
# --------------------------------------------------------------------------

st.set_page_config(page_title="전국 특성화고 학과 검색", page_icon="🏫", layout="wide")

if 'search_history' not in st.session_state:
    st.session_state.search_history = []

st.title("🏫 전국 특성화/특수목적 고등학교 학과 검색")

# --- 데이터 로드 ---
school_data = load_all_school_data()

if school_data is not None: # 데이터가 빈 리스트일 수도 있으므로 None만 체크
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
    