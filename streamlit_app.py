import streamlit as st
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# --------------------------------------------------------------------------
# 1. API 설정 및 데이터 로드 함수
# --------------------------------------------------------------------------

API_KEY = "0b594b395a0248a3a0a68f3b79483427"
API_URL = f"https://www.career.go.kr/cnet/openapi/getOpenApi?apiKey={API_KEY}&svcType=api&svcCode=SCHOOL&contentType=xml&gubun=high_list&perPage=1000"

@st.cache_data(ttl=3600)
def load_school_data():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        school_list = []
        for content in root.findall('.//content'):
            school_info = {
                'schoolName': content.findtext('schoolName'),
                'region': content.findtext('region'),
                'totalCount': content.findtext('totalCount'),
                'major': content.findtext('major'),
                'subject': content.findtext('subject'),
                'chart': content.findtext('chart'),
                'cert': content.findtext('cert')
            }
            school_list.append(school_info)
        return school_list
    except requests.exceptions.RequestException as e:
        st.error(f"API 요청 중 오류가 발생했습니다: {e}")
        return None
    except ET.ParseError as e:
        st.error(f"XML 데이터를 파싱하는 중 오류가 발생했습니다: {e}")
        return None

# --------------------------------------------------------------------------
# 2. Streamlit 앱 UI 구성
# --------------------------------------------------------------------------

st.set_page_config(page_title="전국 특성화고 학과 검색", page_icon="🏫", layout="wide")

if 'search_history' not in st.session_state:
    st.session_state.search_history = []

st.title("🏫 전국 특성화/특수목적 고등학교 학과 검색")
st.info("커리어넷 API를 활용하여 전국의 특성화고 및 특목고 학과 정보를 검색합니다.", icon="💡")

school_data = load_school_data()

# ==============================================================================
# ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ 진단 코드 추가 부분 ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
# ==============================================================================
if school_data:
    st.subheader("🔍 데이터 로딩 상태 확인 (디버깅용)")
    st.success(f"✅ 총 {len(school_data)}개의 학교 데이터를 성공적으로 불러왔습니다.")
    # 받아온 데이터 중 첫 5개를 샘플로 화면에 출력해봅니다.
    st.write("데이터 샘플 (처음 5개):", school_data[:5])
    st.divider()
# ==============================================================================
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲ 진단 코드 추가 부분 ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
# ==============================================================================

if school_data:
    search_query = st.text_input(
        label="궁금한 학과 키워드를 입력하세요 (예: 디자인, 프로그래밍, 조리)",
        placeholder="검색어를 입력하고 Enter를 누르세요."
    )

    if search_query:
        if search_query not in st.session_state.search_history:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.search_history.insert(0, f"[{now}] {search_query}")

        # 'major' 필드가 None인 경우를 방지하기 위해 먼저 확인합니다.
        results = [school for school in school_data if school['major'] and search_query.lower() in school['major'].lower()]

        st.divider()

        if results:
            st.success(f"'{search_query}'에 대한 검색 결과: 총 {len(results)}건")
            for idx, item in enumerate(results):
                with st.expander(f"**{item['schoolName']}** - {item['major']}"):
                    st.markdown(f"**🏫 학교명:** {item['schoolName']} ({item['region']})")
                    st.markdown(f"**📚 학과명:** {item['major']}")
                    st.markdown(f"**📖 배우는 내용:** {item['subject']}")
                    st.markdown(f"**🎓 졸업 후 진로:** {item['chart']}")
                    st.markdown(f"**📜 취득 가능 자격증:** {item['cert']}")
        else:
            st.warning(f"'{search_query}'에 대한 검색 결과가 없습니다. 다른 키워드로 검색해보세요.")
else:
    st.error("데이터를 불러오는데 실패했습니다. 잠시 후 다시 시도해주세요.")

with st.sidebar:
    st.header("🔍 검색 기록")
    if st.session_state.search_history:
        for record in st.session_state.search_history:
            st.text(record)
    else:
        st.info("아직 검색 기록이 없습니다.")
    st.divider()
    st.caption("Powered by Streamlit & CareerNet API")
    
