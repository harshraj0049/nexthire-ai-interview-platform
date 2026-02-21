const micBtn = document.getElementById("mic");
const camBtn = document.getElementById("cam");
const speakerBtn = document.getElementById("");
let mydiv=document.getElementById("user_container");
const container=document.getElementById("avatar_container");

let videostream=null;
let video=null;

if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    alert("Speech recognition not supported in this browser. Please use Chrome.");
}


camBtn.addEventListener('click', async ()=>{
    if(!videostream){
        try{
            video = document.createElement("video");
            video.classList.add("user");
            video.autoplay = true;
            video.playsInline = true;


            videostream=await navigator.mediaDevices.getUserMedia({video:true});
            video.srcObject =videostream;

            mydiv.remove();
            container.appendChild(video);
            camBtn.style.backgroundColor="red";
        }
        catch(error){
            alert(`video access error: ${error}`);
            console.error(error);
        }
    }
    else{
        mydiv=document.createElement("div");
        mydiv.classList.add("user");
        const innerdiv=document.createElement("div");
        innerdiv.classList.add("user_avatar");
        const image=document.createElement("img");
        image.src = "/static/images/user_avatar.png";
        image.id="user_photo";

        mydiv.appendChild(innerdiv);
        innerdiv.appendChild(image);

        videostream.getTracks().forEach(track =>track.stop());
        video.srcObject =null;
        videostream =null;
        video.remove();
        container.appendChild(mydiv);
        camBtn.style.backgroundColor="black";
    }  
})

let recognition;
let micstream = null;
let isMicOn = false;
let finalTranscript = "";

micBtn.addEventListener("click", async () => {

    if (!isMicOn) {
        // 🟢 START LISTENING
        try {
            micstream = await navigator.mediaDevices.getUserMedia({ audio: true });
            micBtn.style.backgroundColor = "red";
            isMicOn = true;
            finalTranscript = "";

            recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();

            recognition.lang = "en-US";
            recognition.continuous = true;
            recognition.interimResults = false;

            recognition.onresult = (event) => {
                const transcript = event.results[event.results.length - 1][0].transcript;
                finalTranscript += transcript + " ";
            };

            recognition.onerror = (event) => {
                console.error("Speech recognition error:", event.error);
            };

            recognition.start();

        } catch (error) {
            alert(`Microphone access error: ${error}`);
            console.error(error);
        }

    } else {
        // 🔴 STOP LISTENING → PROCESS
        isMicOn = false;
        micBtn.style.backgroundColor = "black";

        recognition.stop();

        micstream?.getTracks().forEach(track => track.stop());
        micstream = null;

        const transcript = finalTranscript.trim();

        if (transcript.length > 0) {

            document.getElementById("questionBox").value +=
                `YOU: ${transcript}\n\n`;

            try {
                await sendUserResponse(transcript);
                await getNextInterviewerMessage();
            } catch (err) {
                console.error(err);
            }

        } else {
            console.log("No speech detected");
        }
    }
});




const evaluateBtn=document.getElementById('eval_btn').addEventListener('click',async ()=>{
    const code = codeEditor.getValue();
    const response=await fetch(`/mock_interview/${interviewId}/check`,{
        method:'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: code })});

    const data = await response.json();
    document.getElementById('questionBox').value += `BOT (Evaluation) : ${data.content}\n\n`;
    speakReply(data.content);
})

async function sendUserResponse(text) {
    await fetch(`/mock_interview/${interviewId}/response`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            content: text
        })
    });
}

async function getNextInterviewerMessage() {
    const response = await fetch(`/mock_interview/${interviewId}/next`, {
        method: "POST"
    });

    const data = await response.json();

    document.getElementById('questionBox').value +=
        `INTERVIEWER: ${data.content}\n\n`;

    speakReply(data.content);
}


function speakReply(text) {
    window.speechSynthesis.cancel();

    const speech = new SpeechSynthesisUtterance(text);
    speech.lang = "en-US";
    speech.pitch = 1;
    speech.rate = 1;

    window.speechSynthesis.speak(speech);
}




