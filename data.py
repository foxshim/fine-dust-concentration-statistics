import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

st.set_page_config(layout="wide")  # 페이지 레이아웃을 확장형으로 설정

# 데이터 로드
for i in range(2007, 2024):
    globals()['dt_{}'.format(i)] = pd.read_csv(f'ENV_YDST_143_HR_{i}_{i}_2017.csv', encoding='cp949')

for i in range(2017, 2024):
    globals()['dt_{}'.format(i)].rename(columns={'일시': '시간'}, inplace=True)

c = []
for i in range(2007, 2024):
    c.append(globals()['dt_{}'.format(i)])
result = pd.concat(c)
result.rename(columns={'1시간평균 미세먼지농도(㎍/㎥)': 'density(㎍/㎥)'}, inplace=True)
result['시간'] = pd.to_datetime(result['시간'])
result['year'] = result['시간'].dt.year
result['month'] = result['시간'].dt.month
result['day'] = result['시간'].dt.day
result['hour'] = result['시간'].dt.hour
result = result[['year', 'month', 'day', 'hour', 'density(㎍/㎥)']]

# 사용자 데이터베이스 파일 경로
USER_DATA_FILE = os.path.abspath('user_data.txt')

def load_user_data():
    """파일에서 사용자 데이터를 로드"""
    if not os.path.exists(USER_DATA_FILE):
        return {}
    with open(USER_DATA_FILE, 'r') as file:
        lines = file.readlines()
    user_data = {}
    for line in lines:
        username, password = line.strip().split(',')
        user_data[username] = password
    return user_data

def save_user_data(user_data):
    """파일에 사용자 데이터를 저장"""
    with open(USER_DATA_FILE, 'w') as file:
        for username, password in user_data.items():
            file.write(f"{username},{password}\n")

USER_DATA = load_user_data()

def authenticate(username, password):
    """사용자 인증"""
    if username in USER_DATA and USER_DATA[username] == password:
        return True
    return False

def create_account(username, password):
    """새로운 계정 생성"""
    if username in USER_DATA:
        return False  # 이미 존재하는 사용자 이름
    USER_DATA[username] = password
    save_user_data(USER_DATA)
    return True

def load_data_for_date(year, month, day):
    """날짜에 해당하는 데이터 로드"""
    return result[(result['year'] == year) & (result['month'] == month) & (result['day'] == day)]

def validate_date(year, month, day):
    """날짜 유효성 검사"""
    if month < 1 or month > 12:
        return False
    if day < 1:
        return False
    if month in [1, 3, 5, 7, 8, 10, 12]:
        return day <= 31
    elif month in [4, 6, 9, 11]:
        return day <= 30
    elif month == 2:
        from calendar import isleap
        if isleap(year):
            return day <= 29
        else:
            return day <= 28
    return False

def main():
    if 'page' not in st.session_state:
        st.session_state.page = 'login'

    if st.session_state.page == 'login':
        login_page()
    elif st.session_state.page == 'signup':
        signup_page()
    elif st.session_state.page == 'main':
        main_page()

def login_page():
    st.title("로그인")
    username = st.text_input("사용자 이름")
    password = st.text_input("비밀번호", type="password")

    if st.button("로그인"):
        if authenticate(username, password):
            st.session_state.page = 'main'
            st.session_state.username = username
            st.rerun()
        else:
            st.error("잘못된 사용자 이름 또는 비밀번호입니다.")
    
    if st.button("회원가입"):
        st.session_state.page = 'signup'
        st.rerun()

def signup_page():
    st.title("회원가입")
    new_username = st.text_input("새로운 사용자 이름")
    new_password = st.text_input("새로운 비밀번호", type="password")

    if st.button("회원가입"):
        if create_account(new_username, new_password):
            st.success("계정이 성공적으로 생성되었습니다. 이제 로그인하세요.")
            st.session_state.page = 'login'
            st.rerun()
        else:
            st.error("이미 사용 중인 사용자 이름입니다. 다른 이름을 선택하세요.")
    
    if st.button("로그인으로 돌아가기"):
        st.session_state.page = 'login'
        st.rerun()

def main_page():
    st.title(f"미세먼지 농도 예측 - {st.session_state.username}님 환영합니다!")

    st.write("**년, 월, 일 입력 범위를 참고하세요:**")
    st.write("- **Year:** 2007 - 2023까지만 데이터가 있습니다. 만약 그 뒤의 데이터는 추가하셔야합니다.")
    st.write("- **Month:** 1 - 12")
    st.write("- **Day:** 1 - 31 월에 따라 다를 수 있습니다.")

    year = st.number_input('Year', min_value=2007, value=2023)
    month = st.number_input('Month', min_value=1, max_value=12, value=6)
    day = st.number_input('Day', min_value=1, max_value=31, value=15)
    
    if not validate_date(year, month, day):
        st.error("유효하지 않은 날짜입니다. 다시 입력하세요.")
        return

    data_for_date = load_data_for_date(year, month, day)

    if not data_for_date.empty:
        col1, col2 = st.columns([2, 2])
        
        with col1:
            st.write("해당 날짜의 실제 미세먼지 농도 데이터:")
            st.write(data_for_date)

            # 최대, 최소, 평균값 계산 및 시간 확인
            max_density = data_for_date['density(㎍/㎥)'].max()
            max_density_time = data_for_date.loc[data_for_date['density(㎍/㎥)'].idxmax()]['hour']
            min_density = data_for_date['density(㎍/㎥)'].min()
            min_density_time = data_for_date.loc[data_for_date['density(㎍/㎥)'].idxmin()]['hour']
            mean_density = data_for_date['density(㎍/㎥)'].mean()

            st.write(f"**최대 농도:** {max_density:.2f} ㎍/㎥ (시간: {max_density_time}시)")
            st.write(f"**최소 농도:** {min_density:.2f} ㎍/㎥ (시간: {min_density_time}시)")
            st.write(f"**평균 농도:** {mean_density:.2f} ㎍/㎥")

        with col2:
            st.write("시간대별 미세먼지 농도 그래프:")
            fig, ax = plt.subplots(figsize=(14, 8))
            ax.plot(data_for_date['hour'], data_for_date['density(㎍/㎥)'], marker='o', linestyle='-')
            ax.set_xlabel('Hour')
            ax.set_ylabel('PM2.5 Density (㎍/㎥)')
            ax.set_title(f'PM2.5 Density on {year}-{month:02d}-{day:02d}')
            st.pyplot(fig)
    else:
        st.write("해당 날짜의 데이터가 없습니다.")
        st.write("데이터를 업로드하여 추가해주세요.")
        
        uploaded_file = st.file_uploader("CSV 파일 업로드", type="csv")
        if uploaded_file is not None:
            new_data = pd.read_csv(uploaded_file, encoding='cp949')
            new_data.rename(columns={'일시': '시간', '1시간평균 미세먼지농도(㎍/㎥)': 'density(㎍/㎥)'}, inplace=True)
            new_data['시간'] = pd.to_datetime(new_data['시간'])
            new_data['year'] = new_data['시간'].dt.year
            new_data['month'] = new_data['시간'].dt.month
            new_data['day'] = new_data['시간'].dt.day
            new_data['hour'] = new_data['시간'].dt.hour
            new_data = new_data[['year', 'month', 'day', 'hour', 'density(㎍/㎥)']]

            # 새 데이터를 기존 데이터프레임에 추가
            global result
            result = pd.concat([result, new_data])

            st.success("데이터가 성공적으로 추가되었습니다.")
            st.write(new_data)

            # 추가된 데이터 중 입력한 날짜의 데이터 출력
            updated_data_for_date = load_data_for_date(year, month, day)
            if not updated_data_for_date.empty:
                col1, col2 = st.columns([2, 2])
                
                with col1:
                    st.write("업로드된 데이터로 갱신된 해당 날짜의 미세먼지 농도 데이터:")
                    st.write(updated_data_for_date)

                    # 최대, 최소, 평균값 계산 및 시간 확인
                    max_density = updated_data_for_date['density(㎍/㎥)'].max()
                    max_density_time = updated_data_for_date.loc[updated_data_for_date['density(㎍/㎥)'].idxmax()]['hour']
                    min_density = updated_data_for_date['density(㎍/㎥)'].min()
                    min_density_time = updated_data_for_date.loc[updated_data_for_date['density(㎍/㎥)'].idxmin()]['hour']
                    mean_density = updated_data_for_date['density(㎍/㎥)'].mean()

                    st.write(f"**최대 농도:** {max_density:.2f} ㎍/㎥ (시간: {max_density_time}시)")
                    st.write(f"**최소 농도:** {min_density:.2f} ㎍/㎥ (시간: {min_density_time}시)")
                    st.write(f"**평균 농도:** {mean_density:.2f} ㎍/㎥")

                with col2:
                    st.write("시간대별 미세먼지 농도 그래프:")
                    fig, ax = plt.subplots(figsize=(14, 8))
                    ax.plot(updated_data_for_date['hour'], updated_data_for_date['density(㎍/㎥)'], marker='o', linestyle='-')
                    ax.set_xlabel('Hour')
                    ax.set_ylabel('PM2.5 Density (㎍/㎥)')
                    ax.set_title(f'PM2.5 Density on {year}-{month:02d}-{day:02d}')
                    st.pyplot(fig)

    if st.button("로그아웃"):
        st.session_state.page = 'login'
        st.rerun()

if __name__ == "__main__":
    main()
