import streamlit as st
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# --------------------------------------------------------------------------
# 1. API 설정 및 데이터 로드 함수 (더 안정적인 방식으로 수정)
# --------------------------------------------------------------------------

API_KEY = "0b594b395a0248a3a0a68f3b79483427"
BASE_URL = f"https://www.career.go.kr/cnet/openapi/getOpenApi?apiKey={API_KEY}&svcType=api&svcCode=SCHOOL&contentType=xml&gubun=high_list"

@st.cache_data(ttl=3600) # 1시간 동안 전체 결과를 캐싱
def load_all_school_data_robust():
    """
    totalCount 없이, 데이터가 없을 때까지 페이지를 넘기며 모든 데이터를 가져오는 안정적인 함수
    """
    all_schools = []
    page = 1
    per_page = 100 # 한 번에 100개씩 요청

    with st.spinner('전체 학교 데이터를 불러오는 중입니다... 잠시만 기다려주세요.'):
        while True:
            try:
                # 현재 페이지 데이터 요청
                response = requests.get(f"{BASE_URL}&perPage={per_page}&page={page}")
                response.raise_for_status()
                root = ET.fromstring(response.content)

                # 현재 페이지의 content 목록을 찾음
                contents = root.findall('.//content')
                
                # 만약 content가 하나도 없다면, 마지막 페이지라는 의미이므로 반복 중단
                if not contents:
                    break

                # 데이터가 있다면 all_schools 리스트에 추가
                for content in contents:
                    school_info = {
                        'schoolName': content.findtext('schoolName'), 'region': content.findtext('region'),
                        'totalCount': content.findtext('totalCount'), 'major': content.findtext('major'),
                        'subject': content.findtext('subject'), 'chart': content.findtext('chart'),
                        'cert': content.findtext('cert')
                    }
                    all_schools.append(school_info)
                
                # 다음 페이지로 이동
                page += 1

            except requests.exceptions.RequestException as e:
                st.error(f"API 요청 중 오류가 발생했습니다: {e}")
                return None
            except ET.ParseError as e:
                st.error(f"XML 데이터를 파싱하는 중 오류가 발생했습니다: {e}")
                return None
    
    return all_schools

# --------------------------------------------------------------------------
# 2. Streamlit 앱 UI 구성 (이하 동일)
# --------------------------------------------------------------------------

st.set_page_config(page_title="전국 특성화고 학과 검색", page_icon="🏫", layout="wide")

if 'search_history' not in st.session_state:
    st.session_state.search_history = []

st.title("🏫 전국 특성화/특수목적 고등학교 학과 검색")

# --- 데이터 로드 ---
school_data = load_all_school_data_robust()

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
    