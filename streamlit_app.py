import streamlit as st
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import time

# --------------------------------------------------------------------------
# 1. API 설정 및 데이터 로드 함수 (중복 데이터 감지 기능 추가)
# --------------------------------------------------------------------------

API_KEY = "0b594b395a0248a3a0a68f3b79483427"
BASE_URL = f"https://www.career.go.kr/cnet/openapi/getOpenApi?apiKey={API_KEY}&svcType=api&svcCode=SCHOOL&contentType=xml&gubun=high_list"

@st.cache_data(ttl=3600)
def load_all_school_data_definitive():
    """
    중복 데이터 감지 로직을 추가하여 무한 루프를 방지하는 가장 안정적인 최종 함수
    """
    all_schools = []
    page = 1
    per_page = 100
    previous_page_content = None # 이전 페이지 내용과 비교하기 위한 변수

    with st.spinner('전체 학교 데이터를 불러오는 중입니다... (무한 루프 방지 기능 작동 중)'):
        while True:
            try:
                time.sleep(0.05) # 서버에 부담을 주지 않기 위한 최소한의 지연
                response = requests.get(f"{BASE_URL}&perPage={per_page}&page={page}")
                response.raise_for_status()
                
                # 현재 페이지의 원본 XML 텍스트를 저장
                current_page_content = response.content
                
                # [핵심 로직] 현재 페이지 내용이 이전 페이지와 동일하면, 중복이므로 중단
                if current_page_content == previous_page_content:
                    break
                
                root = ET.fromstring(current_page_content)
                contents = root.findall('.//content')

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
                
                # 다음 루프를 위해 현재 페이지 내용을 previous_page_content에 저장
                previous_page_content = current_page_content
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

school_data = load_all_school_data_definitive()

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
    