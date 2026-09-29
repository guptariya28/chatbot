const sources = data.sources || [];

if (sources.length) {

    // Main container
    const sourceContainer = document.createElement("div");
    sourceContainer.className = "source-container";


    // -------------------------
    // SOURCES BUTTON
    // -------------------------
    const sourceToggle = document.createElement("button");
    sourceToggle.className = "source-toggle";
    sourceToggle.type = "button";

    sourceToggle.innerHTML = `
        <span>Sources</span>
        <span class="source-arrow">▼</span>
    `;


    // -------------------------
    // FILE LIST
    // -------------------------
    const sourceList = document.createElement("div");
    sourceList.className = "source-list";

    // Hidden initially
    sourceList.style.display = "none";


    // -------------------------
    // ADD EACH SOURCE FILE
    // -------------------------
    sources.forEach((s) => {

        const filename =
            s.file_name ||
            s.filename ||
            s.name ||
            s.title ||
            "Source";

        const downloadUrl = s.download_url;

        if (!downloadUrl) return;


        const sourceLink = document.createElement("a");

        sourceLink.className = "source-file";

        sourceLink.href = downloadUrl;

        sourceLink.target = "_blank";
        sourceLink.rel = "noopener noreferrer";

        sourceLink.textContent = filename;

        sourceList.appendChild(sourceLink);
    });


    // -------------------------
    // OPEN / CLOSE SOURCES
    // -------------------------
    sourceToggle.addEventListener("click", () => {

        const isOpen = sourceList.style.display === "block";

        sourceList.style.display =
            isOpen ? "none" : "block";

        const arrow =
            sourceToggle.querySelector(".source-arrow");

        arrow.textContent =
            isOpen ? "▼" : "▲";
    });


    // -------------------------
    // ADD TO UI
    // -------------------------
    sourceContainer.appendChild(sourceToggle);
    sourceContainer.appendChild(sourceList);

    bubbleCol.appendChild(sourceContainer);
}
