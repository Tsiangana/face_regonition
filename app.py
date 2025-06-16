from flask import Flask, request, jsonify
import face_recognition
import requests
from io import BytesIO
from PIL import Image
import gc

app = Flask(__name__)

def resize_image(image_bytes, max_size=(800, 800)):
    """Redimensiona a imagem para economizar memória"""
    img = Image.open(BytesIO(image_bytes))
    img.thumbnail(max_size)
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()

@app.route('/compare', methods=['POST'])
def compare_faces():
    try:
        data = request.json
        search_image_url = data.get("search_image_url")
        bucket_images = data.get("bucket_images", [])

        if not search_image_url:
            return jsonify({"error": "URL da imagem de busca não fornecida."}), 400
        if not bucket_images:
            return jsonify({"error": "Lista de imagens do bucket não fornecida."}), 400

        print(f"Baixando imagem de busca: {search_image_url}")
        search_response = requests.get(search_image_url, timeout=10)
        if search_response.status_code != 200:
            return jsonify({"error": f"Falha ao baixar imagem de busca: {search_response.status_code}"}), 400

        resized_search_image = resize_image(search_response.content)
        search_image = face_recognition.load_image_file(BytesIO(resized_search_image))
        search_encodings = face_recognition.face_encodings(search_image)

        if not search_encodings:
            return jsonify({"error": "Nenhum rosto detectado na imagem de busca."}), 400

        search_encoding = search_encodings[0]

        # Compara com cada imagem do bucket e para se encontrar
        for link in bucket_images:
            try:
                print(f"Comparando com: {link}")
                response = requests.get(link, timeout=10)
                if response.status_code != 200:
                    print(f"Falha ao baixar imagem: {link}, status: {response.status_code}")
                    continue

                resized_bucket_image = resize_image(response.content)
                img = face_recognition.load_image_file(BytesIO(resized_bucket_image))
                encodings = face_recognition.face_encodings(img)

                if not encodings:
                    print(f"Nenhum rosto encontrado em: {link}")
                    continue

                for encoding in encodings:
                    result = face_recognition.compare_faces([encoding], search_encoding, tolerance=0.5)
                    if result[0]:
                        print(f"Semelhança encontrada: {link}")
                        # Limpar memória antes de sair
                        del search_image, search_encodings, search_encoding, img, encodings, encoding
                        gc.collect()
                        return jsonify({"match": link})

                del img, encodings, resized_bucket_image
                gc.collect()

            except Exception as e:
                print(f"Erro ao processar imagem: {link}, erro: {e}")

        # Limpar memória antes de sair
        del search_image, search_encodings, search_encoding, resized_search_image
        gc.collect()

        return jsonify({"match": None})

    except Exception as e:
        import traceback
        gc.collect()
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)

