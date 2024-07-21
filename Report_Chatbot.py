import streamlit as st
import openai
import google.generativeai as genai
from streamlit_chat import message
import os
import requests
from streamlit_extras.colored_header import colored_header
import pandas as pd

# 페이지 구성 설정
st.set_page_config(layout="wide")

openai.api_key = st.secrets["secrets"]["OPENAI_API_KEY"]

if "page" not in st.session_state:
    st.session_state.page = "Home"

if "gpt_api_key" not in st.session_state:
    st.session_state.gpt_api_key = openai.api_key # gpt API Key

if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = st.secrets["secrets"]["GEMINI_API_KEY"]

# 세션 변수 체크
def check_session_vars():
    required_vars = ['selected_district', 'type_its']
    for var in required_vars:
        if var not in st.session_state:
            st.warning("필요한 정보가 없습니다. 사이드바에서 정보를 입력해 주세요.")
            st.stop()

# 사이드바에서 행정동 선택
selected_district = st.sidebar.selectbox(
    "(1) 오산시 행정동을 선택하세요:",
    ('중앙동', '남촌동', '신장동', '세마동', '초평동', '대원동')
)
st.session_state.selected_district = selected_district

# 사이드바에서 챗봇 선택
selected_chatbot = st.sidebar.selectbox(
    "(2) 원하는 챗봇을 선택하세요.",
    options=["GPT를 통한 오산시 맞춤형 교통체증 및 사고 저감 챗봇", "Gemini를 통한 오산시 맞춤형 교통체증 및 사고 저감 챗봇", "GPT를 통한 오산시 맞춤형 ITS 시설물 입지 선정 및 근거자료 챗봇", 
             "Gemini를 통한 오산시 맞춤형 ITS 시설물 입지 선정 및 근거자료 챗봇", "GPT를 활용한 오산시 스마트 교통도시계획 챗봇", "Gemini를 활용한 오산시 스마트 교통도시계획 챗봇"],
    help="선택한 챗봇에 따라 맞춤형 결과물을 제공합니다."
)

# 사이드바에서 ITS 시설물 선택 (해당 챗봇 선택 시)
if selected_chatbot in ["GPT를 통한 오산시 맞춤형 ITS 시설물 입지 선정 및 근거자료 챗봇", "Gemini를 통한 오산시 맞춤형 ITS 시설물 입지 선정 및 근거자료 챗봇"]:
    type_its = st.sidebar.selectbox(
        "(3) 원하는 ITS 시설물을 선택하세요:",
        ['교통관제용 CCTV', '스마트 횡단보도', '좌회전 감응 신호', '신호등 스마트폴', '가로등 스마트폴', 'CCTV 스마트폴', 
         '보안등 스마트폴', '다기능 스마트폴', '전기차충전 스마트폴', '드론 스마트폴', '어린이보호 구역통합 안전스마트폴', '한강공원 스마트폴']
    )
    st.session_state.type_its = type_its

# GPT 프롬프트 엔지니어링 함수 1
def gpt_prompt_1(user_input, selected_district):
    base_prompt = f"""
    너는 사용자가 요구한 오산시의 맞춤형 정보를 작성하는 친절하고 차분한 [오산시 공무원]이다. 
    사용자는 오산시의 맞춤형 정보를 원하는 [오산시 주민]이며, 사용자에게 정확하고 자세한 오산시 정보를 전달한다. 
    내가 채팅을 입력하면 아래의 <규칙>에 따라서 답변한다.

    <규칙>
    1. 사용자가 입력한 정보를 바탕으로 구체적이고 실용적인 솔루션을 제시해줘야 한다.
    2. 사용자의 요청에 따라 오산시의 특정 행정동에 대한 자세한 정보를 제공하고, 관련된 문제 해결 방안을 작성한다.
    3. 예시를 참고하여 내용을 더 발전시켜서 사용자에게 맞춤형 정보를 제공한다.
    4. 거짓말을 하면 안되며, 최대한 정확하고 사실인 정보로 답변한다. 
    5. 답변이 멈추거나 끊어졌으면, 사용자에게 어떤 응답을 받더라도 이어서 이전 내용을 답변한다.
    이 정보를 바탕으로 <규칙>에 따라서 답변한다.

    예시: 오산시 교통체증 및 사고 저감 방안
    - 교통체증이 심각한 지역: {selected_district}의 주요 교차로, 학교 주변
    - 사고 다발 지역: {selected_district}의 주요 도로
    - 해결 방안: 신호등 최적화, 스마트 횡단보도 설치, 실시간 교통 정보 제공, ITS 시설물 등

    사용자 입력: {user_input}
    행정동: {selected_district}
    """
    return base_prompt

# GPT 프롬프트 엔지니어링 함수 2
def gpt_prompt_2(user_input, selected_district):
    base_prompt = f"""
    너는 사용자가 요구한 오산시의 맞춤형 정보를 작성하는 친절하고 차분한 [ITS 시설물 관리자]이다. 
    사용자가 선택한 {st.session_state.type_its}(ITS 시설물)을 오산시 {selected_district}에 설치할 입지를 선정하고, 근거자료를 작성한다.
    사용자는 오산시의 맞춤형 정보를 원하는 [오산시 주민]이며, 사용자에게 정확하고 자세한 오산시 정보를 전달한다. 
    내가 채팅을 입력하면 아래의 <규칙>에 따라서 답변한다.

    <규칙>
    1. 사용자가 입력한 정보를 바탕으로 구체적이고 실용적인 솔루션을 제시해줘야 한다.
    2. 사용자의 요청에 따라 오산시의 특정 행정동에 대한 자세한 정보를 제공하고, 관련된 문제 해결 방안을 작성한다.
    3. 예시를 참고하여 내용을 더 발전시켜서 사용자에게 맞춤형 정보를 제공한다.
    4. 거짓말을 하면 안되며, 최대한 정확하고 사실인 정보로 답변한다. 
    5. 답변이 멈추거나 끊어졌으면, 사용자에게 어떤 응답을 받더라도 이어서 이전 내용을 답변한다.
    이 정보를 바탕으로 <규칙>에 따라서 답변한다.

    예시: ITS 시설물 정보
    [스마트폴 종류] / [세부 표준모델 (10종)] / [수용기능] / [적용환경]
    신호등 스마트폴	/ 신호등 스마트폴 기본형 / 신호등 + 스마트기능 / 차도
    신호등 스마트폴	/ 신호등+가로등 통합 스마트폴 / 신호등 + 가로등 + 스마트기능 / 차도
    신호등 스마트폴	/ 신호등+CCTV 통합 스마트폴 / 신호등 + CCTV + 스마트기능 / 차도
    신호등 스마트폴	/ 신호등+가로등+CCTV 통합 스마트폴 / 신호등 + 가로등 + CCTV + 스마트기능 / 차도
    가로등 스마트폴 / 가로등 스마트폴 기본형 / 가로등 + 스마트기능 /차도
    가로등 스마트폴 / 가로등+CCTV 통합 스마트폴 / 가로등 + CCTV + 스마트기능 / 차도
    CCTV 스마트폴 / CCTV 스마트폴 기본형 / CCTV + 스마트기능 / 차도, 공원, 골목길
    CCTV 스마트폴 / CCTV+보안등 통합 스마트폴 / CCTV + 보안등 + 스마트기능 / 공원, 골목길
    보안등 스마트폴 / 보안등 스마트폴 / 보안등 + 스마트기능 / 공원, 골목길
    다기능 스마트폴 / 다기능 통합 스마트폴 / 각종 등·지주 기능 + 스마트기능 / 차도, 공원, 골목길
    전기차충전 스마트폴	/ 가로등 전기차충전 스마트폴 / 가로등 + 급속 전기차충전 + 스마트기능 / 차도
    전기차충전 스마트폴	/ CCTV 전기차충전 스마트폴 / CCTV + 보안등 + 전기차충전 + 스마트기능 / 차도, 공원, 골목길
    전기차충전 스마트폴	/ 보안등 전기차충전 스마트폴 / 보안등 + 전기차충전 + 스마트기능 / 주차장, 골목길
    드론 스마트폴 / 드론 스마트폴 / CCTV + 공원등 + 드론스테이션 + 스마트기능 / 차도, 공원, 골목길
    어린이보호 구역통합 안전스마트폴 / 어린이보호구역 통합안전 스마트폴 / CCTV(안전+과속단속+불법주차) + 가로등(보안등) + 스마트기능 / 차도, 공원, 골목길
    한강공원 스마트폴 / 공원 CCTV 스마트폴 / CCTV + 공원등 + 스마트기능 / 한강공원    
    한강공원 스마트폴 / 드론 스마트폴 / CCTV + 공원등 + 드론스테이션 + 스마트기능 / 한강공원

    사용자 입력: {user_input}
    """
    return base_prompt

# GPT 프롬프트 엔지니어링 함수 2
def gpt_prompt_3(user_input, selected_district):
    base_prompt = f"""
    너는 현재 오산시 스마트 도시계획 보고서 작성을 위한 친절하고 차분한 [스마트 교통도시계획 챗봇]이다.
    사용자는 오산시의 맞춤형 정보를 원하는 [오산시 주민]이며, 사용자에게 정확하고 자세한 오산시 정보를 전달한다. 
    내가 채팅을 입력하면 아래의 <규칙>에 따라서 답변한다.

    <규칙>
    1. 사용자가 입력한 정보를 바탕으로 구체적이고 실용적인 솔루션을 제시해줘야 한다.
    2. 사용자의 요청에 따라 오산시의 특정 행정동에 대한 자세한 정보를 제공하고, 관련된 문제 해결 방안을 작성한다.
    3. 예시를 참고하여 내용을 더 발전시켜서 사용자에게 맞춤형 정보를 제공한다.
    4. 거짓말을 하면 안되며, 최대한 정확하고 사실인 정보로 답변한다. 
    5. 답변이 멈추거나 끊어졌으면, 사용자에게 어떤 응답을 받더라도 이어서 이전 내용을 답변한다.
    이 정보를 바탕으로 <규칙>에 따라서 답변한다.


    예시: 오산시 스마트 교통도시계획
    [추진전략]인프라의효율적운영과국토지능화 / [세부추진전략] 1. 네트워크형 교통망의 효율화와 대도시권 혼잡 해소, 2.인프라의 전략적 운영과 포용적 교통정책 추진, 3.지능형 국토·도시 공간 조성
    [스마트도시 관련 법·제도] / [유관 법]: 교통체계효율화법 / [해석]: 교통정책에 있어서 종합적인 조정을 강화하여 도로·철도·공항·항만 등 교통시설 간의 효율적인 교통체계구축을 촉진하고 그 이용의 효율을 높이는 것을 목적으로 함(제1조). 지능형 교통체계의 구축목표 및 추진전략, 분야별 지능형 교통체계의 구축 및 운영, 지능형 교통체계의 개발·보급 촉진 등을 기본목적으로 함
    [국내 스마트도시 동향]: 국내 스마트도시 사업추진은 국토교통부의 주관하에 진행되고 있으며, 과거 U-City 정책 방향과 유사하나 그보다 확장된 개념의 스마트시티 실증 단지 조성사업 시행
    [자동차등록대수현황]: 오산시와 인접 지자체 모두 1인당 자동차 등록 대수가 증가하는 추세이며 2021년 기준 오산시의 1인당 자동차 등록 대수 증가율은 인접 지자체와 경기도 전체와 비교할 때 높은 수준(이는 현재 오산시의 도시문제로 지적되는 불법주차,교통혼잡 문제를 더 심화시키는 요인으로 분석
    [교통사고 발생 현황]: 오산시 내 교통사고 건수는 지속적으로 증가했으며,증감률은 감소하고 있으나 교통사고 건수의 절대적인 수치에 대한 감소 대책이 필요
    [자동차 천 대당 교통사고 발생 건수]: 오산시 자동차 천 대당 교통사고 발생 건수는 2018년 8.3건으로 가장 높은 수치를 기록했으며, 2021년 7.2건으로 감소하였으나 여전히 경기도 평균 6.4건보다는 높음
    [횡단중 교통사고 현황]: 오산시 횡단중 교통사고 건수는 68건으로 기타 사고유형을 제외하면 40.2%로 가장 높은 교통사고 유형에 해당함. 또한, 오산시 횡단중 교통사고 비율 40.2%는 경기도 평균 횡단중 교통사고 비율 34.9%보다 높은 비율을 차지
    [통근거리 및 통행량]: 오산시의 평균 통근거리는 25.6km로 경기도 평균 통근거리(10.5km)보다 높게 나타남 / 오산시의 평균 통근거리 이상인 통근자의 비율은 전체 통근자 중 45.4%로 경기도 평균인 39.7%보다 높음
    [불법주차 현황]: 2021년 기준 총 1,645건의 주차 위반 사례 중 남촌동은 37%(617건)를 차지하며 구도심(궐동,원동 등)중심의 집중적인 분포를 보임 
    [교통 분야 검토 결과] 오산시 내부 교통량 예측 및 교통문제의 유형을 분석해 본 결과 1인당 자동차 등록 대수의 증가와 전반적으로 불량한 교통문화지수로 인해 내부 교통 혼잡문제와 다수의 교통사고를 유발 / ‘오산’과 ‘교통 분야’의 스마트도시 관련 키워드분석*을 통해 추출한 키워드를 바탕으로 주차장 현황, 불법주차현황,도로현황,대중교통 이용실태 등을 추가 분석한 결과 오산시는 외부 교통보다는 내부 교통으로 인한 도로 혼잡문제와 주차장 부족 문제가 도출된한편,우수한 교통 관련 기반시설을 활용한 높은 대중교통 이용률과 우수한 자전거도로 환경은 오산의 교통문제 해결의 핵심방안으로 도출 / 따라서 오산의 내부 교통혼잡도 저감을 위한 대중교통 활성화 및 오산시 내 이동수요를 고려한 맞춤형 스마트도시 서비스 필요
    
    
    사용자 입력: {user_input}
    행정동: {selected_district}
    """
    return base_prompt


# Gemini 프롬프트 엔지니어링 함수 1
def gemini_prompt_1(user_input, selected_district):
    base_prompt = f"""
    너는 사용자가 요구한 오산시의 맞춤형 정보를 작성하는 친절하고 차분한 [오산시 공무원]이다. 
    사용자는 오산시의 맞춤형 정보를 원하는 [오산시 주민]이며, 사용자에게 정확하고 자세한 오산시 정보를 전달한다. 
    내가 채팅을 입력하면 아래의 <규칙>에 따라서 답변한다.

    <규칙>
    1. 사용자가 입력한 정보를 바탕으로 구체적이고 실용적인 솔루션을 제시해줘야 한다.
    2. 사용자의 요청에 따라 오산시의 특정 행정동에 대한 자세한 정보를 제공하고, 관련된 문제 해결 방안을 작성한다.
    3. 예시를 참고하여 내용을 더 발전시켜서 사용자에게 맞춤형 정보를 제공한다.
    4. 거짓말을 하면 안되며, 최대한 정확하고 사실인 정보로 답변한다. 
    5. 답변이 멈추거나 끊어졌으면, 사용자에게 어떤 응답을 받더라도 이어서 이전 내용을 답변한다.
    이 정보를 바탕으로 <규칙>에 따라서 답변한다.

    예시: 오산시 교통체증 및 사고 저감 방안
    - 교통체증이 심각한 지역: {selected_district}의 주요 교차로, 학교 주변
    - 사고 다발 지역: {selected_district}의 주요 도로
    - 해결 방안: 신호등 최적화, 스마트 횡단보도 설치, 실시간 교통 정보 제공, ITS 시설물 등

    사용자 입력: {user_input}
    행정동: {selected_district}
    """
    return base_prompt

# Gemini 프롬프트 엔지니어링 함수 2
def gemini_prompt_2(user_input, selected_district):
    base_prompt = f"""
    너는 사용자가 요구한 오산시의 맞춤형 정보를 작성하는 친절하고 차분한 [ITS 시설물 관리자]이다. 
    사용자가 선택한 {st.session_state.type_its}(ITS 시설물)을 오산시 {selected_district}에 설치할 입지를 선정하고, 근거자료를 작성한다.
    사용자는 오산시의 맞춤형 정보를 원하는 [오산시 주민]이며, 사용자에게 정확하고 자세한 오산시 정보를 전달한다. 
    내가 채팅을 입력하면 아래의 <규칙>에 따라서 답변한다.

    <규칙>
    1. 사용자가 입력한 정보를 바탕으로 구체적이고 실용적인 솔루션을 제시해줘야 한다.
    2. 사용자의 요청에 따라 오산시의 특정 행정동에 대한 자세한 정보를 제공하고, 관련된 문제 해결 방안을 작성한다.
    3. 예시를 참고하여 내용을 더 발전시켜서 사용자에게 맞춤형 정보를 제공한다.
    4. 거짓말을 하면 안되며, 최대한 정확하고 사실인 정보로 답변한다. 
    5. 답변이 멈추거나 끊어졌으면, 사용자에게 어떤 응답을 받더라도 이어서 이전 내용을 답변한다.
    이 정보를 바탕으로 <규칙>에 따라서 답변한다.

    예시: ITS 시설물 정보
    [스마트폴 종류] / [세부 표준모델 (10종)] / [수용기능] / [적용환경]
    신호등 스마트폴	/ 신호등 스마트폴 기본형 / 신호등 + 스마트기능 / 차도
    신호등 스마트폴	/ 신호등+가로등 통합 스마트폴 / 신호등 + 가로등 + 스마트기능 / 차도
    신호등 스마트폴	/ 신호등+CCTV 통합 스마트폴 / 신호등 + CCTV + 스마트기능 / 차도
    신호등 스마트폴	/ 신호등+가로등+CCTV 통합 스마트폴 / 신호등 + 가로등 + CCTV + 스마트기능 / 차도
    가로등 스마트폴 / 가로등 스마트폴 기본형 / 가로등 + 스마트기능 /차도
    가로등 스마트폴 / 가로등+CCTV 통합 스마트폴 / 가로등 + CCTV + 스마트기능 / 차도
    CCTV 스마트폴 / CCTV 스마트폴 기본형 / CCTV + 스마트기능 / 차도, 공원, 골목길
    CCTV 스마트폴 / CCTV+보안등 통합 스마트폴 / CCTV + 보안등 + 스마트기능 / 공원, 골목길
    보안등 스마트폴 / 보안등 스마트폴 / 보안등 + 스마트기능 / 공원, 골목길
    다기능 스마트폴 / 다기능 통합 스마트폴 / 각종 등·지주 기능 + 스마트기능 / 차도, 공원, 골목길
    전기차충전 스마트폴	/ 가로등 전기차충전 스마트폴 / 가로등 + 급속 전기차충전 + 스마트기능 / 차도
    전기차충전 스마트폴	/ CCTV 전기차충전 스마트폴 / CCTV + 보안등 + 전기차충전 + 스마트기능 / 차도, 공원, 골목길
    전기차충전 스마트폴	/ 보안등 전기차충전 스마트폴 / 보안등 + 전기차충전 + 스마트기능 / 주차장, 골목길
    드론 스마트폴 / 드론 스마트폴 / CCTV + 공원등 + 드론스테이션 + 스마트기능 / 차도, 공원, 골목길
    어린이보호 구역통합 안전스마트폴 / 어린이보호구역 통합안전 스마트폴 / CCTV(안전+과속단속+불법주차) + 가로등(보안등) + 스마트기능 / 차도, 공원, 골목길
    한강공원 스마트폴 / 공원 CCTV 스마트폴 / CCTV + 공원등 + 스마트기능 / 한강공원    
    한강공원 스마트폴 / 드론 스마트폴 / CCTV + 공원등 + 드론스테이션 + 스마트기능 / 한강공원

    사용자 입력: {user_input}
    """
    return base_prompt

# Gemini 프롬프트 엔지니어링 함수 2
def gemini_prompt_3(user_input, selected_district):
    base_prompt = f"""
    너는 현재 오산시 스마트 도시계획 보고서 작성을 위한 친절하고 차분한 [스마트 교통도시계획 챗봇]이다.
    사용자는 오산시의 맞춤형 정보를 원하는 [오산시 주민]이며, 사용자에게 정확하고 자세한 오산시 정보를 전달한다. 
    내가 채팅을 입력하면 아래의 <규칙>에 따라서 답변한다.

    <규칙>
    1. 사용자가 입력한 정보를 바탕으로 구체적이고 실용적인 솔루션을 제시해줘야 한다.
    2. 사용자의 요청에 따라 오산시의 특정 행정동에 대한 자세한 정보를 제공하고, 관련된 문제 해결 방안을 작성한다.
    3. 예시를 참고하여 내용을 더 발전시켜서 사용자에게 맞춤형 정보를 제공한다.
    4. 거짓말을 하면 안되며, 최대한 정확하고 사실인 정보로 답변한다. 
    5. 답변이 멈추거나 끊어졌으면, 사용자에게 어떤 응답을 받더라도 이어서 이전 내용을 답변한다.
    이 정보를 바탕으로 <규칙>에 따라서 답변한다.

    예시: 오산시 스마트 교통도시계획
    [추진전략]인프라의효율적운영과국토지능화 / [세부추진전략] 1. 네트워크형 교통망의 효율화와 대도시권 혼잡 해소, 2.인프라의 전략적 운영과 포용적 교통정책 추진, 3.지능형 국토·도시 공간 조성
    [스마트도시 관련 법·제도] / [유관 법]: 교통체계효율화법 / [해석]: 교통정책에 있어서 종합적인 조정을 강화하여 도로·철도·공항·항만 등 교통시설 간의 효율적인 교통체계구축을 촉진하고 그 이용의 효율을 높이는 것을 목적으로 함(제1조). 지능형 교통체계의 구축목표 및 추진전략, 분야별 지능형 교통체계의 구축 및 운영, 지능형 교통체계의 개발·보급 촉진 등을 기본목적으로 함
    [국내 스마트도시 동향]: 국내 스마트도시 사업추진은 국토교통부의 주관하에 진행되고 있으며, 과거 U-City 정책 방향과 유사하나 그보다 확장된 개념의 스마트시티 실증 단지 조성사업 시행
    [자동차등록대수현황]: 오산시와 인접 지자체 모두 1인당 자동차 등록 대수가 증가하는 추세이며 2021년 기준 오산시의 1인당 자동차 등록 대수 증가율은 인접 지자체와 경기도 전체와 비교할 때 높은 수준(이는 현재 오산시의 도시문제로 지적되는 불법주차,교통혼잡 문제를 더 심화시키는 요인으로 분석
    [교통사고 발생 현황]: 오산시 내 교통사고 건수는 지속적으로 증가했으며,증감률은 감소하고 있으나 교통사고 건수의 절대적인 수치에 대한 감소 대책이 필요
    [자동차 천 대당 교통사고 발생 건수]: 오산시 자동차 천 대당 교통사고 발생 건수는 2018년 8.3건으로 가장 높은 수치를 기록했으며, 2021년 7.2건으로 감소하였으나 여전히 경기도 평균 6.4건보다는 높음
    [횡단중 교통사고 현황]: 오산시 횡단중 교통사고 건수는 68건으로 기타 사고유형을 제외하면 40.2%로 가장 높은 교통사고 유형에 해당함. 또한, 오산시 횡단중 교통사고 비율 40.2%는 경기도 평균 횡단중 교통사고 비율 34.9%보다 높은 비율을 차지
    [통근거리 및 통행량]: 오산시의 평균 통근거리는 25.6km로 경기도 평균 통근거리(10.5km)보다 높게 나타남 / 오산시의 평균 통근거리 이상인 통근자의 비율은 전체 통근자 중 45.4%로 경기도 평균인 39.7%보다 높음
    [불법주차 현황]: 2021년 기준 총 1,645건의 주차 위반 사례 중 남촌동은 37%(617건)를 차지하며 구도심(궐동,원동 등)중심의 집중적인 분포를 보임 
    [교통 분야 검토 결과] 오산시 내부 교통량 예측 및 교통문제의 유형을 분석해 본 결과 1인당 자동차 등록 대수의 증가와 전반적으로 불량한 교통문화지수로 인해 내부 교통 혼잡문제와 다수의 교통사고를 유발 / ‘오산’과 ‘교통 분야’의 스마트도시 관련 키워드분석*을 통해 추출한 키워드를 바탕으로 주차장 현황, 불법주차현황,도로현황,대중교통 이용실태 등을 추가 분석한 결과 오산시는 외부 교통보다는 내부 교통으로 인한 도로 혼잡문제와 주차장 부족 문제가 도출된한편,우수한 교통 관련 기반시설을 활용한 높은 대중교통 이용률과 우수한 자전거도로 환경은 오산의 교통문제 해결의 핵심방안으로 도출 / 따라서 오산의 내부 교통혼잡도 저감을 위한 대중교통 활성화 및 오산시 내 이동수요를 고려한 맞춤형 스마트도시 서비스 필요
    
    
    사용자 입력: {user_input}
    행정동: {selected_district}
    """
    return base_prompt

# 스트림 표시 함수
def stream_display(response, placeholder):
    text = ''
    for chunk in response:
        if parts := chunk.parts:
            if parts_text := parts[0].text:
                text += parts_text
                placeholder.write(text + "▌")
    return text

# Initialize chat history
if "gpt_messages" not in st.session_state:
    st.session_state.gpt_messages = [
        {"role": "system", "content": "GPT가 사용자에게 맞춤형 오산시 정보를 알려드립니다."}
    ]

if "gemini_messages" not in st.session_state:
    st.session_state.gemini_messages = [
        {"role": "model", "parts": [{"text": "Gemini가 사용자에게 맞춤형 오산시 정보를 알려드립니다."}]}
    ]

if selected_chatbot == "GPT를 통한 오산시 맞춤형 교통체증 및 사고 저감 챗봇":
    colored_header(
        label='GPT를 통한 오산시 맞춤형 교통체증 및 사고 저감 챗봇',
        description=None,
        color_name="gray-70",
    )

    # 세션 변수 체크
    check_session_vars()

    # 대화 초기화 버튼
    def on_clear_chat_gpt():
        st.session_state.gpt_messages = [
            {"role": "system", "content": "GPT가 사용자에게 맞춤형 오산시 정보를 알려드립니다."}
        ]

    st.button("대화 초기화", on_click=on_clear_chat_gpt)

    # 이전 메시지 표시
    for msg in st.session_state.gpt_messages:
        role = 'user' if msg['role'] == 'user' else 'assistant'
        with st.chat_message(role):
            st.write(msg['content'])

    # 사용자 입력 처리
    if prompt := st.chat_input("챗봇과 대화하기:"):
        # 사용자 메시지 추가
        st.session_state.gpt_messages.append({"role": "user", "content": prompt})
        with st.chat_message('user'):
            st.write(prompt)

        # 프롬프트 엔지니어링 적용
        enhanced_prompt = gpt_prompt_1(prompt, st.session_state.selected_district)

        # 모델 호출 및 응답 처리
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": enhanced_prompt}
                ] + st.session_state.gpt_messages,
                max_tokens=1500,
                temperature=0.8,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            text = response.choices[0]['message']['content']

            # 응답 메시지 표시 및 저장
            st.session_state.gpt_messages.append({"role": "assistant", "content": text})
            with st.chat_message("assistant"):
                st.write(text)
        except Exception as e:
            st.error(f"OpenAI API 요청 중 오류가 발생했습니다: {str(e)}")

elif selected_chatbot == "Gemini를 통한 오산시 맞춤형 교통체증 및 사고 저감 챗봇":
    colored_header(
        label='Gemini를 통한 오산시 맞춤형 교통체증 및 사고 저감 챗봇',
        description=None,
        color_name="gray-70",
    )
    # 세션 변수 체크
    check_session_vars()

    # 사이드바에서 모델의 파라미터 설정
    with st.sidebar:
        st.header("모델 설정")
        model_name = st.selectbox(
            "모델 선택",
            ["gemini-1.5-pro", 'gemini-1.5-flash']
        )
        temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.2, help="생성 결과의 다양성을 조절합니다.")
        max_output_tokens = st.number_input("Max Tokens", min_value=1, value=2048, help="생성되는 텍스트의 최대 길이를 제한합니다.")
        top_k = st.slider("Top K", min_value=1, value=40, help="다음 단어를 선택할 때 고려할 후보 단어의 최대 개수를 설정합니다.")
        top_p = st.slider("Top P", min_value=0.0, max_value=1.0, value=0.95, help="다음 단어를 선택할 때 고려할 후보 단어의 누적 확률을 설정합니다.")

    st.button("대화 초기화", on_click=lambda: st.session_state.update({
        "gemini_messages": [{"role": "model", "parts": [{"text": "Gemini가 사용자에게 맞춤형 오산시 정보를 알려드립니다."}]}]
    }))

    # 이전 메시지 표시
    for msg in st.session_state.gemini_messages:
        role = 'human' if msg['role'] == 'user' else 'ai'
        with st.chat_message(role):
            st.write(msg['parts'][0]['text'] if 'parts' in msg and 'text' in msg['parts'][0] else '')

    # 사용자 입력 처리
    if prompt := st.chat_input("챗봇과 대화하기:"):
        # 사용자 메시지 추가
        st.session_state.gemini_messages.append({"role": "user", "parts": [{"text": prompt}]})
        with st.chat_message('human'):
            st.write(prompt)

        # 프롬프트 엔지니어링 적용
        enhanced_prompt = gemini_prompt_1(prompt, st.session_state.selected_district)

        # 모델 호출 및 응답 처리
        try:
            genai.configure(api_key=st.session_state.gemini_api_key)
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
                "top_k": top_k,
                "top_p": top_p
            }
            model = genai.GenerativeModel(model_name=model_name, generation_config=generation_config)
            chat = model.start_chat(history=st.session_state.gemini_messages)
            response = chat.send_message(enhanced_prompt, stream=True)

            with st.chat_message("ai"):
                placeholder = st.empty()
                
            text = stream_display(response, placeholder)
            if not text:
                if (content := response.parts) is not None:
                    text = "Wait for function calling response..."
                    placeholder.write(text + "▌")
                    response = chat.send_message(content, stream=True)
                    text = stream_display(response, placeholder)
            placeholder.write(text)

            # 응답 메시지 표시 및 저장
            st.session_state.gemini_messages.append({"role": "model", "parts": [{"text": text}]})
        except Exception as e:
            st.error(f"Gemini API 요청 중 오류가 발생했습니다: {str(e)}")

elif selected_chatbot == "GPT를 통한 오산시 맞춤형 ITS 시설물 입지 선정 및 근거자료 챗봇":
    colored_header(
        label='GPT를 통한 오산시 맞춤형 ITS 시설물 입지 선정 및 근거자료 챗봇',
        description=None,
        color_name="gray-70",
    )

    # 세션 변수 체크
    check_session_vars()

    # 대화 초기화 버튼
    def on_clear_chat_gpt():
        st.session_state.gpt_messages = [
            {"role": "system", "content": "GPT가 사용자에게 오산시 맞춤형 ITS 시설물 입지 선정 및 근거자료 보고서를 출력해드립니다."}
        ]

    st.button("대화 초기화", on_click=on_clear_chat_gpt)

    # 이전 메시지 표시
    for msg in st.session_state.gpt_messages:
        role = 'user' if msg['role'] == 'user' else 'assistant'
        with st.chat_message(role):
            st.write(msg['content'])

    # 사용자 입력 처리
    if prompt := st.chat_input("챗봇과 대화하기:"):
        # 사용자 메시지 추가
        st.session_state.gpt_messages.append({"role": "user", "content": prompt})
        with st.chat_message('user'):
            st.write(prompt)

        # 프롬프트 엔지니어링 적용
        enhanced_prompt = gpt_prompt_2(prompt, st.session_state.selected_district)

        # 모델 호출 및 응답 처리
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": enhanced_prompt}
                ] + st.session_state.gpt_messages,
                max_tokens=1500,
                temperature=0.8,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            text = response.choices[0]['message']['content']

            # 응답 메시지 표시 및 저장
            st.session_state.gpt_messages.append({"role": "assistant", "content": text})
            with st.chat_message("assistant"):
                st.write(text)
        except Exception as e:
            st.error(f"OpenAI API 요청 중 오류가 발생했습니다: {str(e)}")

elif selected_chatbot == "Gemini를 통한 오산시 맞춤형 ITS 시설물 입지 선정 및 근거자료 챗봇":
    colored_header(
        label='Gemini를 통한 오산시 맞춤형 ITS 시설물 입지 선정 및 근거자료 챗봇',
        description=None,
        color_name="gray-70",
    )
    # 세션 변수 체크
    check_session_vars()

    # 사이드바에서 모델의 파라미터 설정
    with st.sidebar:
        st.header("모델 설정")
        model_name = st.selectbox(
            "모델 선택",
            ["gemini-1.5-pro", 'gemini-1.5-flash']
        )
        temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.2, help="생성 결과의 다양성을 조절합니다.")
        max_output_tokens = st.number_input("Max Tokens", min_value=1, value=2048, help="생성되는 텍스트의 최대 길이를 제한합니다.")
        top_k = st.slider("Top K", min_value=1, value=40, help="다음 단어를 선택할 때 고려할 후보 단어의 최대 개수를 설정합니다.")
        top_p = st.slider("Top P", min_value=0.0, max_value=1.0, value=0.95, help="다음 단어를 선택할 때 고려할 후보 단어의 누적 확률을 설정합니다.")

    st.button("대화 초기화", on_click=lambda: st.session_state.update({
        "gemini_messages": [{"role": "model", "parts": [{"text": "Gemini가 사용자에게 오산시 맞춤형 ITS 시설물 입지 선정 및 근거자료 보고서를 출력해드립니다."}]}]
    }))

    # 이전 메시지 표시
    for msg in st.session_state.gemini_messages:
        role = 'human' if msg['role'] == 'user' else 'ai'
        with st.chat_message(role):
            st.write(msg['parts'][0]['text'] if 'parts' in msg and 'text' in msg['parts'][0] else '')

    # 사용자 입력 처리
    if prompt := st.chat_input("챗봇과 대화하기:"):
        # 사용자 메시지 추가
        st.session_state.gemini_messages.append({"role": "user", "parts": [{"text": prompt}]})
        with st.chat_message('human'):
            st.write(prompt)

        # 프롬프트 엔지니어링 적용
        enhanced_prompt = gemini_prompt_2(prompt, st.session_state.selected_district)

        # 모델 호출 및 응답 처리
        try:
            genai.configure(api_key=st.session_state.gemini_api_key)
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
                "top_k": top_k,
                "top_p": top_p
            }
            model = genai.GenerativeModel(model_name=model_name, generation_config=generation_config)
            chat = model.start_chat(history=st.session_state.gemini_messages)
            response = chat.send_message(enhanced_prompt, stream=True)

            with st.chat_message("ai"):
                placeholder = st.empty()
                
            text = stream_display(response, placeholder)
            if not text:
                if (content := response.parts) is not None:
                    text = "Wait for function calling response..."
                    placeholder.write(text + "▌")
                    response = chat.send_message(content, stream=True)
                    text = stream_display(response, placeholder)
            placeholder.write(text)

            # 응답 메시지 표시 및 저장
            st.session_state.gemini_messages.append({"role": "model", "parts": [{"text": text}]})
        except Exception as e:
            st.error(f"Gemini API 요청 중 오류가 발생했습니다: {str(e)}")

elif selected_chatbot == "GPT를 활용한 오산시 스마트 교통도시계획 챗봇":
    colored_header(
        label='GPT를 활용한 오산시 스마트 교통도시계획 챗봇',
        description=None,
        color_name="gray-70",
    )

    # 세션 변수 체크
    check_session_vars()

    # 대화 초기화 버튼
    def on_clear_chat_gpt():
        st.session_state.gpt_messages = [
            {"role": "system", "content": "GPT가 사용자에게 오산시 스마트 교통도시계획 보고서를 출력해드립니다."}
        ]

    st.button("대화 초기화", on_click=on_clear_chat_gpt)

    # 이전 메시지 표시
    for msg in st.session_state.gpt_messages:
        role = 'user' if msg['role'] == 'user' else 'assistant'
        with st.chat_message(role):
            st.write(msg['content'])

    # 사용자 입력 처리
    if prompt := st.chat_input("챗봇과 대화하기:"):
        # 사용자 메시지 추가
        st.session_state.gpt_messages.append({"role": "user", "content": prompt})
        with st.chat_message('user'):
            st.write(prompt)

        # 프롬프트 엔지니어링 적용
        enhanced_prompt = gpt_prompt_3(prompt, st.session_state.selected_district)

        # 모델 호출 및 응답 처리
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": enhanced_prompt}
                ] + st.session_state.gpt_messages,
                max_tokens=1500,
                temperature=0.8,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            text = response.choices[0]['message']['content']

            # 응답 메시지 표시 및 저장
            st.session_state.gpt_messages.append({"role": "assistant", "content": text})
            with st.chat_message("assistant"):
                st.write(text)
        except Exception as e:
            st.error(f"OpenAI API 요청 중 오류가 발생했습니다: {str(e)}")

elif selected_chatbot == "Gemini를 활용한 오산시 스마트 교통도시계획 챗봇":
    colored_header(
        label='Gemini를 활용한 오산시 스마트 교통도시계획 챗봇',
        description=None,
        color_name="gray-70",
    )
    # 세션 변수 체크
    check_session_vars()

    # 사이드바에서 모델의 파라미터 설정
    with st.sidebar:
        st.header("모델 설정")
        model_name = st.selectbox(
            "모델 선택",
            ["gemini-1.5-pro", 'gemini-1.5-flash']
        )
        temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.2, help="생성 결과의 다양성을 조절합니다.")
        max_output_tokens = st.number_input("Max Tokens", min_value=1, value=2048, help="생성되는 텍스트의 최대 길이를 제한합니다.")
        top_k = st.slider("Top K", min_value=1, value=40, help="다음 단어를 선택할 때 고려할 후보 단어의 최대 개수를 설정합니다.")
        top_p = st.slider("Top P", min_value=0.0, max_value=1.0, value=0.95, help="다음 단어를 선택할 때 고려할 후보 단어의 누적 확률을 설정합니다.")

    st.button("대화 초기화", on_click=lambda: st.session_state.update({
        "gemini_messages": [{"role": "model", "parts": [{"text": "Gemini가 사용자에게 오산시 스마트 교통도시계획 보고서를 출력해드립니다."}]}]
    }))

    # 이전 메시지 표시
    for msg in st.session_state.gemini_messages:
        role = 'human' if msg['role'] == 'user' else 'ai'
        with st.chat_message(role):
            st.write(msg['parts'][0]['text'] if 'parts' in msg and 'text' in msg['parts'][0] else '')

    # 사용자 입력 처리
    if prompt := st.chat_input("챗봇과 대화하기:"):
        # 사용자 메시지 추가
        st.session_state.gemini_messages.append({"role": "user", "parts": [{"text": prompt}]})
        with st.chat_message('human'):
            st.write(prompt)

        # 프롬프트 엔지니어링 적용
        enhanced_prompt = gemini_prompt_3(prompt, st.session_state.selected_district)

        # 모델 호출 및 응답 처리
        try:
            genai.configure(api_key=st.session_state.gemini_api_key)
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
                "top_k": top_k,
                "top_p": top_p
            }
            model = genai.GenerativeModel(model_name=model_name, generation_config=generation_config)
            chat = model.start_chat(history=st.session_state.gemini_messages)
            response = chat.send_message(enhanced_prompt, stream=True)

            with st.chat_message("ai"):
                placeholder = st.empty()
                
            text = stream_display(response, placeholder)
            if not text:
                if (content := response.parts) is not None:
                    text = "Wait for function calling response..."
                    placeholder.write(text + "▌")
                    response = chat.send_message(content, stream=True)
                    text = stream_display(response, placeholder)
            placeholder.write(text)

            # 응답 메시지 표시 및 저장
            st.session_state.gemini_messages.append({"role": "model", "parts": [{"text": text}]})
        except Exception as e:
            st.error(f"Gemini API 요청 중 오류가 발생했습니다: {str(e)}")
