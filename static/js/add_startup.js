function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = (textarea.scrollHeight) + 'px';
}

function CheckForm() {
    const name = document.getElementById('name').value.trim();
    const description = document.getElementById('description').value.trim();
    const image = document.getElementById('image').value;
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = !(name && description && image);
}

function previewImage() {
    const imageInput = document.getElementById('image');
    const preview = document.getElementById('imagePreview');

    const file = imageInput.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = "block";
        };
        reader.readAsDataURL(file);
    } else {
        preview.style.display = "none";
    }
}
