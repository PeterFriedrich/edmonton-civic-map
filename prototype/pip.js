// CLI for the build's cross-check (src/build_address_index.py) and check_pip.py:
//   node pip.js <layer.geojson> [--dist] < "lon,lat\n..." > "hits[;dist]\n..."
// The lookup itself is the site's own site/src/pip.js, so the build checks the
// code the browser runs.
'use strict';
const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');

import(pathToFileURL(path.join(__dirname, '..', 'site', 'src', 'pip.js')).href).then(({ locate, distanceToBoundary }) => {
  const fc = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const withDist = process.argv[3] === '--dist';
  const out = [];
  for (const line of fs.readFileSync(0, 'utf8').split('\n')) {
    if (!line) continue;
    const [lon, lat] = line.split(',').map(Number);
    const hits = locate(lon, lat, fc).join('|');
    out.push(withDist ? hits + ';' + distanceToBoundary(lon, lat, fc).toFixed(1) : hits);
  }
  process.stdout.write(out.join('\n') + '\n');
});
