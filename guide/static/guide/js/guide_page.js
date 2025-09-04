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
      console.log(data);
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
    CURRENTBOOKCHAPTERCOUNT = num;
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

      let debugInfo = `
        <div>English: <b>${wordInfo.english}</b></div><div><span>Original Language: </span><span class="originallanguage">${wordInfo.original_language}</span><span class="strongnum"><a href="https://biblehub.com/${wordInfo.language_type}/${wordInfo.strong_num}.htm" target="_blank">(${wordInfo.strong_num})</a></span></div><div class="strongtext">${wordInfo.strong_text}</div>`
      debugText.innerHTML = debugInfo;
    }
  })
}
let CURRENTBOOKCHAPTERCOUNT = null;
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

const prevButton = document.getElementById("previouschapter");
const nextButton = document.getElementById("nextchapter");

if (CHAPTERNUMBER == 1) {
  prevButton.style.display = "none";
}

if (CURRENTBOOKCHAPTERCOUNT == CHAPTERNUMBER) {
  nextButton.style.display = "none";
}

nextButton.onclick = () => {
  let newPathname = `/guide/${BOOKNAME}/${Number(CHAPTERNUMBER) + 1}/`;
  window.location.pathname = newPathname;
}

prevButton.onclick = () => {
  let newPathname = `/guide/${BOOKNAME}/${Number(CHAPTERNUMBER) - 1}/`;
  window.location.pathname = newPathname;
}
 
const closeInfoButton = document.getElementById("close");
closeInfoButton.onclick = () => {
  debugTextBlock.style.display = "none";
}

const debugTextBlock = document.getElementById("debug-strong-info");
debugTextBlock.style.display = "none";

