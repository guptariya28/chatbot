const sources = data.sources || [];

if (sources.length) {
    console.log("Sources received:", sources);

    const srcRow = document.createElement("div");
    srcRow.className = "sources-row";

    sources.forEach((s) => {

        // Backend keys
        const filename = s.file_name || "Source";
        const downloadUrl = s.download_url;

        // If URL is missing, don't create broken link
        if (!downloadUrl) {
            console.warn("No download_url for source:", s);
            return;
        }

        const a = document.createElement("a");

        a.className = "source-chip";

        // Use URL returned directly from backend
        a.href = downloadUrl;

        // Open source in new tab
        a.target = "_blank";
        a.rel = "noopener noreferrer";

        // Display file name
        a.textContent = filename;

        srcRow.appendChild(a);
    });

    if (srcRow.children.length > 0) {
        bubbleCol.appendChild(srcRow);
    }
}
