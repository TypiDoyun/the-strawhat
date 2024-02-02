import cv2
import json
from http import HTTPStatus
import numpy as np
from openvino.runtime import Core 
from flask import Flask, render_template, request, send_file, jsonify

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)

app = Flask(__name__)
ie = Core()

model = ie.read_model(model="./model/face-detection-adas-0001.xml")
face_model = ie.compile_model(model=model, device_name="CPU")

face_input_layer = face_model.input(0)
face_output_layer = face_model.output(0)

print("Face Model Input layer shape: ", face_input_layer.shape)
print("Face Model Output layer shape:", face_output_layer.shape)


model = ie.read_model(model="./model/emotions-recognition-retail-0003.xml")
emotion_model = ie.compile_model(model=model, device_name="CPU")

emotion_input_layer = model.input(0)
emotion_output_layer = emotion_model.output(0)

print("Emotion Model Input layer shape: ", emotion_input_layer.shape)
print("Emotion Model Output layer shape:", emotion_output_layer.shape)

def DrawBoundingBoxes(output, frame, conf=0.5):
    boxes = []
    h,w,_ = frame.shape
    
    predictions = output[0][0]                         # 하위 집합 데이터 프레임
    confidence = predictions[:,2]                       # conf 값 가져오기 [image_id, label, conf, x_min, y_min, x_max, y_max]
  
    top_predictions = predictions[(confidence>conf)]      # 임계값보다 큰 conf 값을 가진 예측만 선택
 
    for detection in top_predictions:
        box = (detection[3:7]* np.array([w, h, w, h])).astype("int") # 상자 위치 결정
        # (xmin, ymin, xmax, ymax) = box   # xmin, ymin, xmax, ymax에 상자 위치 값 지정
        boxes.append(box)
        # cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 0, 255), 2)       # 사각형 만들기
    
    return boxes

def DrawText(output, frame, face_position):
    
    emotions = {
        0:"neutral", # white
        1:"happy", # yellow
        2:"sad", # blue
        3:"surprise", # green
        4:"anger" # red
    }
                
    predictions = output[0,:,0,0]
   
    topresult_index = np.argmax(predictions)
    emotion = emotions[topresult_index]

    return {
        "xMin": face_position[0],
        "yMin": face_position[1],
        "xMax": face_position[2],
        "yMax": face_position[3],
        "emotion": emotion
    }
   
    # cv2.putText(frame, emotion,
    #             (face_position[0],face_position[1]),
    #             cv2.FONT_HERSHEY_SIMPLEX, 2, 
    #             (255, 255,255), 4)

@app.route("/", methods=["GET"])
def index():
    return render_template('index.html')

@app.route("/recognize", methods=["POST"])
def recognize():
    if 'file' not in request.files:
        print("error 0")
        return 'No file part in the request'

    file = request.files['file']

    if file.filename == '':
        print("error 1")
        return 'No selected file'
    
    # params = request.get_json()
    # print(params)

    image_bytes = file.read()
    image_np = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
    
    resized_frame = cv2.resize(src=frame, dsize=(672, 384)) 
    transposed_frame = resized_frame.transpose(2, 0, 1)
    input_frame = np.expand_dims(transposed_frame, 0)

    face_output = face_model([input_frame])[face_output_layer]
    boxes = DrawBoundingBoxes(face_output, frame, conf=0.5)

    emotionBoxes = []
    
    if boxes is not None:
        
        for box in boxes:
        
            xmin, ymin, xmax, ymax = box
            emotion_input = frame[ymin:ymax,xmin:xmax]

            if emotion_input.shape[0] < 64 or emotion_input.shape[1] < 64: continue
            
            resized_image = cv2.resize(src=emotion_input, dsize=(64, 64))
            transposed_image = resized_image.transpose(2, 0, 1)
            input_image = np.expand_dims(transposed_image, 0)
    
            emotion_output = emotion_model([input_image])[emotion_output_layer]
            emotionBoxes.append(DrawText(emotion_output, frame, box))

    # output_filepath = "output.jpg"

    # cv2.imwrite(output_filepath, frame)

    result = { "boxes": emotionBoxes }

    # return send_file(output_filepath, mimetype='image/jpeg')
    return json.dumps(result, cls=NpEncoder)

if __name__ == "__main__":
    # app.run()
    app.run(host="127.0.0.1")