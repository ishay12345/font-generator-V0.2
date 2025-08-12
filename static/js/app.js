// static/js/app.js
let cropper = null;
let currentIndex = 0;

// LETTERS ו־IMAGE_URL מקבלים מה־template (Jinja)
const letters = typeof LETTERS !== 'undefined' ? LETTERS : [
  'alef','bet','gimel','dalet','he','vav','zayin','het','tet',
  'yod','kaf','lamed','mem','nun','samekh','ayin','pe','tsadi',
  'qof','resh','shin','tav','final_kaf','final_mem','final_nun',
  'final_pe','final_tsadi'
];

function init() {
  document.getElementById('grid').innerHTML = '';
  for (let i = 0; i < letters.length; i++) {
    const div = document.createElement('div');
    div.className = 'cell';
    div.dataset.letter = letters[i];
    div.dataset.index = i;
    div.innerText = letters[i];
    document.getElementById('grid').appendChild(div);
  }

  const imageEl = document.getElementById('image');
  imageEl.src = IMAGE_URL;

  imageEl.onload = () => {
    if (cropper) cropper.destroy();
    cropper = new Cropper(imageEl, {
      viewMode: 1,
      autoCropArea: 0.35,
      background: false,
    });
  };

  document.getElementById('btn-save').addEventListener('click', saveCrop);
  document.getElementById('btn-next').addEventListener('click', nextLetter);
  document.getElementById('btn-list').addEventListener('click', loadGlyphs);
  document.getElementById('btn-finish').addEventListener('click', finalizeFont);

  loadGlyphs();
}

function saveCrop() {
  if (!cropper) return alert('המתן לטעינת התמונה...');
  const canvas = cropper.getCroppedCanvas({
    // אתה יכול לשנות גודל פה אם תרצה אחידות
    // width: 300, height: 300
  });
  const dataURL = canvas.toDataURL('image/png');
  const name = letters[currentIndex];
  const index = currentIndex;

  fetch('/backend/save_crop', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ name, index, data: dataURL })
  })
  .then(r => r.json())
  .then(json => {
    if (json.error) {
      alert('שגיאה בשמירה: ' + json.error);
      return;
    }
    // עדכון המשבצת והגליפים המקומיים
    const cell = document.querySelector(`.cell[data-index="${index}"]`);
    if (cell) {
      cell.innerHTML = '';
      const img = document.createElement('img');
      img.src = dataURL;
      img.style.maxWidth = '100%';
      img.style.maxHeight = '100%';
      cell.appendChild(img);
    }
    loadGlyphs();
    // עבור לאות הבאה אוטומטית
    nextLetter();
  })
  .catch(err => {
    alert('שגיאה ברשת: ' + err);
  });
}

function nextLetter() {
  currentIndex = Math.min(currentIndex + 1, letters.length - 1);
  highlightCurrent();
}

function highlightCurrent() {
  document.querySelectorAll('.cell').forEach(el => el.style.borderColor = '#ddd');
  const cur = document.querySelector(`.cell[data-index="${currentIndex}"]`);
  if (cur) cur.style.borderColor = '#3498db';
}

function loadGlyphs() {
  fetch('/api/list_glyphs').then(r => r.json()).then(json => {
    const area = document.getElementById('glyphs');
    area.innerHTML = '';
    if (json.files && json.files.length) {
      json.files.forEach(fn => {
        const c = document.createElement('div');
        c.className = 'glyph-card';
        const img = document.createElement('img');
        img.src = '/static/glyphs/' + fn;
        img.style.maxWidth = '100%'; img.style.maxHeight = '100%';
        c.appendChild(img);
        area.appendChild(c);
      });
    }
  });
}

function finalizeFont() {
  if (!confirm('לייצר פונט מהגליפים הנוכחיים?')) return;
  fetch('/api/finalize', { method:'POST', headers:{'Content-Type':'application/json'}, body: '{}' })
    .then(r => r.json())
    .then(json => {
      if (json.error) {
        alert('שגיאה ביצירת הפונט: ' + json.error);
      } else {
        alert('הפונט נוצר: ' + (json.ttf || 'an output'));
      }
    });
}

// init לאחר טעינת דף
window.addEventListener('DOMContentLoaded', () => {
  try { init(); highlightCurrent(); } catch(e) { console.error(e); }
});
