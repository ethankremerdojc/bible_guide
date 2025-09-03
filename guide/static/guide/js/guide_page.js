function getWordInfo(verse, strongNum) {
  let verseInfo = chapterInfo[verse];
  for (var wordInfo of verseInfo) {
    if (strongNum == wordInfo["strong_num"]) {
      return wordInfo
    }
  }
}

function setBibleVersion(version) {
  localStorage.setItem("bibleversion", version)
}

function getBibleVersion() {
  let version = localStorage.getItem("bibleversion");
  if (!version) {
    version = "ESV"
  }

  return version
}

function collectChapterInfo() {
  fetch("/get_chapter_info/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": CSRFTOKEN
      },
      body: JSON.stringify({
        book: BOOKNAME,
        chapter: CHAPTERNUMBER,
        version: getBibleVersion()
      })
    })
    .then (res => res.json())
    .then(data => {
      chapterInfo = data.chapterInfo;
      chapterText = data.chapterText;
      run()
    })
    .catch(err => {
      console.error("error:", err)
    })
}

function populateBookAndChapter() {
  // uses global BIBLEBOOKS
  
  let activeCount = null;
  let activeBook = null;
  let bookSelector = document.getElementById("book");
  bookSelector.innerHTML = '';

  for (var [bookName, chapterCount] of BIBLEBOOKS) {
    let option = document.createElement("option");
    option.value = bookName;
    option.innerHTML = bookName;
    bookSelector.appendChild(option);

    if (bookName.toLowerCase() == BOOKNAME.toLowerCase()) {
      activeCount = chapterCount;
      activeBook = bookName;
    }
  }

  bookSelector.value = activeBook;

  let chapterSelector = document.getElementById("chapter");
  chapterSelector.innerHTML = '';

  for (let i = 0; i < activeCount; i++) {
    let option = document.createElement("option");
    let num = i + 1;
    option.value = num;
    option.innerHTML = num;
    chapterSelector.appendChild(option);
  }

  chapterSelector.value = CHAPTERNUMBER;
}

// -----------------------------
// START 
// -----------------------------

function run() {
  const bibleTextBlock = document.getElementById("bible-text");
  bibleTextBlock.innerHTML = chapterText;

  bibleTextBlock.addEventListener("click", e => {
    if (e.target.tagName == "SPAN") {
      const debugText = document.getElementById("debug-content");

      debugTextBlock.style.display = "block";
      let strongNum = e.target.getAttribute("strongnum");
      let verse = e.target.parentNode.id.replace("verse", "");
      let wordInfo = getWordInfo(verse, strongNum);

      let debugInfo = `English: ${wordInfo.english} | Greek: ${wordInfo.original_language} | Strong Number: ${wordInfo.strong_num} | Strong Text: ${wordInfo.strong_text}`
      debugText.innerHTML = debugInfo;
    }
  })
}

let chapterInfo = null;
let chapterText = null;

const versionSelector = document.getElementById("bibleversions");
console.log(getBibleVersion());
versionSelector.value = getBibleVersion();
versionSelector.addEventListener("change", e => {
  setBibleVersion(e.target.value);
  collectChapterInfo();
})

populateBookAndChapter();

const bookSelector = document.getElementById("book");
bookSelector.addEventListener("change", e => {
  BOOKNAME = e.target.value;
  CHAPTERNUMBER = 1;
  populateBookAndChapter();
})

collectChapterInfo();

const goButton = document.getElementById("gobutton");
goButton.onclick = () => {

  let bookSelector = document.getElementById("book");
  let chapterSelector = document.getElementById("chapter");

  let selectedBook = bookSelector.value;
  let selectedChapter = chapterSelector.value;

  let newPathname = `/guide/${selectedBook.toLowerCase()}/${selectedChapter}/`;
  window.location.pathname = newPathname;
}

const closeInfoButton = document.getElementById("close");
closeInfoButton.onclick = () => {
  debugTextBlock.style.display = "none";
}

const debugTextBlock = document.getElementById("debug-strong-info");
debugTextBlock.style.display = "none";

