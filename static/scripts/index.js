function uploadAndDrawRect() {
    const fileInput = document.getElementById("imageInput");
    const file = fileInput.files[0];
    
    console.log("called");

    const formData = new FormData();
    formData.append("file", file);

    fetch("/recognize", {
        method: "POST",
        body: formData
    })
    .then(response => response.blob())
    .then(blob => {
        const imageUrl = URL.createObjectURL(blob);
        const outputImg = document.getElementById("result");
        outputImg.src = imageUrl;
    })
    .catch(error => console.error("Error:", error));
}