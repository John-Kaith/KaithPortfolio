document.addEventListener("DOMContentLoaded", function () {
    const typing = document.querySelector(".typing");
    const words = ["Full Stack Developer", "Web Designer", "Freelancer",];
    let wordIndex = 0;
    let letterIndex = 0;
    let isDeleting = false;
    let speed = 100; // Typing speed

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
});
