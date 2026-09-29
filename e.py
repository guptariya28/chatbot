const newChatBtn = document.getElementById("newChatBtn");
 
newChatBtn.addEventListener("click", async () => {
  try {
    const res = await fetch("/api/close-session", { method: "POST" });
    const data = await res.json();
    console.log(data.status);
  } catch (err) {
    console.error("Failed to close session:", err);
  }
  location.reload(); // simplest reset: back to the landing screen
});
