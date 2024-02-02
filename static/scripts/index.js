async function uploadAndDrawRect() {
    const fileInput = document.getElementById("imageInput");
    const file = fileInput.files[0];

    console.log("called");

    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch("/recognize", {
        method: "POST",
        body: formData,
    });

    const json = await response.json();

    console.log(json, "ascasc");
}

const video = document.getElementById("videoElement");

const canvas = document.getElementById('boxes');
const context = canvas.getContext('2d');

function drawBox(xMin, yMin, xMax, yMax, emotion) {
    switch (emotion) {
        case "neutral":
            context.strokeStyle = '#FFFFFF';
            context.fillStyle = '#FFFFFF';
            break;
        case "happy":
            context.strokeStyle = '#FFFF00';
            context.fillStyle = '#FFFF00';
            break;
        case "sad":
            context.strokeStyle = '#0000FF';
            context.fillStyle = '#0000FF';
            break;
        case "surprise":
            context.strokeStyle = '#00FF00';
            context.fillStyle = '#00FF00';
            break;
        case "anger":
            context.strokeStyle = '#FF0000';
            context.fillStyle = '#FF0000';
            break;
    }

    context.lineWidth = 5; // 테두리 두께 설정
    context.strokeRect(xMin, yMin, xMax - xMin, yMax - yMin); // x, y, width, height

    context.font = '20px Arial';
    context.fillText(emotion, xMin, yMin - 15); // 텍스트, x, y
}

function captureAndSendFrame() {
    const imageCanvas = document.createElement('canvas');
    imageCanvas.width = video.videoWidth;
    imageCanvas.height = video.videoHeight;

    console.log(video.videoWidth);
    console.log(video.videoHeight);
    const imageContext = imageCanvas.getContext('2d');
    imageContext.drawImage(video, 0, 0, imageCanvas.width, imageCanvas.height);
    
    // 캔버스에서 이미지 데이터 가져오기
    imageCanvas.toBlob((blob) => {
        const formData = new FormData();
        formData.append('file', blob, 'file.jpg');
        
        // 이미지 데이터를 서버로 전송 (Fetch API 사용)
        fetch('http://127.0.0.1:5000/recognize', {
            method: 'POST',
            body: formData,
        })
        .then(async (response) => {
            if (!response.ok) {
                throw new Error('Failed to upload frame.');
            }
            
            const { boxes } = await response.json();
            
            context.clearRect(0, 0, canvas.width, canvas.height);
            const ratio = 600 / 640;
            const fix = 30;
            for (const box of boxes) {
                drawBox(box.xMin * ratio, box.yMin * ratio - fix, box.xMax * ratio, box.yMax * ratio - fix, box.emotion);
            }
        })
        .then(data => {
            console.log('Frame uploaded successfully:', data);
        })
        .catch(error => {
            console.error('Error uploading frame:', error);
        });
    }, 'image/jpeg');
}

addEventListener("DOMContentLoaded", () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert("Media Device not supported");
        return;
    }
    
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(function (stream) {
            video.srcObject = stream;

            setInterval(captureAndSendFrame, 100);
        })
        .catch(function (error) {
            console.error('Error accessing webcam:', error);
        });
    
})