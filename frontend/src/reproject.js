export const MERCATOR_LAT_LIMIT = 85.0511287798;

function pixels(bitmap) {
  const canvas = document.createElement('canvas');
  canvas.width = bitmap.width;
  canvas.height = bitmap.height;
  const context = canvas.getContext('2d', { willReadFrequently: true });
  context.drawImage(bitmap, 0, 0);
  return context.getImageData(0, 0, bitmap.width, bitmap.height);
}

export function reprojectToMercator(bitmap, size) {
  const src = pixels(bitmap);
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const context = canvas.getContext('2d');
  const out = context.createImageData(size, size);

  for (let row = 0; row < size; row++) {
    const lat = Math.atan(Math.sinh(Math.PI * (1 - (2 * (row + 0.5)) / size)));
    const srcRow = Math.min(src.height - 1, Math.floor(((Math.PI / 2 - lat) / Math.PI) * src.height));
    for (let col = 0; col < size; col++) {
      const srcCol = Math.floor((col / size) * src.width);
      const from = (srcRow * src.width + srcCol) * 4;
      const to = (row * size + col) * 4;
      for (let k = 0; k < 4; k++) out.data[to + k] = src.data[from + k];
    }
  }

  context.putImageData(out, 0, 0);
  return canvas;
}
