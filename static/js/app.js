// static/js/app.js
document.addEventListener('DOMContentLoaded', () => {
  const fileInput = document.getElementById('fileInput');
  const btnProcess = document.getElementById('btnProcess');
  const uploadedPreview = document.getElementById('uploadedPreview');
  const processedCanvas = document.getElementById('processedCanvas');
  const thumbnails = document.getElementById('thumbnails');
  const btnCropAdd = document.getElementById('btnCropAdd');
  const btnClearThumbnails = document.getElementById('btnClearThumbnails');
  const a4canvas = document.getElementById('a4canvas');
  const btnDownloadA4 = document.getElementById('btnDownloadA4');
  const btnSaveGlyphs = document.getElementById('btnSaveGlyphs');
  const stepInfo = document.getElementById('stepInfo');

  let uploadedImage = null;
  let cropper = null;
  let processedDataUrl = null;
  const gridOrder = [
   'alef','gimel','dalet','bet','he','vav','zayin','het',
   'kaf','lamed','tet','yod','nun','ayin','mem','samekh',
   'tsadi','resh','pe','qof','shin','tav','final_kaf','final_mem',
   'final_nun','final_pe','final_tsadi'
  ];

  // build A4 grid layout on canvas: A4 @ 300dpi -> 2480 x 3508
  const ctx = a4canvas.getContext('2d');
  function drawA4Grid() {
    // white background
    ctx.fillStyle = '#fff';
    ctx.fillRect(0,0,a4canvas.width,a4canvas.height);

    // decide grid: use 7 rows x 4 cols (28 cells) and only first 27 used in order
    const rows = 7, cols = 4;
    const margin = 120; // px margin around page (approx 10mm at 300dpi)
    const usableW = a4canvas.width - margin*2;
    const usableH = a4canvas.height - margin*2;
    const cellW = Math.floor(usableW / cols);
    const cellH = Math.floor(usableH / rows);

    // store cells positions globally
    window.A4_CELLS = [];
    let idx = 0;
    ctx.strokeStyle = '#888';
    ctx.lineWidth = 2;
    ctx.font = "22px Arial";
    ctx.fillStyle = '#333';

    for (let r=0;r<rows;r++){
      for (let c=0;c<cols;c++){
        const x = margin + c*cellW;
        const y = margin + r*cellH;
        ctx.strokeRect(x, y, cellW, cellH);
        if (idx < gridOrder.length) {
          ctx.fillText(gridOrder[idx], x+8, y+28);
        }
        window.A4_CELLS.push({x,y,w:cellW,h:cellH, index: idx});
        idx++;
      }
    }
  }
  drawA4Grid();

  // helper to redraw A4 plus placed glyph thumbnails
  window.PLACED = {}; // index -> {img, sx, sy, sW, sH}
  function redrawA4(){
    drawA4Grid();
    for (const key in window.PLACED){
      const p = window.PLACED[key];
      // draw centered inside cell
      const cell = window.A4_CELLS[key];
      if (!cell) continue;
      const maxW = cell.w - 20;
      const maxH = cell.h - 20;
      // scale to fit
      const ratio = Math.min(maxW / p.img.width, maxH / p.img.height, 1);
      const w = Math.round(p.img.width * ratio);
      const h = Math.round(p.img.height * ratio);
      const dx = cell.x + Math.round((cell.w - w)/2);
      const dy = cell.y + Math.round((cell.h - h)/2);
      ctx.drawImage(p.img, dx, dy, w, h);
      // border
      ctx.strokeStyle = '#2a9d8f';
      ctx.lineWidth = 3;
      ctx.strokeRect(cell.x+2, cell.y+2, cell.w-4, cell.h-4);
    }
  }

  // upload handler
  fileInput.addEventListener('change', (ev) => {
    const f = ev.target.files[0];
    if (!f) return;
    const reader = new FileReader();
    reader.onload = () => {
      uploadedPreview.src = reader.result;
      uploadedPreview.style.display = 'block';
      // enable process
      btnProcess.disabled = false;
      uploadedImage = reader.result;
    };
    reader.readAsDataURL(f);
  });

  // send to server for BW processing
  btnProcess.addEventListener('click', async () => {
    if (!uploadedImage) return alert("בחר תמונה קודם");
    stepInfo.innerText = "מעבד תמונה לשחור-לבן...";
    btnProcess.disabled = true;
    // convert dataURL to blob
    const blob = await (await fetch(uploadedImage)).blob();
    const form = new FormData();
    form.append('file', blob, 'upload.png');
    const res = await fetch('/upload', { method:'POST', body: form });
    const json = await res.json();
    if (json.error) {
      alert("שגיאה: "+json.error);
      stepInfo.innerText = "";
      return;
    }
    processedDataUrl = json.processed_b64;
    // show processed in canvas
    const img = new Image();
    img.onload = () => {
      processedCanvas.width = img.width;
      processedCanvas.height = img.height;
      processedCanvas.style.display = 'block';
      const pctx = processedCanvas.getContext('2d');
      pctx.drawImage(img,0,0);
      // enable cropper
      if (cropper) cropper.destroy();
      cropper = new Cropper(processedCanvas, {
        viewMode: 1,
        dragMode: 'move',
        background: false,
        autoCropArea: 0.15,
        movable: true,
        zoomable: true,
        rotatable: true,
        scalable: true
      });
      btnCropAdd.disabled = false;
      stepInfo.innerText = "עכשיו חותכים: בחר אזור סביב האות ולחץ 'חתוך והוסף'.";
    };
    img.src = processedDataUrl;
  });

  // add crop result to thumbnails
  btnCropAdd.addEventListener('click', () => {
    if (!cropper) return;
    const canvas = cropper.getCroppedCanvas({ fillColor: '#ffffff' });
    if (!canvas) return;
    const dataUrl = canvas.toDataURL('image/png');
    const div = document.createElement('div');
    div.className = 'thumb';
    const img = document.createElement('img');
    img.src = dataUrl;
    div.appendChild(img);
    const lbl = document.createElement('div');
    lbl.className = 'label';
    lbl.innerText = thumbnails.children.length+1;
    div.appendChild(lbl);
    thumbnails.appendChild(div);

    // make draggable: when clicked, prompt which cell to place into (guided)
    div.addEventListener('click', () => {
      // ask user which letter (index) to map to:
      let idxStr = prompt("הכנס מספר משבצת (1..27) או הרשם שם אות (alef, bet, ...). אחרת בחר אוטומטית אחרון ריק:");
      let index = null;
      if (idxStr) {
        const n = parseInt(idxStr);
        if (!isNaN(n) && n>=1 && n<=27) index = n-1;
        else {
          const nameIndex = gridOrder.indexOf(idxStr);
          if (nameIndex>=0) index = nameIndex;
        }
      }
      if (index === null) {
        // pick first empty
        for (let i=0;i<gridOrder.length;i++){
          if (!(i in window.PLACED)) { index = i; break; }
        }
      }
      if (index===undefined || index===null) { alert("לא נבחרת משבצת"); return; }
      const imgObj = new Image();
      imgObj.onload = () => {
        window.PLACED[index] = { img: imgObj };
        redrawA4();
      };
      imgObj.src = dataUrl;
    });

    // enable save
  });

  btnClearThumbnails.addEventListener('click', () => thumbnails.innerHTML = "");

  // download A4 PNG
  btnDownloadA4.addEventListener('click', () => {
    const dataUrl = a4canvas.toDataURL('image/png');
    const a = document.createElement('a');
    a.href = dataUrl;
    a.download = 'a4_page.png';
    a.click();
  });

  // Save glyphs to server: iterate PLACED and send each as base64 crop
  btnSaveGlyphs.addEventListener('click', async () => {
    // ensure at least something placed
    const keys = Object.keys(window.PLACED).map(k=>parseInt(k)).sort((a,b)=>a-b);
    if (keys.length === 0) { alert("אין חיתוכים במערכת. חתוך והצב משבצות."); return; }
    stepInfo.innerText = "שומר חיתוכים בשרת...";
    for (const k of keys){
      const cell = window.A4_CELLS[k];
      const placed = window.PLACED[k];
      // re-render placed image as exact PNG with cell size
      const tmpCanvas = document.createElement('canvas');
      tmpCanvas.width = cell.w; tmpCanvas.height = cell.h;
      const tctx = tmpCanvas.getContext('2d');
      tctx.fillStyle = '#fff'; tctx.fillRect(0,0,tmpCanvas.width,tmpCanvas.height);
      // draw centered
      const ratio = Math.min((cell.w-20)/placed.img.width, (cell.h-20)/placed.img.height, 1);
      const w = Math.round(placed.img.width * ratio);
      const h = Math.round(placed.img.height * ratio);
      const dx = Math.round((cell.w - w)/2);
      const dy = Math.round((cell.h - h)/2);
      tctx.drawImage(placed.img, dx, dy, w, h);
      const dataUrl = tmpCanvas.toDataURL('image/png');
      // send to server with name GRID_ORDER[k]
      await fetch('/save_crop', {
        method:'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ name: gridOrder[k], index: k, imageData: dataUrl })
      });
    }
    stepInfo.innerText = "החיתוכים נשמרו בשרת.";
    // enable finalize if generate_ttf present
    document.getElementById('btnFinalize').disabled = false;
  });

  // finalize button: call /finalize to create TTF (server must have generate_ttf)
  document.getElementById('btnFinalize').addEventListener('click', async () => {
    stepInfo.innerText = "יוצר פונט בשרת...";
    const res = await fetch('/finalize', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ output_ttf: 'user_font.ttf' })});
    const json = await res.json();
    if (json.error) {
      stepInfo.innerText = "שגיאה ביצירת פונטים: "+json.error;
    } else {
      stepInfo.innerHTML = `פונט נוצר: ${json.ttf}. הורדת הפונט: <a href="/output/${json.ttf}" target="_blank">${json.ttf}</a>`;
    }
  });

  // small helper: allow clicking on canvas cells to remove placed glyph
  a4canvas.addEventListener('click', (ev) => {
    const rect = a4canvas.getBoundingClientRect();
    const x = Math.round((ev.clientX - rect.left) * (a4canvas.width / rect.width));
    const y = Math.round((ev.clientY - rect.top) * (a4canvas.height / rect.height));
    for (let i=0;i<window.A4_CELLS.length;i++){
      const cell = window.A4_CELLS[i];
      if (x >= cell.x && x <= cell.x+cell.w && y >= cell.y && y <= cell.y+cell.h){
        if (i in window.PLACED) {
          if (confirm("להסיר חיתוך מהמשבצת הזו?")) {
            delete window.PLACED[i];
            redrawA4();
          }
        }
      }
    }
  });
});
