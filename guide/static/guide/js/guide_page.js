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

function getWordInfo(verse, strongNum) {
  let verseInfo = chapterInfo[verse];
  for (var wordInfo of verseInfo) {
    if (strongNum == wordInfo["strong_num"]) {
      return wordInfo
    }
  }
}

function run() {
  const bibleTextBlock = document.getElementById("bible-text");
  const debugTextBlock = document.getElementById("debug-strong-info");
  console.log(chapterInfo);

  let hoveredWord = null;

  bibleTextBlock.addEventListener("click", e => {
    if (e.target.tagName == "SPAN") {
      //console.log("hovered word: ", e.target);
      hoveredWord = e.target;
      
      let strongNum = e.target.getAttribute("strongnum");
      let verse = e.target.parentNode.id.replace("verse", "");
      //console.log(strongNum, verse);
      let wordInfo = getWordInfo(verse, strongNum);
      console.log(wordInfo);

      let debugInfo = `English: ${wordInfo.english} | Greek: ${wordInfo.original_language} | Strong Number: ${wordInfo.strong_num} | Strong Text: ${wordInfo.strong_text}`
      debugTextBlock.innerHTML = debugInfo;
    }
  })
}

let chapterInfo = null;

fetch("/get_chapter_info/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrftoken
    },
    body: JSON.stringify({
      book: BOOKNAME,
      chapter: CHAPTERNUMBER
    })
  })
  .then (res => res.json())
  .then(data => {
    chapterInfo = data;
    run()
  })
  .catch(err => {
    console.error("error:", err)
  })


