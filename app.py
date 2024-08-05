import streamlit as st
import os
import requests
from PIL import Image, ImageOps
from io import BytesIO
import time
import random
from googletrans import Translator
from urllib.parse import quote
import zipfile

# Pexels API 키
API_KEY = st.secrets["PEXELS_API_KEY"]

# 번역기 초기화
translator = Translator()

# 무지개 색상 리스트
rainbow_colors = [
    (255, 0, 0), (255, 127, 0), (255, 255, 0), (0, 255, 0),
    (0, 0, 255), (75, 0, 130), (143, 0, 255)
]

def compress_image(img, max_size_kb=200):
    quality = 85
    while True:
        temp_buffer = BytesIO()
        img.save(temp_buffer, format='JPEG', quality=quality, optimize=True)
        size_kb = temp_buffer.tell() / 1024
        
        if size_kb <= max_size_kb:
            break
        if quality <= 20:  # 최소 품질 제한
            break
        quality -= 5
    
    return Image.open(temp_buffer)

def download_and_process_image(url):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    
    # 이미지 크기 조정 (필요한 경우)
    max_dimension = 1500
    if max(img.size) > max_dimension:
        img.thumbnail((max_dimension, max_dimension))
    
    # 랜덤 자르기 (왼쪽 또는 오른쪽에서 100픽셀)
    width, height = img.size
    if random.choice([True, False]):  # 왼쪽 자르기
        img = img.crop((100, 0, width, height))
    else:  # 오른쪽 자르기
        img = img.crop((0, 0, width - 100, height))
    
    # 랜덤 테두리 색상 선택
    border_color = random.choice(rainbow_colors)
    border_size = 20
    
    # 테두리 추가
    img_with_border = ImageOps.expand(img, border=border_size, fill=border_color)
    
    # 랜덤 각도로 회전 (-10도 ~ -4도 또는 4도 ~ 10도)
    rotate_angle = random.choice([-1, 1]) * random.randint(4, 10)
    img_rotated = img_with_border.rotate(rotate_angle, expand=True, fillcolor=border_color)
    
    # 이미지 압축
    img_compressed = compress_image(img_rotated)
    
    return img_compressed

def fetch_images(keyword, page=1, per_page=15):
    encoded_keyword = quote(keyword)
    url = f"https://api.pexels.com/v1/search?query={encoded_keyword}&page={page}&per_page={per_page}"
    headers = {"Authorization": API_KEY}
    response = requests.get(url, headers=headers)
    return response.json()

def main():
    st.title("Pexels 이미지 크롤러")
    
    keyword_kr = st.text_input("검색할 키워드를 한글로 입력하세요:")
    
    if st.button("이미지 검색 및 처리"):
        if keyword_kr:
            keyword = translator.translate(keyword_kr, src='ko', dest='en').text
            st.write(f"번역된 키워드: {keyword}")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            images = []
            total_images = 0
            page = 1
            
            while total_images < 35:
                status_text.text(f"{page}페이지 가져오는 중...")
                data = fetch_images(keyword, page)
                
                if "photos" not in data or len(data["photos"]) == 0:
                    break
                
                for photo in data["photos"]:
                    if total_images >= 35:
                        break
                    
                    image_url = photo["src"]["original"]
                    try:
                        img = download_and_process_image(image_url)
                        images.append(img)
                        total_images += 1
                        progress_bar.progress(total_images / 35)
                    except Exception as e:
                        st.error(f"이미지 처리 중 오류 발생: {e}")
                    
                    if total_images == 35:
                        break
                
                if total_images == 35:
                    break
                
                if "next_page" not in data:
                    break
                
                page += 1
                time.sleep(1)
            
            status_text.text(f"총 {total_images}개의 이미지를 처리했습니다.")
            
            if images:
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                    for i, img in enumerate(images):
                        img_buffer = BytesIO()
                        img.save(img_buffer, format="JPEG")
                        zip_file.writestr(f"{keyword}_{i+1}.jpg", img_buffer.getvalue())
                
                st.download_button(
                    label="처리된 이미지 다운로드",
                    data=zip_buffer.getvalue(),
                    file_name=f"{keyword}_processed_images.zip",
                    mime="application/zip"
                )
            else:
                st.warning("다운로드할 이미지가 없습니다.")
        else:
            st.warning("키워드를 입력해주세요.")

if __name__ == "__main__":
    main()
