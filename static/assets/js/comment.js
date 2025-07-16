// ------------------ DOM ELEMENTS ------------------
const modalImageSlider = document.querySelector(".modal-image-slider");
const modalImageSlides = document.querySelectorAll(".modal-image-slide");
const prevSlideBtn = document.querySelector(".prev-slide");
const nextSlideBtn = document.querySelector(".next-slide");
const modalImage = document.querySelector(".modal-large-photo");
const slideDotsContainer = document.querySelector(".slide-dots");

// ------------------ GLOBAL VARIABLES ------------------
let slideIndex = 0;
const commentSockets = {}; // Global socket cache

// ------------------ MODAL FUNCTIONS ------------------
function openCommentPopup(postId) {
  const modal = document.getElementById("commentModal-" + postId);
  if (modal) {
    modal.style.display = "flex";
    document.body.style.overflow = "hidden";
    
    // Initialize slider if images exist
    initializeSlider();
    
    // Initialize WebSocket for this post if not already done
    initializeCommentSocket(postId);
  }
}

function closeCommentPopup(postId) {
  const modal = document.getElementById("commentModal-" + postId);
  if (modal) {
    modal.style.display = "none";
    document.body.style.overflow = "";
  }
}

// Close modal when clicking outside
document.addEventListener("click", function (e) {
  const modal = e.target.closest(".feed-modal");
  if (modal && e.target === modal) {
    const postId = modal.id.replace("commentModal-", "");
    closeCommentPopup(postId);
  }
});

// ------------------ SLIDER LOGIC ------------------
function initializeSlider() {
  // Re-query elements in case they've changed
  const slides = document.querySelectorAll(".modal-image-slide");
  const prevBtn = document.querySelector(".prev-slide");
  const nextBtn = document.querySelector(".next-slide");
  
  if (slides.length > 0) {
    slideIndex = 0;
    showSlide(slideIndex);
    createDots();
    
    // Add event listeners if they don't exist
    if (prevBtn && !prevBtn.hasAttribute('data-listener')) {
      prevBtn.addEventListener("click", prevSlide);
      prevBtn.setAttribute('data-listener', 'true');
    }
    if (nextBtn && !nextBtn.hasAttribute('data-listener')) {
      nextBtn.addEventListener("click", nextSlide);
      nextBtn.setAttribute('data-listener', 'true');
    }
  }
}

function showSlide(n) {
  const slides = document.querySelectorAll(".modal-image-slide");
  const slider = document.querySelector(".modal-image-slider");
  const prevBtn = document.querySelector(".prev-slide");
  const nextBtn = document.querySelector(".next-slide");
  
  if (!slides.length || !slider) return;
  
  slideIndex = n;
  
  if (slideIndex < 0) slideIndex = 0;
  if (slideIndex >= slides.length) slideIndex = slides.length - 1;
  
  slider.style.transform = `translateX(-${slideIndex * 100}%)`;
  
  if (prevBtn) prevBtn.disabled = slideIndex === 0;
  if (nextBtn) nextBtn.disabled = slideIndex === slides.length - 1;
  
  updateDots();
}

function nextSlide() {
  const slides = document.querySelectorAll(".modal-image-slide");
  if (slideIndex < slides.length - 1) {
    slideIndex++;
    showSlide(slideIndex);
  }
}

function prevSlide() {
  if (slideIndex > 0) {
    slideIndex--;
    showSlide(slideIndex);
  }
}

function createDots() {
  const slides = document.querySelectorAll(".modal-image-slide");
  const dotsContainer = document.querySelector(".slide-dots");
  
  if (!dotsContainer || !slides.length) return;
  
  dotsContainer.innerHTML = "";
  slides.forEach((_, index) => {
    const dot = document.createElement("div");
    dot.classList.add("slide-dot");
    dot.addEventListener("click", () => showSlide(index));
    dotsContainer.appendChild(dot);
  });
  updateDots();
}

function updateDots() {
  const dots = document.querySelectorAll(".slide-dot");
  dots.forEach((dot, index) => {
    dot.classList.toggle("active", index === slideIndex);
  });
}

// ------------------ WEBSOCKET COMMENT SYSTEM ------------------
function initializeCommentSocket(postId) {
  // Avoid duplicate WebSocket connections
  if (commentSockets[postId]) {
    return commentSockets[postId];
  }
  
  const socket = new WebSocket(`ws://${window.location.host}/ws/comments/${postId}/`);
  
  socket.onmessage = function (e) {
    const data = JSON.parse(e.data);
    addCommentToUI(postId, data);
  };
  
  socket.onopen = function() {
    console.log(`WebSocket connected for post ${postId}`);
  };
  
  socket.onclose = function() {
    console.log(`WebSocket closed for post ${postId}`);
    // Remove from cache when closed
    delete commentSockets[postId];
  };
  
  socket.onerror = function(error) {
    console.error(`WebSocket error for post ${postId}:`, error);
  };
  
  commentSockets[postId] = socket;
  return socket;
}

function addCommentToUI(postId, data) {
  const commentSection = document.querySelector(`#commentModal-${postId} .modal-all-comments`);
  if (!commentSection) return;
  
  // Hide "no comments" message
  const noCommentsMsg = commentSection.querySelector(".no-comments-msg");
  if (noCommentsMsg) noCommentsMsg.style.display = "none";
  
  // Create new comment element
  const newComment = document.createElement("div");
  newComment.classList.add("modal-comment");
  newComment.innerHTML = `
    <div class="modal-comment-avatar">
      <img src="${data.profile_img}" alt="${data.username}" />
    </div>
    <div class="modal-comment-body">
      <p class="modal-comment-author">${data.username}</p>
      <p class="modal-comment-text">${data.text}</p>
    </div>
  `;
  
  commentSection.appendChild(newComment);
  commentSection.scrollTop = commentSection.scrollHeight;
}

// ------------------ COMMENT FORM SUBMISSION ------------------
function initializeCommentForms() {
  document.querySelectorAll(".comment-form").forEach((form) => {
    // Skip if already initialized
    if (form.hasAttribute('data-initialized')) return;
    
    const postId = form.dataset.postId;
    
    form.addEventListener("submit", async function (e) {
      e.preventDefault();
      await handleCommentSubmission(this, postId);
    });
    
    form.setAttribute('data-initialized', 'true');
  });
}

async function handleCommentSubmission(form, postId) {
  const submitBtn = form.querySelector('button[type="submit"]');
  const textInput = form.querySelector('input[name="comment_text"]');
  const commentText = textInput.value.trim();
  const csrfToken = form.querySelector('input[name="csrfmiddlewaretoken"]').value;
  
  const btnText = submitBtn.querySelector(".btn-text");
  const btnSpinner = submitBtn.querySelector(".btn-spinner");
  
  if (!commentText) return;
  
  // Show loading state
  setButtonLoadingState(submitBtn, btnText, btnSpinner, true);
  
  try {
    const response = await fetch(form.action, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfToken,
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({ comment_text: commentText }),
    });
    
    if (response.ok) {
      // Send via WebSocket if connection is open
      const socket = commentSockets[postId];
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ text: commentText }));
      }
      textInput.value = "";
    } else {
      showErrorMessage("Something went wrong when posting your comment.");
    }
  } catch (error) {
    showErrorMessage("Failed to connect to server.");
    console.error("Comment submission error:", error);
  } finally {
    // Restore button state
    setButtonLoadingState(submitBtn, btnText, btnSpinner, false);
  }
}

function setButtonLoadingState(button, textSpan, spinnerSpan, isLoading) {
  button.disabled = isLoading;
  textSpan.style.display = isLoading ? "none" : "inline";
  spinnerSpan.style.display = isLoading ? "inline" : "none";
}

function showErrorMessage(message) {
  alert(message); // You can replace this with a better notification system
}

// ------------------ INITIALIZATION ------------------
document.addEventListener("DOMContentLoaded", function () {
  initializeCommentForms();
});

// ------------------ CLEANUP ------------------
// Close WebSocket connections when page is unloaded
window.addEventListener('beforeunload', function() {
  Object.values(commentSockets).forEach(socket => {
    if (socket.readyState === WebSocket.OPEN) {
      socket.close();
    }
  });
});

// ------------------ BOOKMARK FUNCTIONALITY ------------------
function toggleBookmark(postId, elem) {
  fetch(window.bookmarkUrl || "{% url 'toggle_bookmark' %}", {
    method: "POST",
    headers: {
      "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: `post_id=${postId}`,
  })
    .then((response) => response.json())
    .then((data) => {
      const icon = elem.querySelector("i");
      icon.classList.add("animate");
      
      if (data.status === "added") {
        icon.classList.add("bookmarked");
      } else {
        icon.classList.remove("bookmarked");
      }
      
      // Remove animation after short delay
      setTimeout(() => icon.classList.remove("animate"), 200);
    })
    .catch((error) => {
      console.error("Bookmark toggle error:", error);
      showErrorMessage("Failed to update bookmark.");
    });
}