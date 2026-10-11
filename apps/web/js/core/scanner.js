// Barcode reading. Uses the live camera where the browser allows it, otherwise a photo of the barcode.
// Decoders: the browser's built-in BarcodeDetector when present, else ZXing (loaded in index.html).
const FORMATS = ['ean_13', 'ean_8', 'upc_a', 'upc_e', 'code_128'];

function nativeDetector() {
  try { return 'BarcodeDetector' in window ? new window.BarcodeDetector({ formats: FORMATS }) : null; } catch { return null; }
}

function zxingReader() {
  const Z = window.ZXing;
  if (!Z) return null;
  const hints = new Map();
  hints.set(Z.DecodeHintType.POSSIBLE_FORMATS, [Z.BarcodeFormat.EAN_13, Z.BarcodeFormat.EAN_8, Z.BarcodeFormat.UPC_A, Z.BarcodeFormat.UPC_E, Z.BarcodeFormat.CODE_128]);
  hints.set(Z.DecodeHintType.TRY_HARDER, true);
  return new Z.BrowserMultiFormatReader(hints);
}

// Shrink large phone photos so decoding is quick and reliable.
async function toScaledImage(file, maxSide = 1400) {
  const bmp = await createImageBitmap(file);
  const s = Math.min(1, maxSide / Math.max(bmp.width, bmp.height));
  const c = document.createElement('canvas');
  c.width = Math.round(bmp.width * s); c.height = Math.round(bmp.height * s);
  c.getContext('2d').drawImage(bmp, 0, 0, c.width, c.height);
  return c;
}

export async function decodePhoto(file) {
  const canvas = await toScaledImage(file);
  const det = nativeDetector();
  if (det) { try { const r = await det.detect(canvas); if (r[0]) return r[0].rawValue; } catch {} }
  const reader = zxingReader();
  if (!reader) throw new Error('Barcode reader did not load. Type the number instead.');
  try { return (await reader.decodeFromImageUrl(canvas.toDataURL('image/jpeg', 0.92))).getText(); }
  catch { throw new Error('No barcode found in that photo. Try again closer, with the barcode flat and in focus.'); }
}

// Live camera. Resolves false when the camera is not available here (caller then offers photo mode).
export async function startLive(videoEl, onCode) {
  if (!navigator.mediaDevices?.getUserMedia) return false;
  const reader = zxingReader();
  if (!reader) return false;
  try {
    let last = '';
    const controls = await reader.decodeFromConstraints({ video: { facingMode: 'environment' } }, videoEl, (res) => {
      if (res && res.getText() !== last) { last = res.getText(); onCode(last); setTimeout(() => { last = ''; }, 2500); }
    });
    return { stop: () => { try { controls?.stop?.(); reader.reset(); } catch {} } };
  } catch { try { reader.reset(); } catch {} return false; }
}
