function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.startsWith(name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

async function respondRequest(requestId, action) {
  try {
    const response = await fetch(`/friend-request/respond/${requestId}/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: `action=${action}`,
    });

    const data = await response.json();
    if (data.status === "accepted" || data.status === "declined") {
      const element = document.getElementById(`friend-request-${requestId}`);
      if (element) {
        element.remove(); // Removes the friend request box from the DOM
      }
    }
  } catch (error) {
    console.error("Error responding to friend request:", error);
  }
}
// DOM CONTENT LOADED HANDLER
document.addEventListener("DOMContentLoaded", () => {
  feather.replace();

  // Modal handling
  const modals = {
    report: {
      element: document.getElementById("reportModal"),
      openBtn: document.getElementById("reportBtn"),
      closeBtn: document.getElementById("closeReportModal"),
    },
    cover: {
      element: document.getElementById("coverModal"),
      openBtn: document.getElementById("changeCoverBtn"),
      closeBtn: document.getElementById("closeCoverModal"),
    },
    post: {
      element: document.getElementById("postModal"),
      closeBtn: document.getElementById("closePostModal"),
    },
  };

  // Setup modal open/close
  Object.values(modals).forEach((modal) => {
    if (modal.closeBtn && modal.element) {
      modal.closeBtn.addEventListener("click", () => {
        modal.element.classList.replace("open", "hidden");
      });
    }
    if (modal.openBtn) {
      modal.openBtn.addEventListener("click", () => {
        modal.element.classList.replace("hidden", "open");
      });
    }
  });

  // Report form submission
  const reportForm = document.getElementById("reportForm");
  if (reportForm) {
    reportForm.addEventListener("submit", (e) => {
      e.preventDefault();
      document.getElementById("reportSuccessMsg").classList.remove("hidden");
      setTimeout(
        () => modals.report.element.classList.replace("open", "hidden"),
        2000
      );
    });
  }

  // Sample comment data
  const sampleComments = [
    {
      id: 1,
      username: "jane_doe",
      text: "This is amazing! 😍",
      time: "2h",
    },
    {
      id: 2,
      username: "travel_buddy",
      text: "Where was this taken? Looks beautiful!",
      time: "5h",
    },
    {
      id: 3,
      username: "photo_lover",
      text: "Great composition and colors!",
      time: "1d",
    },
  ];

  // Function to open post modal
  function openPostModal(postId, postData) {
    // Set post data in modal
    document.getElementById("modalPostImage").src = postData.imageUrl;
    document.getElementById("modalPostUserImg").src = postData.userImg;
    document.getElementById("modalPostUsername").textContent =
      postData.username;
    document.getElementById("modalPostUsername2").textContent =
      postData.username;
    document.getElementById("modalPostCaption").textContent = postData.caption;
    document.getElementById("modalPostLikes").textContent = postData.likes;
    document.getElementById(
      "modalPostCommentsCount"
    ).textContent = `${postData.comments} comments`;
    document.getElementById("likeCount").textContent = postData.likes;
    document.getElementById("commentCount").textContent = postData.comments;
    document.getElementById("bookmarkCount").textContent = postData.bookmarks;
    document.getElementById("modalPostDate").textContent = postData.date;

    // Populate comments
    const commentsContainer = document.getElementById("modalPostComments");
    commentsContainer.innerHTML = "";

    sampleComments.forEach((comment) => {
      const commentEl = document.createElement("div");
      commentEl.className = "comment-item";
      commentEl.innerHTML = `
              <div class="flex items-start">
                <div class="flex-1">
                  <span class="username">${comment.username}</span>
                  <p class="text">${comment.text}</p>
                  <p class="time">${comment.time}</p>
                </div>
                <button class="text-gray-400 hover:text-red-500">
                  <i data-feather="heart" class="w-4 h-4"></i>
                </button>
              </div>
            `;
      commentsContainer.appendChild(commentEl);
    });

    // Open modal
    modals.post.element.classList.replace("hidden", "open");

    // Refresh Feather icons
    setTimeout(() => feather.replace(), 100);
  }

  // Add event listeners to post items
  document.querySelectorAll(".feed-item").forEach((item) => {
    item.addEventListener("click", function () {
      if (this.classList.contains("pointer-events-none")) return;

      const postId = this.dataset.postId;

      // Get the post elements
      const img = this.querySelector("img");
      const caption = this.querySelector("p");
      const counts = this.querySelectorAll(".flex.items-center.space-x-1 span");

      // Format the created_at date
      const date = new Date();
      const formattedDate = date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      });

      // Get post data from the item
      const postData = {
        imageUrl: img.src,
        userImg:
          "{% if user.profile.profileimg %}{{ user.profile.profileimg.url }}{% else %}{% static 'blank_profile_picture.png' %}{% endif %}",
        username: "{{ user.username }}",
        caption: caption.textContent.trim(),
        likes: counts[0].textContent,
        comments: counts[1].textContent,
        bookmarks: counts[2].textContent,
        date: `Posted on ${formattedDate}`,
      };

      openPostModal(postId, postData);
    });
  });

  // Updated JavaScript function
  document.querySelectorAll("[data-friend-action]").forEach((button) => {
    button.addEventListener("click", function () {
      const action = this.dataset.friendAction;
      const userId = this.dataset.userId;

      if (action === "send") sendFriendRequest(userId);
      if (action === "cancel") cancelRequest(userId);
      if (action === "unfriend") unfriend(userId);
    });
  });
});
async function respondRequest(requestId, action) {
  try {
    const response = await fetch(`/friend-request/respond/${requestId}/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: `action=${action}`,
    });

    const data = await response.json();
    if (data.status === "accepted" || data.status === "declined") {
      // Remove the friend request from the DOM
      const element = document.getElementById(`friend-request-${requestId}`);
      if (element) {
        element.remove();
      }
    }
  } catch (error) {
    console.error("Error responding to friend request:", error);
  }
}
