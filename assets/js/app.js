const API_URL =
    "https://1-2-aplicaciones-web-ia-seven.vercel.app/api/chat";


const form =
    document.getElementById("chatForm");

const input =
    document.getElementById("messageInput");

const messages =
    document.getElementById("messages");

const sendButton =
    document.getElementById("sendButton");


/* =========================================
   LIMPIAR MARCAS COMUNES DE MARKDOWN
========================================= */

function cleanMarkdown(text) {

    return text

        // Bloques de código
        .replace(/```[\w-]*\n?/g, "")

        // Encabezados Markdown
        .replace(/^#{1,6}\s+/gm, "")

        // Negritas
        .replace(/\*\*(.*?)\*\*/g, "$1")
        .replace(/__(.*?)__/g, "$1")

        // Cursivas simples
        .replace(/\*(.*?)\*/g, "$1")

        // Backticks
        .replace(/`([^`]+)`/g, "$1")

        .trim();
}


/* =========================================
   FORMATEAR RESPUESTA DEL ASISTENTE
========================================= */

function formatAssistantResponse(element, text) {

    const cleanedText =
        cleanMarkdown(text);

    const lines =
        cleanedText.split("\n");

    lines.forEach((originalLine) => {

        const line =
            originalLine.trim();


        // Ignorar líneas vacías
        if (!line) {
            return;
        }


        /* -------------------------
           Viñetas
        ------------------------- */

        if (
            line.startsWith("- ") ||
            line.startsWith("* ") ||
            line.startsWith("• ")
        ) {

            const item =
                document.createElement("div");

            item.classList.add(
                "response-item"
            );


            const bullet =
                document.createElement("span");

            bullet.classList.add(
                "response-bullet"
            );

            bullet.textContent = "•";


            const itemText =
                document.createElement("span");

            itemText.textContent =
                line.replace(
                    /^[-*•]\s*/,
                    ""
                );


            item.appendChild(bullet);

            item.appendChild(itemText);

            element.appendChild(item);

            return;
        }


        /* -------------------------
           Listas numeradas
        ------------------------- */

        if (/^\d+\.\s/.test(line)) {

            const item =
                document.createElement("div");

            item.classList.add(
                "response-item"
            );


            const match =
                line.match(/^(\d+)\.\s+(.*)$/);


            if (match) {

                const bullet =
                    document.createElement("span");

                bullet.classList.add(
                    "response-bullet"
                );

                bullet.textContent =
                    match[1] + ".";


                const itemText =
                    document.createElement("span");

                itemText.textContent =
                    match[2];


                item.appendChild(bullet);

                item.appendChild(itemText);

                element.appendChild(item);

                return;
            }
        }


        /* -------------------------
           Texto normal
        ------------------------- */

        const paragraph =
            document.createElement("p");

        paragraph.textContent =
            line;

        element.appendChild(paragraph);

    });
}


/* =========================================
   CREAR MENSAJE
========================================= */

function addMessage(text, type) {

    const container =
        document.createElement("div");

    container.classList.add(
        "message-row"
    );


    /*
        Si el mensaje es loading,
        visualmente pertenece al asistente.
    */

    if (type === "loading") {

        container.classList.add(
            "assistant",
            "loading"
        );

    }
    else {

        container.classList.add(type);

    }


    /* =========================
       AVATAR
    ========================= */

    const avatar =
        document.createElement("div");

    avatar.classList.add("avatar");


    if (type === "user") {

        avatar.classList.add(
            "user-avatar"
        );

        const icon =
            document.createElement("i");

        icon.className =
            "bi bi-person-fill";

        avatar.appendChild(icon);

    }
    else {

        avatar.classList.add(
            "assistant-avatar"
        );

        const icon =
            document.createElement("i");

        icon.className =
            "bi bi-stars";

        avatar.appendChild(icon);

    }


    /* =========================
       BLOQUE DEL MENSAJE
    ========================= */

    const messageBlock =
        document.createElement("div");

    messageBlock.classList.add(
        "message-block"
    );


    /* Etiqueta */

    const label =
        document.createElement("div");

    label.classList.add(
        "message-label"
    );


    if (type === "user") {

        label.textContent = "Tú";

    }
    else {

        label.textContent =
            "Asistente TIC";

    }


    /* Contenido */

    const content =
        document.createElement("div");

    content.classList.add(
        "message-content"
    );


    if (type === "assistant") {

        formatAssistantResponse(
            content,
            text
        );

    }
    else {

        content.textContent = text;

    }


    /* =========================
       ENSAMBLAR
    ========================= */

    messageBlock.appendChild(label);

    messageBlock.appendChild(content);


    container.appendChild(avatar);

    container.appendChild(messageBlock);


    messages.appendChild(container);


    /* Scroll automático */

    messages.scrollTo({
        top: messages.scrollHeight,
        behavior: "smooth"
    });


    return container;
}


/* =========================================
   ENVIAR MENSAJE
========================================= */

form.addEventListener(
    "submit",
    async (event) => {

        event.preventDefault();


        const message =
            input.value.trim();


        if (!message) {
            return;
        }


        /* Mostrar mensaje del usuario */

        addMessage(
            message,
            "user"
        );


        /* Limpiar input */

        input.value = "";

        input.disabled = true;

        sendButton.disabled = true;


        /* Mostrar mensaje de espera */

        const loading =
            addMessage(
                "Analizando tu consulta",
                "loading"
            );


        try {

            const response =
                await fetch(
                    API_URL,
                    {

                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({
                            message: message
                        })

                    }
                );


            /*
                Comprobamos el tipo de respuesta
                antes de convertirla a JSON.
            */

            const contentType =
                response.headers.get(
                    "content-type"
                ) || "";


            if (
                !contentType.includes(
                    "application/json"
                )
            ) {

                throw new Error(
                    "El servidor devolvió una respuesta no válida."
                );

            }


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.error ||
                    "Error del servidor."
                );

            }


            loading.remove();


            /* Mostrar respuesta IA */

            addMessage(
                data.reply,
                "assistant"
            );

        }
        catch (error) {

            loading.remove();


            addMessage(
                "No fue posible completar la consulta. " +
                error.message,
                "assistant"
            );

        }
        finally {

            input.disabled = false;

            sendButton.disabled = false;

            input.focus();

        }

    }
);