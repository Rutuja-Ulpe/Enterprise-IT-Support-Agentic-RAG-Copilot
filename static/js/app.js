const chat = document.getElementById("chatMessages");
const form = document.getElementById("chatForm");
const question = document.getElementById("question");
const trace = document.getElementById("trace-list");
const sourceUsed = document.getElementById("sourceUsed");

/* Escape HTML to prevent unsafe HTML rendering */

function escapeHtml(value = "") {
    return String(value).replace(/[&<>'"]/g, function (char) {
        return {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            "'": "&#39;",
            '"': "&quot;"
        }[char];
    });
}

/* Convert Markdown-like text to HTML */

function formatText(value = "") {
    let text = escapeHtml(value);

    // Inline code: `example`
    text = text.replace(
        /`([^`]+)`/g,
        "<code>$1</code>"
    );

    // Bold text: **example**
    text = text.replace(
        /\*\*(.*?)\*\*/g,
        "<strong>$1</strong>"
    );

    // Convert line breaks
    text = text.replace(/\n/g, "<br>");

    return text;
}

/* Add user or assistant message */

function addMessage(
    role,
    text,
    source = "",
    citations = []
) {
    const wrap = document.createElement("div");

    wrap.className = `message ${role}`;

    let citeHtml = "";

    if (Array.isArray(citations) && citations.length > 0) {
        citeHtml = `
            <div class="citations">
                <strong>Sources</strong><br>
                ${citations
                    .map(function (citation) {
                        if (citation.url) {
                            return `
                                <a
                                    href="${escapeHtml(citation.url)}"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                >
                                    ${escapeHtml(
                                        citation.title || citation.url
                                    )}
                                </a>
                            `;
                        }

                        return escapeHtml(
                            citation.title || "Private KB"
                        );
                    })
                    .join("<br>")}
            </div>
        `;
    }

    const sourceHtml = source
        ? `
            <div class="answer-source">
                Source: ${escapeHtml(source)}
            </div>
        `
        : "";

    wrap.innerHTML = `
        <div class="avatar">
            ${role === "user" ? "You" : "AI"}
        </div>

        <div class="bubble">
            ${formatText(text)}
            ${sourceHtml}
            ${citeHtml}
        </div>
    `;

    chat.appendChild(wrap);

    chat.scrollTop = chat.scrollHeight;
}

/* Render LangGraph trace */

function renderTrace(items = []) {
    if (!Array.isArray(items) || items.length === 0) {
        trace.innerHTML = `
            <div class="empty">
                No trace.
            </div>
        `;
        return;
    }

    trace.innerHTML = items
        .map(function (item) {
            return `
                <div class="trace-item">
                    ${escapeHtml(item)}
                </div>
            `;
        })
        .join("");
}

/* Ask backend agent */

async function askAgent(query) {
    addMessage("user", query);

    question.value = "";

    renderTrace([
        "Running LangGraph workflow..."
    ]);

    sourceUsed.textContent = "Running";

    const button = form.querySelector("button");

    button.disabled = true;

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: query
            })
        });

        let data;

        try {
            data = await response.json();
        } catch (jsonError) {
            throw new Error(
                "Backend returned an invalid response."
            );
        }

        if (!response.ok) {
            throw new Error(
                data.detail || "Request failed"
            );
        }

        addMessage(
            "assistant",
            data.answer || "No answer received.",
            data.source_used || "",
            data.citations || []
        );

        renderTrace(data.trace || []);

        sourceUsed.textContent =
            data.source_used || "Private KB";

    } catch (error) {
        addMessage(
            "assistant",
            `Error: ${error.message}`
        );

        renderTrace([
            "Request failed"
        ]);

        sourceUsed.textContent = "Error";

        console.error("Chat error:", error);

    } finally {
        button.disabled = false;
    }
}

/* Submit question using Ask Agent button */

if (form) {
    form.addEventListener("submit", function (event) {
        event.preventDefault();

        const query = question.value.trim();

        if (query) {
            askAgent(query);
        }
    });
}

/* Suggested questions */

document
    .querySelectorAll(".suggestion-btn")
    .forEach(function (button) {
        button.addEventListener("click", function () {
            question.value =
                button.dataset.question ||
                button.textContent.trim();

            question.focus();
        });
    });

/* Upload modal */

const modal = document.getElementById("uploadModal");
const openUpload = document.getElementById("openUpload");
const closeUpload = document.getElementById("closeUpload");

if (openUpload && modal) {
    openUpload.onclick = function () {
        modal.classList.remove("hidden");
    };
}

if (closeUpload && modal) {
    closeUpload.onclick = function () {
        modal.classList.add("hidden");
    };
}

/* Close modal when clicking outside the modal card */

if (modal) {
    modal.addEventListener("click", function (event) {
        if (event.target === modal) {
            modal.classList.add("hidden");
        }
    });
}

/* Upload and ingest company document */

const uploadButton = document.getElementById("uploadBtn");

if (uploadButton) {
    uploadButton.onclick = async function () {
        const fileElement =
            document.getElementById("fileInput");

        const keyElement =
            document.getElementById("adminKey");

        const status =
            document.getElementById("uploadStatus");

        const file = fileElement.files[0];
        const key = keyElement.value.trim();

        if (!file) {
            status.textContent =
                "Please choose a file first.";
            return;
        }

        if (!key) {
            status.textContent =
                "Please enter the Admin API key.";
            return;
        }

        status.textContent =
            "Indexing document...";

        uploadButton.disabled = true;

        const formData = new FormData();

        formData.append("file", file);

        try {
            const response = await fetch("/api/ingest", {
                method: "POST",
                headers: {
                    "X-Admin-Key": key
                },
                body: formData
            });

            let data;

            try {
                data = await response.json();
            } catch (jsonError) {
                throw new Error(
                    "Invalid response from server."
                );
            }

            if (!response.ok) {
                throw new Error(
                    data.detail || "Upload failed"
                );
            }

            status.textContent =
                `Indexed ${data.file}: ${data.chunks} chunks.`;

        } catch (error) {
            status.textContent =
                `Error: ${error.message}`;

            console.error("Upload error:", error);

        } finally {
            uploadButton.disabled = false;
        }
    };
}