import os
from flask import Flask, Response, abort
import pymysql

app = Flask(__name__)

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',
    'database': 'rasa_core'
}

BASE_IMAGE_DIR = "C:\pjw\image"  # 또는 "C:\\image" 둘 다 가능

@app.route('/image/<int:image_id>')
def get_image(image_id):
    try:
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT image FROM image_rules WHERE id = %s", (image_id,))
        result = cursor.fetchone()

        if result and result[0]:
            # DB에는 이미지 파일명만 저장했다고 가정 (예: pic1.jpg)
            image_file_name = result[0]

            # 절대경로 조합
            image_path = os.path.join(BASE_IMAGE_DIR, image_file_name)

            if not os.path.isfile(image_path):
                abort(404, description="이미지 파일이 서버에 존재하지 않습니다.")

            with open(image_path, 'rb') as f:
                image_data = f.read()

            if image_path.lower().endswith('.png'):
                mime_type = 'image/png'
            else:
                mime_type = 'image/jpeg'

            return Response(image_data, mimetype=mime_type)

        else:
            abort(404, description="이미지를 찾을 수 없습니다.")

    except Exception as e:
        return f"오류 발생: {str(e)}", 500

    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(port=8080)
