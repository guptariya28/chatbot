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


.source-container {
    margin-top: 10px;
}


/* Sources button */

.source-toggle {
    display: inline-flex;
    align-items: center;
    gap: 6px;

    padding: 6px 12px;

    border: 1px solid #d9dce3;
    border-radius: 16px;

    background: #f5f6fa;

    font-size: 13px;
    font-family: inherit;

    color: #444;

    cursor: pointer;
}

.source-toggle:hover {
    background: #e9ebf2;
}


/* Arrow */

.source-arrow {
    font-size: 10px;
}


/* Expanded source list */

.source-list {
    margin-top: 7px;

    padding: 8px 10px;

    background: #f8f9fb;

    border: 1px solid #e2e4e9;
    border-radius: 8px;

    max-width: 350px;
}


/* Individual filename */

.source-file {
    display: block;

    padding: 5px 4px;

    color: #4056b4;

    font-size: 13px;

    text-decoration: none;

    word-break: break-word;
}

.source-file:hover {
    text-decoration: underline;
}
