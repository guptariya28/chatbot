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


/* ---------- Sources dropdown ---------- */

.source-container {
    margin-top: 2px;
    padding: 0 2px;
}

.source-toggle {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--accent-soft);
    color: var(--accent-dark);
    border: 1px solid var(--accent-soft-2);
    border-radius: 999px;
    padding: 5px 11px;
    font-family: inherit;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: background .15s ease;
}

.source-toggle:hover {
    background: var(--accent-soft-2);
}

.source-arrow {
    font-size: 9px;
}

.source-list {
    margin-top: 7px;
    padding: 7px;
    min-width: 220px;
    max-width: 380px;
    background: var(--bg-soft);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
}

.source-file {
    display: block;
    padding: 7px 10px;
    color: var(--accent-dark);
    background: var(--bg);
    border-radius: 6px;
    font-size: 12.5px;
    font-weight: 500;
    text-decoration: none;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.source-file + .source-file {
    margin-top: 5px;
}

.source-file:hover {
    background: var(--accent-soft);
    text-decoration: underline;
}
    
    

    
