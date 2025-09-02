function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.startsWith(name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

const csrftoken = getCookie("csrftoken");

function run() {
  const bibleTextBlock = document.getElementById("bible-text");

  let hoveredWord = null;

  bibleTextBlock.addEventListener("click", e => {
    if (e.target.tagName == "SPAN") {
      console.log("hovered word: ", e.target);
      hoveredWord = e.target;
      // get index of span, verse number, and specific word and send it off to the backend
      //
      fetch("/get_word_info/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrftoken
        },
        body: JSON.stringify({
          word: e.target.innerText,
          verse: e.target.parentNode.id
        })
      })
      .then (res => res.json())
      .then(data => {
        console.log("server responded", data)
      })
      .catch(err => {
        console.error("error:", err)
      })
    }
  })

}

run()
