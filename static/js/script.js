document.addEventListener("DOMContentLoaded", function () {
    initTypingEffect();
    initNavigation();
    initScrollReveal();
    initModals();
    initLightbox();
    initContactStatusModal();
});

function initTypingEffect() {
    const typing = document.querySelector(".typing");
    const caret = document.querySelector(".caret");
    if (!typing) return;

    const words = ["Full Stack Developer", "Web Designer", "Freelancer", "Motion Graphics Editor"];
    let wordIndex = 0;
    let letterIndex = 0;
    let isDeleting = false;

    function tick() {
        const currentWord = words[wordIndex];
        typing.textContent = currentWord.substring(0, letterIndex);

        let delay = 100;

        if (!isDeleting && letterIndex < currentWord.length) {
            letterIndex += 1;
        } else if (isDeleting && letterIndex > 0) {
            letterIndex -= 1;
            delay = 45;
        } else {
            isDeleting = !isDeleting;
            delay = isDeleting ? 1400 : 500;
            if (!isDeleting) {
                wordIndex = (wordIndex + 1) % words.length;
            }
        }

        if (caret) {
            caret.style.visibility = letterIndex === currentWord.length && !isDeleting ? "hidden" : "visible";
        }

        setTimeout(tick, delay);
    }

    tick();
}

function initNavigation() {
    const navToggle = document.querySelector(".nav-toggle");
    const nav = document.querySelector("header nav");
    if (!navToggle || !nav) return;

    navToggle.addEventListener("click", function () {
        const isOpen = nav.classList.toggle("open");
        navToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });

    nav.querySelectorAll("a").forEach(function (link) {
        link.addEventListener("click", function () {
            nav.classList.remove("open");
            navToggle.setAttribute("aria-expanded", "false");
        });
    });

    document.addEventListener("click", function (event) {
        if (!nav.contains(event.target) && !navToggle.contains(event.target)) {
            nav.classList.remove("open");
            navToggle.setAttribute("aria-expanded", "false");
        }
    });
}

function initScrollReveal() {
    const items = document.querySelectorAll(".reveal");
    if (!items.length) return;

    if (!("IntersectionObserver" in window)) {
        items.forEach(function (item) {
            item.classList.add("visible");
        });
        return;
    }

    const observer = new IntersectionObserver(
        function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add("visible");
                    observer.unobserve(entry.target);
                }
            });
        },
        { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );

    items.forEach(function (item) {
        observer.observe(item);
    });

    items.forEach(function (item) {
        const rect = item.getBoundingClientRect();
        if (rect.top < window.innerHeight && rect.bottom > 0) {
            item.classList.add("visible");
            observer.unobserve(item);
        }
    });
}

function lockPageScroll() {
    if (document.body.dataset.scrollLocked === "true") return;
    document.body.dataset.scrollLocked = "true";
    document.documentElement.classList.add("scroll-locked");
    document.body.classList.add("scroll-locked");
}

function unlockPageScroll() {
    if (document.body.dataset.scrollLocked !== "true") return;
    document.documentElement.classList.remove("scroll-locked");
    document.body.classList.remove("scroll-locked");
    delete document.body.dataset.scrollLocked;
}

function initModals() {
    const modalTriggers = document.querySelectorAll(".modal-trigger, .mg-modal-trigger");
    const modalOverlays = document.querySelectorAll(".modal-overlay");

    function closeModal(overlay) {
        if (document.activeElement instanceof HTMLElement) {
            document.activeElement.blur();
        }

        overlay.classList.remove("open");
        overlay.setAttribute("aria-hidden", "true");

        const anyOpenOverlay =
            document.querySelector(".modal-overlay.open") ||
            document.querySelector(".lightbox-overlay.open") ||
            document.querySelector(".status-modal-overlay.open");

        if (!anyOpenOverlay) {
            unlockPageScroll();
        }

        overlay.querySelectorAll(".mg-video").forEach(function (video) {
            video.pause();
            video.currentTime = 0;
        });
    }

    function openModal(overlay) {
        lockPageScroll();
        overlay.classList.add("open");
        overlay.setAttribute("aria-hidden", "false");
    }

    modalTriggers.forEach(function (trigger) {
        trigger.addEventListener("click", function () {
            const targetId = trigger.getAttribute("data-modal-target");
            const overlay = document.getElementById(targetId);
            if (overlay) openModal(overlay);
        });
    });

    modalOverlays.forEach(function (overlay) {
        const closeBtn = overlay.querySelector(".modal-close");
        if (closeBtn) {
            closeBtn.addEventListener("click", function (event) {
                event.preventDefault();
                closeModal(overlay);
            });
        }

        overlay.addEventListener("click", function (event) {
            if (event.target === overlay) closeModal(overlay);
        });

        overlay.querySelectorAll(".modal-site-link[href]").forEach(function (link) {
            link.addEventListener("click", function (event) {
                event.stopPropagation();
            });
        });
    });

    document.addEventListener("keydown", function (event) {
        if (event.key !== "Escape") return;
        modalOverlays.forEach(function (overlay) {
            if (overlay.classList.contains("open")) closeModal(overlay);
        });
    });
}

function initLightbox() {
    const lightboxOverlay = document.getElementById("lightboxOverlay");
    const viewport = document.getElementById("lightboxViewport");
    const lightboxImage = lightboxOverlay ? lightboxOverlay.querySelector(".lightbox-image") : null;
    const lightboxClose = lightboxOverlay ? lightboxOverlay.querySelector(".lightbox-close") : null;
    const lightboxPrev = lightboxOverlay ? lightboxOverlay.querySelector(".lightbox-prev") : null;
    const lightboxNext = lightboxOverlay ? lightboxOverlay.querySelector(".lightbox-next") : null;
    const zoomLevelEl = lightboxOverlay ? lightboxOverlay.querySelector(".lightbox-zoom-level") : null;

    if (!lightboxOverlay || !lightboxImage || !viewport) return;

    let lightboxImages = [];
    let lightboxIndex = 0;
    let scale = 1;
    let panX = 0;
    let panY = 0;
    let isDragging = false;
    let dragStartX = 0;
    let dragStartY = 0;
    let dragPanX = 0;
    let dragPanY = 0;

    const MIN_SCALE = 1;
    const MAX_SCALE = 4;
    const ZOOM_STEP = 0.2;

    function applyTransform() {
        lightboxImage.style.transform =
            "translate(calc(-50% + " + panX + "px), calc(-50% + " + panY + "px)) scale(" + scale + ")";
        viewport.classList.toggle("is-zoomed", scale > 1);
        if (zoomLevelEl) {
            zoomLevelEl.textContent = Math.round(scale * 100) + "%";
        }
    }

    function clampPan() {
        if (scale <= 1) {
            panX = 0;
            panY = 0;
            return;
        }

        const frameRect = viewport.getBoundingClientRect();
        const imageRect = lightboxImage.getBoundingClientRect();
        const maxPanX = Math.max(0, (imageRect.width - frameRect.width) / 2);
        const maxPanY = Math.max(0, (imageRect.height - frameRect.height) / 2);
        panX = Math.min(maxPanX, Math.max(-maxPanX, panX));
        panY = Math.min(maxPanY, Math.max(-maxPanY, panY));
    }

    function resetZoom() {
        scale = 1;
        panX = 0;
        panY = 0;
        viewport.classList.remove("is-panning");
        applyTransform();
    }

    function setScale(nextScale, originX, originY) {
        const previousScale = scale;
        scale = Math.min(MAX_SCALE, Math.max(MIN_SCALE, nextScale));

        if (originX != null && originY != null && previousScale !== scale) {
            const frameRect = viewport.getBoundingClientRect();
            const offsetX = originX - frameRect.left - frameRect.width / 2;
            const offsetY = originY - frameRect.top - frameRect.height / 2;
            const ratio = scale / previousScale;
            panX = offsetX - (offsetX - panX) * ratio;
            panY = offsetY - (offsetY - panY) * ratio;
        }

        if (scale === 1) {
            panX = 0;
            panY = 0;
        } else {
            clampPan();
        }

        applyTransform();
    }

    function openLightbox(index) {
        if (!lightboxImages.length) return;
        lightboxIndex = index;
        resetZoom();
        lightboxImage.src = lightboxImages[lightboxIndex].src;
        lightboxImage.alt = lightboxImages[lightboxIndex].alt || "Zoomed screenshot";
        lightboxOverlay.classList.add("open");
        lightboxOverlay.setAttribute("aria-hidden", "false");
        lockPageScroll();
    }

    function closeLightbox() {
        if (document.activeElement instanceof HTMLElement) {
            document.activeElement.blur();
        }

        lightboxOverlay.classList.remove("open");
        lightboxOverlay.setAttribute("aria-hidden", "true");
        lightboxImage.src = "";
        resetZoom();

        const anyOpenOverlay =
            document.querySelector(".modal-overlay.open") ||
            document.querySelector(".lightbox-overlay.open") ||
            document.querySelector(".status-modal-overlay.open");

        if (!anyOpenOverlay) {
            unlockPageScroll();
        }
    }

    function showNext(delta) {
        if (!lightboxImages.length) return;
        lightboxIndex = (lightboxIndex + delta + lightboxImages.length) % lightboxImages.length;
        resetZoom();
        lightboxImage.src = lightboxImages[lightboxIndex].src;
        lightboxImage.alt = lightboxImages[lightboxIndex].alt || "Zoomed screenshot";
    }

    document.querySelectorAll(".modal-gallery .website-shot").forEach(function (img) {
        img.addEventListener("click", function () {
            const gallery = img.closest(".modal-gallery");
            if (!gallery) return;
            lightboxImages = Array.from(gallery.querySelectorAll(".website-shot"));
            const index = lightboxImages.indexOf(img);
            if (index !== -1) openLightbox(index);
        });
    });

    if (lightboxClose) {
        lightboxClose.addEventListener("click", function (event) {
            event.preventDefault();
            closeLightbox();
        });
    }
    if (lightboxPrev) lightboxPrev.addEventListener("click", function () { showNext(-1); });
    if (lightboxNext) lightboxNext.addEventListener("click", function () { showNext(1); });

    lightboxOverlay.querySelectorAll("[data-zoom]").forEach(function (button) {
        button.addEventListener("click", function () {
            const action = button.getAttribute("data-zoom");
            if (action === "in") {
                setScale(scale + ZOOM_STEP);
            } else if (action === "out") {
                setScale(scale - ZOOM_STEP);
            } else {
                resetZoom();
            }
        });
    });

    viewport.addEventListener("wheel", function (event) {
        if (!lightboxOverlay.classList.contains("open")) return;
        event.preventDefault();
        const delta = event.deltaY < 0 ? ZOOM_STEP : -ZOOM_STEP;
        setScale(scale + delta, event.clientX, event.clientY);
    }, { passive: false });

    viewport.addEventListener("mousedown", function (event) {
        if (scale <= 1 || event.button !== 0) return;
        isDragging = true;
        dragStartX = event.clientX;
        dragStartY = event.clientY;
        dragPanX = panX;
        dragPanY = panY;
        viewport.classList.add("is-panning");
    });

    window.addEventListener("mousemove", function (event) {
        if (!isDragging) return;
        panX = dragPanX + (event.clientX - dragStartX);
        panY = dragPanY + (event.clientY - dragStartY);
        clampPan();
        applyTransform();
    });

    window.addEventListener("mouseup", function () {
        isDragging = false;
        viewport.classList.remove("is-panning");
    });

    viewport.addEventListener("dblclick", function (event) {
        if (scale > 1) {
            resetZoom();
        } else {
            setScale(2, event.clientX, event.clientY);
        }
    });

    lightboxOverlay.addEventListener("click", function (event) {
        if (event.target === lightboxOverlay) closeLightbox();
    });

    document.addEventListener("keydown", function (event) {
        if (!lightboxOverlay.classList.contains("open")) return;
        if (event.key === "Escape") closeLightbox();
        if (event.key === "ArrowRight") showNext(1);
        if (event.key === "ArrowLeft") showNext(-1);
        if (event.key === "+" || event.key === "=") setScale(scale + ZOOM_STEP);
        if (event.key === "-") setScale(scale - ZOOM_STEP);
        if (event.key === "0") resetZoom();
    });
}

function initContactStatusModal() {
    const status = document.body.dataset.contactStatus;
    if (!status) return;

    const overlay = document.getElementById("contactStatusModal");
    if (!overlay) return;

    const title = overlay.querySelector("#statusTitle");
    const text = overlay.querySelector("#statusText");
    const closeBtn = overlay.querySelector(".status-modal-close");
    const okBtn = overlay.querySelector(".status-modal-button");

    if (status === "success") {
        title.textContent = "Message sent!";
        text.textContent = "Thank you for reaching out. I will get back to you as soon as possible.";
    } else if (status === "error") {
        title.textContent = "Message not sent";
        text.textContent = "Something went wrong while sending your message. Please try again later or use the email shown on this page.";
    } else {
        return;
    }

    function closeStatusModal() {
        overlay.classList.remove("open");
        overlay.setAttribute("aria-hidden", "true");
        unlockPageScroll();
    }

    function openStatusModal() {
        lockPageScroll();
        overlay.classList.add("open");
        overlay.setAttribute("aria-hidden", "false");
    }

    if (closeBtn) closeBtn.addEventListener("click", closeStatusModal);
    if (okBtn) okBtn.addEventListener("click", closeStatusModal);

    overlay.addEventListener("click", function (event) {
        if (event.target === overlay) closeStatusModal();
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && overlay.classList.contains("open")) closeStatusModal();
    });

    openStatusModal();
}
