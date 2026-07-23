const preview = document.getElementById("avatarPreview");
const input = document.getElementById("avatarInput");

preview.addEventListener("click", () => {input.click();});

input.addEventListener("change", () => {
    const file = input.files[0];
    if (file) {
        preview.src = URL.createObjectURL(file);
    }
});
