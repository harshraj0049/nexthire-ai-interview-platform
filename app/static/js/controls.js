// ================= ELEMENTS =================
const micBtn = document.getElementById("mic");
const camBtn = document.getElementById("cam");
const questionBox = document.getElementById("questionBox");

let mydiv = document.getElementById("user_container");
const container = document.getElementById("avatar_container");

let videostream = null;
let video = null;

// ================= CAMERA =================
camBtn.addEventListener("click", async () => {

    if (!videostream) {
        try {
            video = document.createElement("video");
            video.classList.add("user");
            video.autoplay = true;
            video.playsInline = true;

            videostream = await navigator.mediaDevices.getUserMedia({ video: true });
            video.srcObject = videostream;

            mydiv.remove();
            container.appendChild(video);
            camBtn.style.backgroundColor = "red";
        } catch (error) {
            alert(`video access error: ${error}`);
            console.error(error);
        }
    } else {
        mydiv = document.createElement("div");
        mydiv.classList.add("user");

        const innerdiv = document.createElement("div");
        innerdiv.classList.add("user_avatar");

        const image = document.createElement("img");
        image.src = "/static/images/user_avatar.png";
        image.id = "user_photo";

        mydiv.appendChild(innerdiv);
        innerdiv.appendChild(image);

        videostream.getTracks().forEach(track => track.stop());
        video.srcObject = null;
        videostream = null;
        video.remove();

        container.appendChild(mydiv);
        camBtn.style.backgroundColor = "black";
    }
});


// ================= SPEECH SUPPORT =================
if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    alert("Speech recognition not supported. Use Chrome.");
}


// ================= MIC STATE =================
let recognition = null;
let isMicOn = false;


// ================= CREATE RECOGNITION =================
function createRecognition() {

    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SR();

    recognition.lang = "en-US";
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    // ⭐ RESULTS (LIVE UI UPDATE)
    recognition.onresult = (event) => {

        for (let i = event.resultIndex; i < event.results.length; i++) {

            const text = event.results[i][0].transcript;

            if (event.results[i].isFinal) {

                console.log("FINAL:", text);

                // update UI immediately
                questionBox.value += `YOU: ${text}\n\n`;

                // send to backend
                sendUserResponse(text)
                    .then(getNextInterviewerMessage)
                    .catch(console.error);
            }
        }
    };

    recognition.onerror = (event) => {
        console.log("speech error:", event.error);
    };

    // ⭐ SAFE AUTO RESTART
    recognition.onend = () => {
        if (isMicOn) {
            console.log("restarting recognition…");
            recognition.start();
        }
    };

    recognition.onspeechstart = () => console.log("🗣 speech detected");
    recognition.onspeechend = () => console.log("speech ended");
}


// ================= MIC TOGGLE =================
micBtn.addEventListener("click", async () => {

    // START
    if (!isMicOn) {

        isMicOn = true;
        micBtn.style.backgroundColor = "red";

        createRecognition();

        setTimeout(() => recognition.start(), 300);
        return;
    }

    // STOP
    isMicOn = false;
    micBtn.style.backgroundColor = "black";

    recognition?.stop();
    recognition = null;
});


// ================= EVALUATE =================
document.getElementById('eval_btn').addEventListener('click', async () => {

    const code = codeEditor.getValue();

    const response = await fetch(`/mock_interview/${interviewId}/check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code })
    });

    const data = await response.json();

    questionBox.value += `BOT (Evaluation): ${data.content}\n\n`;
    speakReply(data.content);
});


// ================= BACKEND CALLS =================
async function sendUserResponse(text) {

    await fetch(`/mock_interview/${interviewId}/response`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: text })
    });
}


async function getNextInterviewerMessage() {

    const response = await fetch(`/mock_interview/${interviewId}/next`, {
        method: "POST"
    });

    const data = await response.json();

    questionBox.value += `${data.content}\n\n`;

    speakReply(data.content);
}


// ================= TEXT TO SPEECH =================
function speakReply(text) {

    window.speechSynthesis.cancel();

    const speech = new SpeechSynthesisUtterance(text);
    speech.lang = "en-US";
    speech.pitch = 1;
    speech.rate = 1;

    window.speechSynthesis.speak(speech);
}