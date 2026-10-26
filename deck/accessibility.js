// Accessibility fixes pptxgenjs cannot write itself, applied to the saved .pptx:
//  1. shapes with no text (cards, circles, dots) are marked decorative, so screen
//     readers skip them and PowerPoint does not report missing alt text;
//  2. every table gets its object name as its description and a header row.
const fs = require("fs");

function loadJSZip() {
  // jszip ships with pptxgenjs; load it from there
  return require(require.resolve("jszip", { paths: [require.resolve("pptxgenjs")] }));
}

const DECORATIVE =
  '<a:extLst><a:ext uri="{C183D7F6-B498-43B3-948B-1728B52AA6E4}">' +
  '<adec:decorative xmlns:adec="http://schemas.microsoft.com/office/drawing/2017/decorative" val="1"/>' +
  "</a:ext></a:extLst>";

function markDecorativeShapes(xml) {
  return xml.replace(/<p:sp>([\s\S]*?)<\/p:sp>/g, (shape, inner) => {
    if (/<a:t[ >]/.test(inner) || inner.includes("<p:ph")) return shape; // has text or is a placeholder
    return shape.replace(/<p:cNvPr ([^>]*?)(?:\/>|><\/p:cNvPr>)/, `<p:cNvPr $1>${DECORATIVE}</p:cNvPr>`);
  });
}

function describeTables(xml) {
  return xml.replace(/<p:graphicFrame>([\s\S]*?)<\/p:graphicFrame>/g, (frame, inner) => {
    if (!inner.includes("<a:tbl>")) return frame;
    return frame
      .replace(/<p:cNvPr id="(\d+)" name="([^"]*)"\/>/, '<p:cNvPr id="$1" name="$2" descr="$2"/>')
      .replace("<a:tblPr/>", '<a:tblPr firstRow="1" bandRow="1"/>');
  });
}

async function fixAccessibility(file) {
  const JSZip = loadJSZip();
  const zip = await JSZip.loadAsync(fs.readFileSync(file));
  const slides = Object.keys(zip.files).filter((n) => /^ppt\/slides\/slide\d+\.xml$/.test(n));
  for (const name of slides) {
    const xml = await zip.file(name).async("string");
    zip.file(name, describeTables(markDecorativeShapes(xml)));
  }
  fs.writeFileSync(file, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
}

module.exports = { fixAccessibility };
