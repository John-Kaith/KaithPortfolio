document.addEventListener("DOMContentLoaded", function () {
    const typing = document.querySelector(".typing");
    const words = ["Full Stack Developer", "Web Designer", "Freelancer",];
    let wordIndex = 0;
    let letterIndex = 0;
    let isDeleting = false;
    let speed = 100; // Typing speed

    if (typing) {
        function typeEffect() {
            let currentWord = words[wordIndex];
            let displayText = currentWord.substring(0, letterIndex);
            
            // Ensure gradient effect is applied properly
            typing.innerHTML = `<span class="gradient-text">${displayText}</span><span class="cursor"></span>`;

            if (!isDeleting && letterIndex < currentWord.length) {
                letterIndex++;
                speed = 100; // Speed when typing
            } else if (isDeleting && letterIndex > 0) {
                letterIndex--;
                speed = 50; // Speed when erasing
            } else {
                isDeleting = !isDeleting;
                speed = 1000; // Pause before typing next word
                if (!isDeleting) {
                    wordIndex = (wordIndex + 1) % words.length; // Move to next word
                }
            }

            setTimeout(typeEffect, speed);
        }

        typeEffect(); // Start the typing effect
    }

    const navToggle = document.querySelector(".nav-toggle");
    const nav = document.querySelector("header nav");

    if (navToggle && nav) {
        navToggle.addEventListener("click", function () {
            nav.classList.toggle("open");
        });
    }

    // Generic modal logic (websites + motion graphics)
    const modalTriggers = document.querySelectorAll(".modal-trigger, .mg-modal-trigger");
    const modalOverlays = document.querySelectorAll(".modal-overlay");

    function closeModal(overlay) {
        overlay.classList.remove("open");
        overlay.setAttribute("aria-hidden", "true");

        // Pause and reset motion graphics videos inside this overlay (if any)
        const videos = overlay.querySelectorAll(".mg-video");
        videos.forEach(v => {
            v.pause();
            v.currentTime = 0;
        });
    }

    modalTriggers.forEach(trigger => {
        trigger.addEventListener("click", () => {
            const targetId = trigger.getAttribute("data-modal-target") || "mg-modal";
            const overlay = document.getElementById(targetId);
            if (!overlay) return;
            overlay.classList.add("open");
            overlay.setAttribute("aria-hidden", "false");
        });
    });

    modalOverlays.forEach(overlay => {
        const closeBtn = overlay.querySelector(".modal-close");

        if (closeBtn) {
            closeBtn.addEventListener("click", () => closeModal(overlay));
        }

        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) {
                closeModal(overlay);
            }
        });
    });

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            modalOverlays.forEach(overlay => {
                if (overlay.classList.contains("open")) {
                    closeModal(overlay);
                }
            });
        }
    });

    // Lightbox for website gallery images inside modals
    const lightboxOverlay = document.getElementById("lightboxOverlay");
    const lightboxImage = lightboxOverlay ? lightboxOverlay.querySelector(".lightbox-image") : null;
    const lightboxClose = lightboxOverlay ? lightboxOverlay.querySelector(".lightbox-close") : null;
    const lightboxPrev = lightboxOverlay ? lightboxOverlay.querySelector(".lightbox-prev") : null;
    const lightboxNext = lightboxOverlay ? lightboxOverlay.querySelector(".lightbox-next") : null;

    let lightboxImages = [];
    let lightboxIndex = 0;

    function openLightbox(index) {
        if (!lightboxOverlay || !lightboxImage || lightboxImages.length === 0) return;
        lightboxIndex = index;
        lightboxImage.src = lightboxImages[lightboxIndex].src;
        lightboxOverlay.classList.add("open");
        lightboxOverlay.setAttribute("aria-hidden", "false");
    }

    function closeLightbox() {
        if (!lightboxOverlay) return;
        lightboxOverlay.classList.remove("open");
        lightboxOverlay.setAttribute("aria-hidden", "true");
    }

    function showNext(delta) {
        if (lightboxImages.length === 0) return;
        lightboxIndex = (lightboxIndex + delta + lightboxImages.length) % lightboxImages.length;
        lightboxImage.src = lightboxImages[lightboxIndex].src;
    }

    const galleryImages = document.querySelectorAll(".modal-gallery .website-shot");
    if (galleryImages.length && lightboxOverlay && lightboxImage) {
        galleryImages.forEach(img => {
            img.style.cursor = "pointer";
            img.addEventListener("click", () => {
                const gallery = img.closest(".modal-gallery");
                if (!gallery) return;
                lightboxImages = Array.from(gallery.querySelectorAll(".website-shot"));
                const index = lightboxImages.indexOf(img);
                if (index !== -1) {
                    openLightbox(index);
                }
            });
        });

        if (lightboxClose) {
            lightboxClose.addEventListener("click", closeLightbox);
        }

        if (lightboxPrev) {
            lightboxPrev.addEventListener("click", () => showNext(-1));
        }

        if (lightboxNext) {
            lightboxNext.addEventListener("click", () => showNext(1));
        }

        lightboxOverlay.addEventListener("click", (e) => {
            if (e.target === lightboxOverlay) {
                closeLightbox();
            }
        });

        document.addEventListener("keydown", (e) => {
            if (!lightboxOverlay.classList.contains("open")) return;
            if (e.key === "Escape") closeLightbox();
            if (e.key === "ArrowRight") showNext(1);
            if (e.key === "ArrowLeft") showNext(-1);
        });
    }
});
