import streamlit as st
from streamlit_folium import st_folium
from streamlit_folium import folium_static
import streamlit.components.v1 as components
import folium
import geopandas as gpd
import pandas as pd
import numpy as np
import seaborn as sns
from datetime import date
from datetime import datetime
import holidays
from statsmodels.tsa.seasonal import seasonal_decompose
import scipy.stats as stats
from statsmodels.tsa.stattools import adfuller
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import MinMaxScaler
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter, YearLocator, MonthLocator
from matplotlib import container
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt 
from matplotlib import rc
from PIL import Image

rc('font', family='AppleGothic')
plt.rcParams['axes.unicode_minus'] = False

# 데이터 
# df_trade = pd.read_csv("/content/drive/MyDrive/공모전(Dacon)/international_trade.csv")
df_train = pd.read_csv("/Users/seungho/Desktop/승호/공모전 및 프로젝트/데이콘/데이콘 제주특산물가격예측 /dataset/temp_train(11.16) (1).csv")
df_test = pd.read_csv("/Users/seungho/Desktop/승호/공모전 및 프로젝트/데이콘/데이콘 제주특산물가격예측 /dataset/df_test.csv")
df_train['timestamp'] = pd.to_datetime(df_train['timestamp'])
df_train['timestamp'] = df_train['timestamp'].dt.date


# Minmax_scaling 
from sklearn.preprocessing import MinMaxScaler

def scale_columns(df, columns):
    scaler = MinMaxScaler()
    df[columns] = scaler.fit_transform(df[columns])
    return df

scaled_df = scale_columns(df_train, ['price(원/kg)','수입 금액'])
scaled_df1 = scale_columns(df_train, ['price(원/kg)','supply(kg)'])
 

# 제목 
st.title("제주도 :green[주요 농산물] 데이터 분석 🏝️")


# 사이드바 
page = st.sidebar.selectbox(" 🍊 주요 농산물 데이터 분석 ", ["1) 농산물 데이터", "2) 제주도 지도", "3) 탐색적 데이터분석(EDA)","4) 데이터 전처리", "5) 모델링"])

if page == "1) 농산물 데이터": 
    st.header("농산물 데이터", help = "TG : 감귤, BC : 브로콜리, RD : 무, CR : 당근, CB : 양배추 ")
    item = st.selectbox('item(품목)', options = df_train['item'].unique(), key='item_selectbox_1')
    corp = st.selectbox('corporation(법인)',options = df_train['corporation'].unique())
    location = st.selectbox('location(지역)',options = df_train['location'].unique())
    start_date = st.date_input("시작 날짜", df_train['timestamp'].min())
    end_date = st.date_input("종료 날짜", df_train['timestamp'].max())
    filtered_df = df_train[
    (df_train['item'] == item) &
    (df_train['timestamp'] >= start_date) &
    (df_train['timestamp'] <= end_date) &
    (df_train['corporation'] == corp) &
    (df_train['location'] == location)
]
    st.write(filtered_df)

    csv = filtered_df.to_csv(index=False)
 
    st.download_button(
        label = "file Download",
        data = csv,
        file_name="file.csv", 
        mime="text/csv"
    )
elif page == "2) 제주도 지도":
    
    def load_data():
    # Shapefile 읽기
        gdf = gpd.read_file('/Users/seungho/Desktop/승호/공모전 및 프로젝트/데이콘/데이콘 제주특산물가격예측 /dataset/LARD_ADM_SECT_SGG_50.dbf', encoding='euc-kr')
        gdf.set_crs(epsg=4326, inplace=True, allow_override=True)
        return gdf

    def create_map(gdf):
    # 제주도의 중심 좌표
        jeju_coordinates = [33.361666, 126.529166]

        corporations = {
            "A": [33.315, 126.199],  
            "B": [33.422, 126.308],  
            "C": [33.500, 126.782],  
            "D": [33.500, 126.638],  
            "E": [33.321, 126.688],  
            "F": [33.273, 126.560]   
    }

        colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred']

        # 기본 지도 생성
        map_jeju = folium.Map(location=jeju_coordinates, zoom_start=10)

        def style_function(feature):
            if feature['properties']['SGG_NM'] == '제주시':
                return {'fillColor':'green', 'color':'green', 'weight': 1.5, 'fillOpacity': 0.5}
            else:
                return {'fillColor': 'blue', 'color': 'blue', 'weight': 1.5, 'fillOpacity': 0.5}

        def highlight_function(feature):
            return {'fillColor': '#ffaf00', 'color': '#ffaf00', 'fillOpacity': 0.5, 'weight': 3}

        folium.GeoJson(
            gdf,
            name='jeju',
            style_function = style_function,
            highlight_function = highlight_function,
            tooltip=folium.GeoJsonTooltip(fields=['SGG_NM'], aliases=['지역:'])
        ).add_to(map_jeju)
        

        for (corporation, coords), color in zip(corporations.items(), colors):
            folium.CircleMarker(
                location=coords,
                radius=df_train[df_train['corporation'] == corporation]['price(원/kg)'].mean() * 1000,
                color=color,
                fill=True,
                fill_color=color,
                tooltip=f"{corporation}"
            ).add_to(map_jeju)



        for (corporation, coords), color in zip(corporations.items(), colors):
            folium.Marker(
                location=coords,
                icon=folium.Icon(color=color, icon='info-sign'),
                tooltip=f"{corporation}유통법인 판매량"
                        ).add_to(map_jeju) 
        
        return map_jeju

    def main():
        st.subheader("제주도 유통법인 별 평균 판매량")

        # 데이터 로드
        gdf = load_data()

        # 지도 생성
        map_jeju = create_map(gdf)

        # 지도를 HTML로 변환하여 Streamlit 앱에 표시
        map_html = map_jeju._repr_html_()
        components.html(map_html, height=600)

    if __name__ == "__main__":
        main()

elif page == "3) 탐색적 데이터분석(EDA)":
    st.header("탐색적 데이터분석(EDA)")

    st.subheader("1.기술통계")
    if st.checkbox("기술통계",help = "TG : 감귤, BC : 브로콜리, RD : 무, CR : 당근, CB : 양배추 ") : 
        item = st.selectbox('item(품목)', options = df_train['item'].unique(), key='item_selectbox_2')
        st.dataframe(df_train[df_train['item'] == item].describe())
    
    st.subheader("2.상관관계 분석")
    if st.checkbox("상관관계"):
        fig, ax = plt.subplots() 
        corr_matrix = df_train.corr()
        sns.heatmap(corr_matrix, annot = True , cmap = 'coolwarm', linewidths=.4, fmt=".2f")
        st.pyplot(fig)  


    st.subheader("3.Box-plot")
    if st.checkbox("1)품목에 따른 가격과 공급량 비교"):
        fig, ax =  plt.subplots(1,2, figsize =(10, 8))
        sns.boxplot(data = df_train, x='item', y='price(원/kg)', ax = ax[0])
        ax[0].set_title('품목에 따른 가격 box-plot')
       
        sns.boxplot(data = df_train, x='item', y='supply(kg)', ax = ax[1])
        ax[1].set_title('품목에 따른 공급량 box-plot')
        st.pyplot(fig)        
    
    if st.checkbox("2)품목에 따른 가격과 공급량"):
        item = st.selectbox('item(품목)', options = df_train['item'].unique(), key='item_selectbox_3')

        fig, ax =  plt.subplots(1,2, figsize =(10, 8))
        sns.boxplot(data = df_train[df_train['item'] == item], x='item', y='price(원/kg)', ax = ax[0])
        ax[0].set_title(f'{item}에 따른 가격 box-plot')
       
        sns.boxplot(data = df_train[df_train['item'] == item], x='item', y='supply(kg)', ax = ax[1])
        ax[1].set_title(f'{item}에 따른 공급량 box-plot')
        st.pyplot(fig)

    if st.checkbox("3)법인에 따른 가격과 공급량 비교"):    
        fig, ax =  plt.subplots(1,2, figsize =(10, 8))
        sns.boxplot(data = df_train, x='corporation', y='price(원/kg)', ax = ax[0])
        ax[0].set_title('법인에 따른 가격 box-plot')
       
        sns.boxplot(data = df_train, x='corporation', y='supply(kg)', ax = ax[1])
        ax[1].set_title('법인에 따른 공급량 box-plot')
        st.pyplot(fig)   

    if st.checkbox("4)법인에 따른 가격과 공급량"):    
        corp = st.selectbox('corporation(법인)',options = df_train['corporation'].unique())
        fig, ax =  plt.subplots(1,2, figsize =(10, 8))
        sns.boxplot(data = df_train[df_train['corporation']== corp], x='corporation', y='price(원/kg)', ax = ax[0])
        ax[0].set_title(f'{corp}법인 가격 box-plot')
       
        sns.boxplot(data = df_train[df_train['corporation']== corp], x='corporation', y='supply(kg)', ax = ax[1])
        ax[1].set_title(f'{corp}법인 공급량 box-plot')
        st.pyplot(fig)  

    if st.checkbox("5)지역에 따른 가격과 공급량 비교", help= 'J: 제주시, S:서귀포시'):    
        fig, ax =  plt.subplots(1,2, figsize =(10, 8))
        sns.boxplot(data = df_train, x='location', y='price(원/kg)', ax = ax[0])
        ax[0].set_title('지역에 따른 가격 box-plot')
       
        sns.boxplot(data = df_train, x='location', y='supply(kg)', ax = ax[1])
        ax[1].set_title('지역에 따른 공급량 box-plot')
        st.pyplot(fig) 

    if st.checkbox("6)지역에 따른 가격과 공급량", help= 'J: 제주시, S:서귀포시'):
        location = st.selectbox('location(지역)',options = df_train['location'].unique())    
        fig, ax =  plt.subplots(1,2, figsize =(10, 8))
        sns.boxplot(data = df_train[df_train['location']== location], x='corporation', y='price(원/kg)', ax = ax[0])
        ax[0].set_title(f'{location}지역 가격 box-plot')
       
        sns.boxplot(data = df_train[df_train['location']== location], x='corporation', y='supply(kg)', ax = ax[1])
        ax[1].set_title(f'{location}지역 공급량 box-plot')
        st.pyplot(fig)

    if st.checkbox("7)휴일여부에 따른 가격 비교"):
        fig, ax = plt.subplots(3, 1, figsize=(10, 12))
        sns.barplot(data= df_train,x='item',y='price(원/kg)',hue='holiday',ax=ax[0])
        sns.barplot(data=df_train,x='corporation',y='price(원/kg)',hue='holiday',ax=ax[1])
        sns.barplot(data=df_train,x='location',y='price(원/kg)',hue='holiday',ax=ax[2])
        st.pyplot(fig) 

    if st.checkbox("8)휴일여부에 따른 가격 공급량 비교"):
        fig, ax = plt.subplots(3, 1, figsize=(10, 14))
        sns.barplot(data= df_train,x='item',y='supply(kg)',hue='holiday',ax=ax[0])
        sns.barplot(data=df_train,x='corporation',y='supply(kg)',hue='holiday',ax=ax[1])
        sns.barplot(data=df_train,x='location',y='supply(kg)',hue='holiday',ax=ax[2])
        st.pyplot(fig)         

    st.subheader("4.Scatter-plot")
    if st.checkbox("1)품목에 따른 가격과 공급량 Scatter-plot",help = "TG : 감귤, BC : 브로콜리, RD : 무, CR : 당근, CB : 양배추 "):
        item = st.selectbox('item(품목)', options = df_train['item'].unique(), key='item_selectbox_4') 
        fig, ax =  plt.subplots(1,1, figsize =(10, 10))
        sns.scatterplot(data = df_train[df_train['item']== item], x='supply(kg)', y='price(원/kg)', ax = ax)
        ax.set_title(f'{item}에 따른 가격과 공급량 Scatter-plot')
        st.pyplot(fig)        

    if st.checkbox("2)시간에 따른 공급량 Scatter-plot",help = "TG : 감귤, BC : 브로콜리, RD : 무, CR : 당근, CB : 양배추 "):
        item = st.selectbox('item(품목)', options = df_train['item'].unique(), key='item_selectbox_5')
        fig, ax = plt.subplots(1, 1, figsize=(10, 10))
        min_date, max_date = st.slider("날짜 범위 선택:", 
                                   min_value=df_train['timestamp'].min(),
                                   max_value=df_train['timestamp'].max(),
                                   value=(df_train['timestamp'].min(), df_train['timestamp'].max()))
        min_date, max_date = pd.to_datetime(min_date), pd.to_datetime(max_date)
        ax.scatter(data = df_train[(df_train['item']== item) & (df_train['timestamp'] >= min_date) & (df_train['timestamp'] <= max_date)],x = 'timestamp', y ='supply(kg)' ,marker='o', color='b')
        ax.set_title(f'{item} 공급량')
        ax.set_xlabel('날짜')
        ax.set_ylabel('공급량') 
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=(12)))
        ax.tick_params(axis='x', rotation=45)
        st.pyplot(fig) 

    if st.checkbox("3)시간에 따른 가격 Scatter-plot",help = "TG : 감귤, BC : 브로콜리, RD : 무, CR : 당근, CB : 양배추 "):
        item = st.selectbox('item(품목)', options = df_train['item'].unique(), key='item_selectbox_6')
        fig, ax = plt.subplots(1, 1, figsize=(10, 10))
        min_date, max_date = st.slider("날짜 범위 선택:", 
                                   min_value=df_train['timestamp'].min(),
                                   max_value=df_train['timestamp'].max(),
                                   value=(df_train['timestamp'].min(), df_train['timestamp'].max()))
        min_date, max_date = pd.to_datetime(min_date), pd.to_datetime(max_date)
        ax.scatter(data = df_train[(df_train['item']== item) & (df_train['timestamp'] >= min_date) & (df_train['timestamp'] <= max_date)],x = 'timestamp', y = 'price(원/kg)' ,marker='o', color='g')
        ax.set_title(f'{item} 가격')
        ax.set_xlabel('날짜')
        ax.set_ylabel('가격')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=(12)))
        ax.tick_params(axis='x', rotation=45)
        st.pyplot(fig)  

    st.subheader("5.line-plot",help = "비교를 위해 스케일링 진행")
    if st.checkbox("1)수입금액 - 가격 line-plot",help = "TG : 감귤, BC : 브로콜리, RD : 무, CR : 당근, CB : 양배추 "):
        item = st.selectbox('item(품목)', options = df_train['item'].unique(), key='item_selectbox_7')
        fig = plt.figure(figsize=(10,10))
        filter_df = df_train[df_train['item']== item].groupby(['timestamp(M)'])[['수입 중량','수입 금액']].sum()
        filter_df = scale_columns(filter_df, ['수입 중량','수입 금액'])
        filter_df1 = df_train[df_train['item']== item].groupby(['timestamp(M)'])[['supply(kg)','price(원/kg)']].mean()
        filter_df1 = scale_columns(filter_df1, ['supply(kg)','price(원/kg)'])
        plt.plot(np.arange(len(filter_df.index)), filter_df['수입 금액'].to_numpy(), label = "수입 금액" )
        plt.plot(np.arange(len(filter_df1.index)), filter_df1['price(원/kg)'].to_numpy(), label = "price(원/kg)" )
        plt.title("수입금액 & 가격 비교 ")
        plt.legend()
        st.pyplot(fig)

    if st.checkbox("2)수입중량 - 공급량 line-plot",help = "TG : 감귤, BC : 브로콜리, RD : 무, CR : 당근, CB : 양배추 "):
        item = st.selectbox('item(품목)', options = df_train['item'].unique(), key='item_selectbox_8')
        fig = plt.figure(figsize=(10,10))
        filter_df = df_train[df_train['item']== item].groupby(['timestamp(M)'])[['수입 중량','수입 금액']].sum()
        filter_df = scale_columns(filter_df, ['수입 중량','수입 금액'])
        filter_df1 = df_train[df_train['item']== item].groupby(['timestamp(M)'])[['supply(kg)','price(원/kg)']].mean()
        filter_df1 = scale_columns(filter_df1, ['supply(kg)','price(원/kg)'])
        plt.plot(np.arange(len(filter_df.index)), filter_df['수입 중량'].to_numpy(), label = "수입 중량" )
        plt.plot(np.arange(len(filter_df1.index)), filter_df1['supply(kg)'].to_numpy(), label = "supply(kg)" )
        plt.title("수입 중량 & 공급량 비교 ")
        plt.legend()
        st.pyplot(fig)

    if st.checkbox("3)가격 - 공급량 line-plot",help = "TG : 감귤, BC : 브로콜리, RD : 무, CR : 당근, CB : 양배추 "):
        item = st.selectbox('item(품목)', options = df_train['item'].unique(), key='item_selectbox_9')
        fig = plt.figure(figsize=(10,10))
        filter_df = df_train[df_train['item']== item].groupby(['timestamp(M)'])[['수입 중량','수입 금액']].sum()
        filter_df = scale_columns(filter_df, ['수입 중량','수입 금액'])
        filter_df1 = df_train[df_train['item']== item].groupby(['timestamp(M)'])[['supply(kg)','price(원/kg)']].mean()
        filter_df1 = scale_columns(filter_df1, ['supply(kg)','price(원/kg)'])
        plt.plot(np.arange(len(filter_df1.index)), filter_df1['price(원/kg)'].to_numpy(), label = "price(원/kg)" )
        plt.plot(np.arange(len(filter_df1.index)), filter_df1['supply(kg)'].to_numpy(), label = "supply(kg)" )
        plt.title("가격 & 공급량 비교 ")
        plt.legend()
        st.pyplot(fig)

    st.subheader("6.kde-plot")
    if st.checkbox("1) price Kde-plot"):
        item = st.selectbox('item(품목)', options = df_train['item'].unique(), key='item_selectbox_10')
        fig , ax = plt.subplots() 
        sns.kdeplot(data = df_train[df_train['item']== item]['price(원/kg)'], shade = True)
        ax.set_title("KDE plot of price(원/kg)")
        ax.set_xlabel('price(원/kg)')
        st.pyplot(fig)

    if st.checkbox("2) supply Kde-plot"):
        item = st.selectbox('item(품목)', options = df_train['item'].unique(), key='item_selectbox_11')
        fig , ax = plt.subplots() 
        sns.kdeplot(data = df_train[df_train['item']== item]['supply(kg)'], shade = True)
        ax.set_title("KDE plot of price(원/kg)")
        ax.set_xlabel('supply(kg)')
        st.pyplot(fig)



elif page == "4) 데이터 전처리":
    st.header("데이터 전처리")
    if st.checkbox("⌨️ 이상치처리"):
        st.subheader("1. 이상치 처리 ")
        st.markdown("### - Supply(kg) 이상치 확인")
        code = '''
        list = [(tg_df, '감귤'), (bc_df, '브로콜리'), (rd_df, '무'), (cr_df, '당근'), (cb_df, '양배추')]

        for df, _ in list:
        if df is rd_df:
            contamination=0.009
        elif df is cr_df:
            contamination=0.01
        else:
            contamination=0.005

        model = IsolationForest(contamination = contamination)
        model.fit(df[['supply(kg)']])
        supply_outliers = model.predict(df[['supply(kg)']])
        df['supply_outlier'] = supply_outliers

        fig, ax = plt.subplots(figsize=(5,5))
        anomaly = df.loc[df['supply_outlier'] == -1, ['supply(kg)']]
        ax.scatter(df.index, df['supply(kg)'], color = 'black', label = 'supply(kg)')
        ax.scatter(anomaly.index, anomaly['supply(kg)'], color = 'red', label = 'Anomaly')
        plt.title(f'{_} supply(kg) 이상치' )

        plt.legend()
        plt.show()  '''
        st.code(code, language='python') 
        image1 = Image.open( "/Users/seungho/Desktop/승호/공모전 및 프로젝트/데이콘/데이콘 제주특산물가격예측 /사진/1.png")
        image2 = Image.open( "/Users/seungho/Desktop/승호/공모전 및 프로젝트/데이콘/데이콘 제주특산물가격예측 /사진/2.png")
        image3 = Image.open( "/Users/seungho/Desktop/승호/공모전 및 프로젝트/데이콘/데이콘 제주특산물가격예측 /사진/3.png")
        image4 = Image.open( "/Users/seungho/Desktop/승호/공모전 및 프로젝트/데이콘/데이콘 제주특산물가격예측 /사진/4.png")
        image5 = Image.open( "/Users/seungho/Desktop/승호/공모전 및 프로젝트/데이콘/데이콘 제주특산물가격예측 /사진/5.png")
        image6 = Image.open( "/Users/seungho/Desktop/승호/공모전 및 프로젝트/데이콘/데이콘 제주특산물가격예측 /사진/5.png")
        image7 = Image.open( "/Users/seungho/Desktop/승호/공모전 및 프로젝트/데이콘/데이콘 제주특산물가격예측 /사진/5.png")
        image8 = Image.open( "/Users/seungho/Desktop/승호/공모전 및 프로젝트/데이콘/데이콘 제주특산물가격예측 /사진/5.png")
        image9 = Image.open( "/Users/seungho/Desktop/승호/공모전 및 프로젝트/데이콘/데이콘 제주특산물가격예측 /사진/5.png")
        image10 = Image.open( "/Users/seungho/Desktop/승호/공모전 및 프로젝트/데이콘/데이콘 제주특산물가격예측 /사진/5.png")
        images = [image1,image2,image3,image4,image5]

        st.image(images, width =350 ,caption=['감귤','브로콜리','무','당근','양배추'])


        st.markdown("### - Price(원/Kg) 이상치 확인")
        code = '''
        list = [(tg_df, '감귤'), (bc_df, '브로콜리'), (rd_df, '무'), (cr_df, '당근'), (cb_df, '양배추')]

        for df, _ in list:
        if df is rd_df:
            contamination=0.009
        elif df is cr_df:
            contamination=0.01
        else:
            contamination=0.005
        
        model = IsolationForest(contamination = contamination)
        model.fit(df[['price(원/kg)']])
        price_outliers = model.predict(df[['price(원/kg)']])
        df['price_outlier'] = price_outliers

        fig, ax = plt.subplots(figsize=(5,5))
        anomaly = df.loc[df['price_outlier'] == -1, ['price(원/kg)']]
        ax.scatter(df.index, df['price(원/kg)'], color = 'black', label = 'price(원/kg)')
        ax.scatter(anomaly.index, anomaly['price(원/kg)'], color = 'red', label = 'Anomaly')
        plt.title(f'{_} price(원/kg) 이상치' )

        plt.legend()
        plt.show()

                '''
        st.code(code, language='python')
        images2 = [image6,image7,image8,image9,image10]
        st.image(images2, width =350 ,caption=['감귤','브로콜리','무','당근','양배추'])
        


        st.markdown("### - 이상치 Q3 + 1.5 * IQR 로 대체")
        code = '''
        list = [(tg_df, '감귤'), (bc_df, '브로콜리'), (rd_df, '무'), (cr_df, '당근'), (cb_df, '양배추')]
        for df, _ in list:   
        Q1 = df['supply(kg)'].quantile(0.25)
        Q3 = df['supply(kg)'].quantile(0.75)
        IQR = Q3 - Q1
        upper_bound = Q3 + 1.5 * IQR
        df.loc[df['supply_outlier'] == -1, 'supply(kg)'] = upper_bound

                '''
        st.code(code, language='python')
        

    if st.checkbox("⌨️ Min-max-scaling"):
        st.subheader("2. Min-max-scaling ")
        code = '''
        # Minmax_scaling 
        from sklearn.preprocessing import MinMaxScaler

        def scale_columns(df, columns):
        scaler = MinMaxScaler()
        df[columns] = scaler.fit_transform(df[columns])
        return df

        scaled_df = scale_columns(df_train, ['price(원/kg)','수입 금액'])
        scaled_df1 = scale_columns(df_train, ['price(원/kg)','supply(kg)'])

                '''
        st.code(code, language='python')


    if st.checkbox("⌨️ label encoding"):
        st.subheader("3. label encoding ")
        code = '''
        from sklearn.preprocessing import  LabelEncoder
        col = ['item','corporation', 'location','holiday']

        for i in col:
        encoder = LabelEncoder()
        df_train[i] = encoder.fit_transform(df_train[i])
        df_test[i] = encoder.transform(df_test[i])        

                '''
        st.code(code, language='python')

elif page == "5) 모델링":
    st.title("모델링(Modeling)")
    if st.checkbox("⌨️ Autogluon"):
        st.subheader("1.Autogluon ")
        st.markdown('''**__:blue[AutoGluon]__**은 Amazon이 개발한 오픈 소스 머신 러닝 라이브러리로, 특히 자동화된 머신 러닝(AutoML)에 초점을 
맞추고 있다. 이 도구는 데이터 과학자들이 최소한의 도메인 지식으로도 복잡한 머신 러닝 모델을 빠르고 쉽게 훈련시킬 수 있도록 설계되었음. 
AutoGluon의 주요 특징과 장점은 다음과 같다''') 
        st.markdown("1) **__:blue[사용의 용이성]__** : 몇줄의 코드만으로 데이터를 로드하고 모델을 훈련시킴")
        st.markdown('''2) **__:blue[자동화된 모델 선택과 하이퍼파라미터 튜닝]__** : 이 과정은 통상적으로 많은 시간과 전문 지식을 요구하지만, 
                    AutoGluon은 이를 자동화함으로써 과정을 단순화 시켜줌''')
        st.markdown("3) **__:blue[앙상블 학습과 스택킹]__** : 여러 모델의 예측을 결합하여 성능을 향상 시키는 앙상블 학습과 스택킹 기법을 자동으로 적용")

    

        st.subheader("2.Hyper parameter ")
        st.markdown("1) **__:red[train_data = df_train]__**  : 훈련 데이터셋")    
        st.markdown("2) **__:red[presets='best_quality']__**  : 예측 정확도를 우선시하는 최상의 품질 설정을 사용")    
        st.markdown("3) **__:red[auto_stack = True:]__** 성능을 향상시키기 위해 자동으로 모델 스태킹을 수행")    
        st.markdown("4) **__:red[fit_weighted_ensemble = True]__**  : 모든 모델의 가중 앙상블을 학습하여 예측 성능을 향상")    
        st.markdown("5) **__:red[num_bag_folds = n]__**  : 과적합을 줄이는 데 도움이 되는 n겹의 배깅을 사용")    
        st.markdown("6) **__:red[num_bag_sets = n]__**  : 성능을 안정화하기 위해 배깅을 n회 반복")    
        st.markdown("7) **__:red[num_stack_levels = n]__**  : 이전 레벨의 모델을 기반으로 새로운 모델을 구축하는 n개의 스태킹 레벨을 만듬")    
        st.markdown("8) **__:red[num_gpus = 1]__**  : GPU 사용개수")    
        st.markdown("9) **__:red[num_cpus = cpu]__** :  사용개수")    
        st.markdown("10) **__:red[verbosity = 2]__**:  훈련 과정 중 상세한 로그를 출력")    
        


        st.subheader("3.Code ")
        code = '''
        # 불필요 컬럼 삭제 
        df_train = TabularDataset(df_train)
        df_test = TabularDataset(df_test)

        predictor = TabularPredictor(label='price(원/kg)',
                             eval_metric='rmse',
                             problem_type= 'regression')

        predictor.fit(train_data = df_train,
              presets='best_quality',
              auto_stack = True, fit_weighted_ensemble = True,
              num_bag_folds = 10, num_bag_sets = 2, num_stack_levels = 2,
              verbosity = 2
              )
        ld_board = predictor.leaderboard(df_train, silent=True)

        pred_y = predictor.predict(df_test)
        pred_y


                '''
        st.code(code, language='python')
        code = "ld_board = predictor.leaderboard(df_train, silent=True)"
        st.markdown("학습과정") 
        url ="/Users/seungho/Desktop/승호/공모전 및 프로젝트/데이콘/데이콘 제주특산물가격예측 /사진/15.png"
        st.image(url, caption = ' ') 
        st.markdown("학습결과") 
        st.code(code, language='python')
        url1 = "/Users/seungho/Desktop/승호/공모전 및 프로젝트/데이콘/데이콘 제주특산물가격예측 /사진/14.png"
        st.image(url1, caption = ' ')


# page1 = st.sidebar.selectbox("🖥️ 제주도 농산물 가격예측 시스템 ", ["Model-1", "Model-2"])
# if page1 == "Model-1": 
#     st.header("가격예측 시스템")
#     url ="/Users/seungho/Desktop/승호/공모전 및 프로젝트/데이콘/데이콘 제주특산물가격예측 /사진/13.png"
#     st.image(url, caption = ' ') 




