// Toast container
const toastContainer = document.createElement("div");
toastContainer.style.position = "fixed";
toastContainer.style.top = "10px";
toastContainer.style.right = "10px";
toastContainer.style.zIndex = "1050";
toastContainer.style.display = "flex";
toastContainer.style.flexDirection = "column";
toastContainer.style.gap = "10px"; // Space between toasts
document.body.appendChild(toastContainer);

function showToast(type, title, message, img = null, timeAgo = "Just now") {
    const toast = document.createElement("div");
    toast.className = "toast show";
    toast.style.minWidth = "250px";

    let headerContent = '';

    if (type === "direct") {
        headerContent = `
            <img src="${img}" class="rounded me-2 avatar-xs" alt="Profile">
            <strong class="me-auto">${title}</strong>
            <small>${timeAgo}</small>
        `;
    } else {
        let color = type === "success" ? "green" : type === "error" ? "red" : "blue";
        headerContent = `
            <span class="me-2" style="width:10px; height:10px; background-color:${color}; border-radius:50%; display:inline-block;"></span>
            <strong class="me-auto">${title}</strong>
        `;
    }

    // Toast HTML
    toast.innerHTML = `
        <div class="toast-header">
            ${headerContent}
            <button type="button" class="ms-2 mb-1 btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;

    // Apply animation class
    toast.classList.add("toast-animation");

    // Append to toast container
    toastContainer.appendChild(toast);

    // Initialize Bootstrap Toast
    const toastBootstrap = new bootstrap.Toast(toast);
    toastBootstrap.show();

    // Remove toast after delay with fade-out effect
    setTimeout(() => {
        toast.classList.add("fade-out");
        setTimeout(() => toast.remove(), 500); // Wait for animation to complete
    }, 5000); // Show for 5s before starting fade-out
}

function removeMedia(action) {
    fetch('', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            "X-Requested-With": "XMLHttpRequest",
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ action: action })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (action === 'remove_avatar') {
                document.getElementById('avatar').src = '/static/images/avatar.jpg'; // Clear avatar image
                showToast("success", "Success!", "Your avatar picture has been successfully removed.");
            } else if (action === 'remove_profile_cover') {
                document.getElementById('profile-cover').style.backgroundImage = '/static/images/profile-cover.jpg'; // Clear profile cover
                showToast("success", "Success!", "Your profile cover has been successfully removed.");
            }
        } else {
            showToast("error", "Error!", data.reason);
        }
    });
}

// Function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.querySelectorAll(".specific-file-input").forEach(input => {
    input.addEventListener("change", function () {
        if (this.files.length > 0) {
            let file = this.files[0];
            let fileName = file.name;
            showToast("success", "File " + fileName +" Selected!", "Don't forget to click 'Save Cahnges' to upload.");
        }
    });
});
