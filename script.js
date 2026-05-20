// 弗洛伊德恋母情结分析 — 前端逻辑

(function () {
    const imgEl = document.getElementById("freud-image");
    const inputEl = document.getElementById("user-input");
    const btnEl = document.getElementById("analyze-btn");
    const outputContent = document.getElementById("output-content");
    const cursorEl = document.getElementById("cursor");
    const charCountEl = document.getElementById("char-count");

    const IMG = {
        default: "/image/default.png",
        listening: "/image/listening.png",
        thinking: "/image/thinking.png",
        talking: "/image/talking.png",
    };

    const HIGHLIGHT_TEXT = "你有恋母情结";
    const CHAR_DELAY = 50; // ms per char (~20 chars/sec)
    let isTyping = false;

    // --------------- 图片状态管理 ---------------
    function setImage(state) {
        const src = IMG[state];
        // 小技巧: 先设空再设新值, 确保过渡动画生效
        if (imgEl.src !== src) {
            imgEl.src = src;
        }
    }

    // --------------- 输入监听 ---------------
    inputEl.addEventListener("focus", function () {
        if (!isTyping) setImage("listening");
    });

    inputEl.addEventListener("blur", function () {
        if (!isTyping) setImage("default");
    });

    inputEl.addEventListener("input", function () {
        if (!isTyping) setImage("listening");
        var len = inputEl.value.length;
        charCountEl.textContent = len;
        if (len > 450) {
            charCountEl.style.color = "#c85a5a";
        } else {
            charCountEl.style.color = "";
        }
    });

    // --------------- 类型机效果 ---------------
    function typewriter(text) {
        return new Promise(function (resolve) {
            isTyping = true;
            setImage("talking");
            outputContent.innerHTML = "";
            cursorEl.style.display = "inline";

            var i = 0;
            var html = "";

            function tick() {
                if (i < text.length) {
                    // 检查是否到达高亮词起始位置
                    if (text.substring(i, i + HIGHLIGHT_TEXT.length) === HIGHLIGHT_TEXT) {
                        html += '<span class="highlight">' + HIGHLIGHT_TEXT + "</span>";
                        i += HIGHLIGHT_TEXT.length;
                    } else {
                        html += escapeHtml(text[i]);
                        i++;
                    }
                    outputContent.innerHTML = html;
                    setTimeout(tick, CHAR_DELAY);
                } else {
                    cursorEl.style.display = "none";
                    isTyping = false;
                    setImage("default");
                    resolve();
                }
            }

            tick();
        });
    }

    function escapeHtml(str) {
        var div = document.createElement("div");
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    // --------------- API 调用 ---------------
    async function analyze() {
        var text = inputEl.value.trim();
        if (!text || isTyping) return;

        // 禁用输入
        inputEl.disabled = true;
        btnEl.disabled = true;
        setImage("thinking");
        outputContent.innerHTML = "";
        cursorEl.style.display = "none";

        try {
            var resp = await fetch("/api/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: text }),
            });

            var data = await resp.json();

            if (!resp.ok || data.response === "我现在要休息了") {
                outputContent.innerHTML = "我现在要休息了";
                setImage("default");
                return;
            }

            // 开始打字机输出
            await typewriter(data.response);
        } catch (err) {
            outputContent.innerHTML = "我现在要休息了";
            setImage("default");
        } finally {
            inputEl.disabled = false;
            btnEl.disabled = false;
            isTyping = false;
        }
    }

    // --------------- 事件绑定 ---------------
    btnEl.addEventListener("click", analyze);

    inputEl.addEventListener("keydown", function (e) {
        // Ctrl+Enter 提交
        if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            analyze();
        }
    });

    // 初始化
    setImage("default");
})();
