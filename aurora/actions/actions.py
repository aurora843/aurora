import mysql.connector
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from typing import Any, Text, Dict, List
import difflib
from googletrans import Translator # googletrans 라이브러리 설치 필요 (pip install googletrans==4.0.0-rc1)

class ActionChatBot(Action):

    def name(self) -> Text:
        return "action_chatbot"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        original_message = tracker.latest_message.get('text')
        translator = Translator()

        # 언어 감지 및 번역
        detected_lang = 'ko' # 기본값 한국어
        translated_msg = original_message
        try:
            if original_message: # 메시지가 비어있지 않은 경우에만 감지/번역 시도
                detected = translator.detect(original_message)
                if detected:
                    detected_lang = detected.lang
                    if detected_lang != 'ko':
                        translated_msg = translator.translate(original_message, src=detected_lang, dest='ko').text
        except Exception as e:
            print(f"번역 중 오류 발생: {e}. 원본 메시지로 계속 진행합니다.")
            # 번역 실패 시 translated_msg는 original_message 그대로 사용됨, detected_lang은 'ko' 유지

        # DB 연결 (중요: 실제 운영 시에는 환경 변수 등으로 안전하게 관리하세요)
        conn = mysql.connector.connect(
            host='127.0.0.1',
            user='root',
            password='1234', # 사용자님이 마지막으로 보여주신 actions.py 기준 비밀번호
            database='rasa_core'
        )
        cursor = conn.cursor()

        # 이미지 ID 매핑 (규칙 카테고리 -> images 테이블의 ID)
        # 이 key 값들은 rules_data 테이블의 category 값과 일치해야 합니다.
        category_image_ids = {
            "일반 규칙": 1,
            "기숙사 시설 이용": 2,
            "주의사항 (화재)": 3,
            "주의사항 (화상)": 4,
            "기타 주의사항": 5,
            "금지 행위": 6,
            "상벌 제도": 7,
            "세탁 카페": 8,
            "버스 시간표": 9
            # "연락처 정보": 10 # 연락처에 대한 이미지는 별도 로직 또는 이 딕셔너리 활용 결정 필요
        }

        try:
            # ------------------- 연락처 카테고리 목록 요청 -------------------
            if "연락처 목록" in translated_msg or "연락처 카테고리" in translated_msg or "연락처 종류" in translated_msg:
                query = "SELECT DISTINCT category FROM chatbot" # 수정: chatbot 테이블 및 category 컬럼 사용
                cursor.execute(query)
                rows = cursor.fetchall()

                if rows:
                    categories = [row[0] for row in rows]
                    result = "\n- " + "\n- ".join(categories)
                    message = f"📞 현재 등록된 연락처 카테고리는 다음과 같습니다:\n{result}"
                else:
                    message = "연락처 카테고리가 등록되어 있지 않습니다."
                
                final_msg = translator.translate(message, src='ko', dest=detected_lang).text if detected_lang != 'ko' else message
                dispatcher.utter_message(text=final_msg)
                return []

            # ------------------- 규칙 카테고리 목록 요청 -------------------
            # "카테고리" 키워드가 연락처와 겹칠 수 있어 NLU 인텐트 분리가 더 좋음. "규칙" 포함 시 규칙으로 간주.
            if ("규칙 목록" in translated_msg or "규칙 리스트" in translated_msg or \
                ("카테고리" in translated_msg and ("규칙" in translated_msg or "안내" in translated_msg)) and \
                not ("연락처" in translated_msg)): # 연락처 카테고리 요청과 구분 강화
                
                # 중요: 'rules_data' 테이블이 category 컬럼을 가지고 있다고 가정합니다.
                # 이 테이블은 직접 만드셔야 합니다.
                query = "SELECT DISTINCT category FROM rules_data" # 수정: rules_data 테이블 사용
                cursor.execute(query)
                rows = cursor.fetchall()

                if rows:
                    categories = [row[0] for row in rows]
                    result = "\n- " + "\n- ".join(categories)
                    message = f"📚 현재 가능한 규칙 카테고리는 다음과 같습니다:\n{result}"
                else:
                    message = "등록된 규칙 카테고리가 없습니다."
                
                final_msg = translator.translate(message, src='ko', dest=detected_lang).text if detected_lang != 'ko' else message
                dispatcher.utter_message(text=final_msg)
                return []

            # ------------------- 규칙 카테고리 판별 (키워드 기반) -------------------
            # 이 부분은 규칙 관련 정보를 조회하기 위한 카테고리를 결정합니다.
            determined_rule_category = None # 변수명 변경으로 명확화
            if "일반 규칙" in translated_msg: determined_rule_category = "일반 규칙"
            elif "기숙사 시설 이용" in translated_msg or "기숙사" in translated_msg: determined_rule_category = "기숙사 시설 이용"
            elif "주의사항 (화재)" in translated_msg or "화재" in translated_msg: determined_rule_category = "주의사항 (화재)"
            elif "주의사항 (화상)" in translated_msg or "화상" in translated_msg: determined_rule_category = "주의사항 (화상)"
            elif "기타 주의사항" in translated_msg or "기타" in translated_msg: determined_rule_category = "기타 주의사항"
            elif "금지 행위" in translated_msg or "금지" in translated_msg: determined_rule_category = "금지 행위"
            elif "상벌 제도" in translated_msg or "상벌" in translated_msg: determined_rule_category = "상벌 제도"
            elif "세탁 카페" in translated_msg or "세탁" in translated_msg: determined_rule_category = "세탁 카페"
            elif "버스 시간표" in translated_msg or "버스" in translated_msg: determined_rule_category = "버스 시간표"

            # ------------------- 규칙 세부 내용 + 이미지 먼저 출력 (determined_rule_category 사용) ---
            if determined_rule_category:
                # 이미지 먼저 보내기 (해당하는 이미지가 있다면)
                image_to_send_url = None
                if determined_rule_category in category_image_ids:
                    image_id = category_image_ids[determined_rule_category]
                    image_to_send_url = f"http://127.0.0.1:8080/image/{image_id}"
                else:
                    # 중요: 'rule_images' 테이블이 (category_name VARCHAR, image_id INT) 구조라고 가정합니다.
                    # 이 테이블은 직접 만드셔야 합니다. image_id는 images 테이블의 id를 참조합니다.
                    query_img = "SELECT image_id FROM rule_images WHERE category_name = %s" # 수정: 테이블명/컬럼명 확인 필요
                    cursor.execute(query_img, (determined_rule_category,))
                    image_row = cursor.fetchone() # 대표 이미지 하나만 가정
                    if image_row and image_row[0]:
                        image_id = image_row[0]
                        image_to_send_url = f"http://127.0.0.1:8080/image/{image_id}"
                
                if image_to_send_url:
                    dispatcher.utter_message(image=image_to_send_url)

                # 다음으로 텍스트 설명 보내기
                # 중요: 'rules_data' 테이블이 category, sub_category, details 컬럼을 가지고 있다고 가정합니다.
                query_text = "SELECT sub_category, details FROM rules_data WHERE category = %s" # 수정: rules_data 테이블 사용
                cursor.execute(query_text, (determined_rule_category,))
                rows_text = cursor.fetchall()

                if rows_text:
                    lines = [f"- {row[0]} → {row[1]}" for row in rows_text] # row[0]=sub_category, row[1]=details
                    result = "\n".join(lines)
                    message = f"📚 [{determined_rule_category} 안내]\n{result}"
                elif not image_to_send_url: # 이미지도 없고 텍스트도 없을 때만 메시지 전송
                    message = "해당 규칙에 대한 상세 정보나 이미지를 찾을 수 없습니다."
                else: # 이미지는 보냈지만 텍스트가 없는 경우
                    message = f"📚 [{determined_rule_category}] 관련 이미지를 확인해주세요." 
                    # 또는 아무 메시지도 보내지 않거나, "이미지를 확인하세요" 정도의 간단한 메시지
                
                final_msg = translator.translate(message, src='ko', dest=detected_lang).text if detected_lang != 'ko' else message
                dispatcher.utter_message(text=final_msg)
                return []

            # ------------------- 연락처 구분 유사 매칭 (difflib) -------------------
            # 이 블록은 연락처 정보를 조회하므로 chatbot 테이블을 사용합니다.
            query_contact_categories = "SELECT DISTINCT category FROM chatbot" # 수정
            cursor.execute(query_contact_categories)
            all_db_contact_categories = [row[0] for row in cursor.fetchall()]

            matched_contact_category = None # 변수명 명확화
            # difflib는 번역된 메시지와 DB의 한국어 카테고리를 비교
            matches = difflib.get_close_matches(translated_msg, all_db_contact_categories, n=1, cutoff=0.5)
            if matches:
                matched_contact_category = matches[0]
            else:
                for db_cat_contact in all_db_contact_categories: # 변수명 변경
                    if db_cat_contact in translated_msg: # translated_msg에서 DB 카테고리명 직접 포함하는지 확인
                        matched_contact_category = db_cat_contact
                        break
            
            if matched_contact_category:
                # 연락처에 대한 이미지를 보여줄지 여부는 여기서 결정. 
                # 예를 들어, "연락처 정보" 카테고리에 대한 이미지가 category_image_ids에 있다면 사용 가능
                if matched_contact_category == "연락처 정보" and "연락처 정보" in category_image_ids:
                     image_id_contact = category_image_ids["연락처 정보"]
                     dispatcher.utter_message(image=f"http://127.0.0.1:8080/image/{image_id_contact}")

                query_contact_details = "SELECT sub_category, details FROM chatbot WHERE category = %s" # 수정
                cursor.execute(query_contact_details, (matched_contact_category,))
                rows = cursor.fetchall()

                if rows:
                    lines = [f"- {row[0]} → {row[1]}" for row in rows]
                    result = "\n".join(lines)
                    message = f"📞 [{matched_contact_category}] 연락처 세부항목 목록입니다:\n{result}"
                else:
                    message = "해당 구분에 연락처 세부항목이 없습니다."
                
                final_msg = translator.translate(message, src='ko', dest=detected_lang).text if detected_lang != 'ko' else message
                dispatcher.utter_message(text=final_msg)
                return []

            # ------------------- 연락처 세부항목 직접 매칭 (키워드 기반) ---------
            # 이 블록도 연락처 정보를 조회하므로 chatbot 테이블을 사용합니다.
            query_all_contact_sub_items = "SELECT sub_category, details FROM chatbot" # 수정
            cursor.execute(query_all_contact_sub_items)
            all_db_contact_sub_items_details = cursor.fetchall()

            matched_contact_sub_item_info = None
            for db_sub_cat, db_contact_detail in all_db_contact_sub_items_details: # 변수명 변경
                if db_sub_cat and db_sub_cat in translated_msg: 
                    matched_contact_sub_item_info = (db_sub_cat, db_contact_detail)
                    break
            
            if matched_contact_sub_item_info:
                sub_item_name, sub_item_detail_text = matched_contact_sub_item_info # 변수명 변경
                message = f"{sub_item_detail_text}" # 상세 내용만 출력
                final_msg = translator.translate(message, src='ko', dest=detected_lang).text if detected_lang != 'ko' else message
                dispatcher.utter_message(text=final_msg)
                return []

            # ------------------- 처리 실패 시 (가장 마지막 fallback)-------------------
            message = "죄송해요. 해당 내용을 이해하지 못했어요. 다시 질문해 주세요."
            final_msg = translator.translate(message, src='ko', dest=detected_lang).text if detected_lang != 'ko' else message
            dispatcher.utter_message(text=final_msg)
            return []

        except mysql.connector.Error as e:
            print(f"actions.py DB 오류: {e}")
            # 사용자에게 보여줄 메시지는 번역할 필요가 있을 수 있습니다.
            error_message_ko = "죄송합니다, 정보를 처리하는 중 데이터베이스 오류가 발생했어요."
            final_error_msg = translator.translate(error_message_ko, src='ko', dest=detected_lang).text if detected_lang != 'ko' else error_message_ko
            dispatcher.utter_message(text=final_error_msg)
            return []
        except Exception as e:
            print(f"actions.py 일반 오류: {e}")
            error_message_ko = "죄송합니다, 예상치 못한 오류가 발생했습니다."
            final_error_msg = translator.translate(error_message_ko, src='ko', dest=detected_lang).text if detected_lang != 'ko' else error_message_ko
            dispatcher.utter_message(text=final_error_msg)
            return []
        finally:
            if conn and conn.is_connected():
                if cursor:
                    cursor.close()
                conn.close()