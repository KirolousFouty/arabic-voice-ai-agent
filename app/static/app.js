// `crypto.randomUUID` is restricted on some HTTP localhost configurations.
// A session identifier needs uniqueness, not cryptographic identity assurance.
const sid = globalThis.crypto?.randomUUID?.() || `browser-${Date.now()}-${Math.random().toString(36).slice(2)}`;
const log = document.querySelector("#log"), status = document.querySelector("#status");
const metrics = document.querySelector("#metrics"), mic = document.querySelector("#mic"), yes = document.querySelector("#yes");
let socket, socketReady, recorder, chunks = [];
const add = (who, text) => log.insertAdjacentHTML("beforeend", `<div class="msg ${who}"><b>${who === "me" ? "أنت" : "المساعد"}:</b> ${text}</div>`);
function connect() {
  if (socket?.readyState === WebSocket.OPEN) return Promise.resolve();
  socket = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/voice`);
  socketReady = new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = () => reject(new Error("تعذر الاتصال بخدمة الصوت.")); });
  socket.onmessage = async (event) => {
    if (typeof event.data !== "string") { new Audio(URL.createObjectURL(event.data)).play(); return; }
    const message = JSON.parse(event.data);
    if (message.type === "status") status.textContent = message.value;
    if (message.type === "transcript") add("me", message.text);
    if (message.type === "response") { add("agent", message.text); metrics.textContent = JSON.stringify(message.metrics, null, 2); yes.hidden = !message.requires_confirmation; }
    if (message.type === "error") status.textContent = message.message;
  };
  return socketReady;
}
async function startRecording() {
  if (!navigator.mediaDevices?.getUserMedia) throw new Error("متصفحك لا يدعم تسجيل الصوت. استخدم متصفحاً حديثاً.");
  status.textContent = "جارٍ طلب إذن الميكروفون…";
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  await connect();
  recorder = new MediaRecorder(stream);
  recorder.ondataavailable = (event) => chunks.push(event.data);
  recorder.onerror = () => { status.textContent = "حدث خطأ أثناء التسجيل."; };
  recorder.onstop = async () => {
    stream.getTracks().forEach((track) => track.stop());
    try {
      await socketReady;
      socket.send(JSON.stringify({ type: "start", session_id: sid }));
      socket.send(await new Blob(chunks, { type: recorder.mimeType || "audio/webm" }).arrayBuffer());
      status.textContent = "جارٍ إرسال التسجيل…";
    } catch (error) { status.textContent = error.message; }
    finally { chunks = []; recorder = null; mic.textContent = "🎙 ابدأ التسجيل"; }
  };
  recorder.start(); mic.textContent = "⏹ أوقف التسجيل";
  status.textContent = "جارٍ التسجيل — اضغط مرة أخرى عند الانتهاء";
}
mic.onclick = async () => {
  if (recorder?.state === "recording") { recorder.stop(); return; }
  try { await startRecording(); }
  catch (error) { status.textContent = `تعذر بدء التسجيل: ${error.message}`; mic.textContent = "🎙 حاول مرة أخرى"; }
};
yes.onclick = async () => {
  const response = await fetch("/api/confirm", { method: "POST", headers: { "content-type": "application/json", authorization: "Bearer demo-cust_demo" }, body: JSON.stringify({ session_id: sid, confirmed: true }) });
  const data = await response.json(); add("agent", data.text); yes.hidden = true;
};
