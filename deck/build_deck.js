// Builds MMM_presentation.pptx from deck_data.json (exported by src/08_deck_data.py).
// Run from the deck folder:  node build_deck.js
const path = require("path");
const pptxgen = require("pptxgenjs");
const D = require("./deck_data.json");


const THEME = {
  name: "Water and Sun",
  headFontFace: "Calibri",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "13262F", lt1: "FFFFFF", dk2: "0B3C49", lt2: "EEF6F7",
    accent1: "1B7F8C", accent2: "F2A541", accent3: "E4572E", accent4: "7FB7BE",
    accent5: "9AA9AD", accent6: "3D5A80", hlink: "1B7F8C", folHlink: "3D5A80",
  },
};
const HEX = THEME.colors;
const MUTED_HEX = "5B6B70";
const GRID_HEX = "E1E8E9";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Bottled water marketing mix model";
pres.author = "Yazan Alrefaai";
const C = pres.SchemeColor;

// ------------------------------------------------------------------ helpers
const pct = (v, d = 1) => `${v >= 0 ? "+" : "−"}${Math.abs(v * 100).toFixed(d)}%`;
const gbp = (v, d = 2) => `£${v.toFixed(d)}`;
const fixed = (v, d) => {
  const t = Number(v).toFixed(d);
  return /^-0\.?0*$/.test(t) ? t.slice(1) : t;
};
const gbpK = (v) => `£${Math.round(v / 1000).toLocaleString("en-GB")}k`;
const media = Object.fromEntries(D.media.map((m) => [m.channel, m]));
const share = D.share;
const mediaShare = ["TV", "Online video", "Online partnership", "OOH"].reduce((s, k) => s + share[k], 0);
const scenOP = D.scenarios["Online partnership"];

const chartText = { fontFace: "+mn-lt" };
const axisStyle = {
  catAxisLabelColor: MUTED_HEX, valAxisLabelColor: MUTED_HEX,
  catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
  catAxisLabelFontSize: 11, valAxisLabelFontSize: 11,
  catAxisLineShow: true, catAxisLineColor: "C9D3D5",
  valAxisLineShow: false,
  catGridLine: { style: "none" },
};
const valGrid = () => ({ valGridLine: { color: GRID_HEX, size: 0.75 } });
const chartTitle = (t) => ({
  showTitle: true, title: t, titleFontSize: 13, titleColor: HEX.dk2, titleFontFace: "+mn-lt", titleAlign: "left",
});

// ------------------------------------------------------------------ layouts
const FOOTER = "Bottled water marketing mix model  ·  Jan 2022 – Jan 2025";

pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: HEX.dk2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.0, w: 9.2, h: 2.0, fontSize: 40, bold: true,
      color: C.background1, valign: "bottom", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 4.2, w: 9.0, h: 0.9, fontSize: 20,
      color: C.accent4, valign: "top", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "byline", type: "body", x: 0.8, y: 6.3, w: 9.0, h: 0.5, fontSize: 14,
      color: C.background2, margin: 0 }, text: "" } },
  ],
});

pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: HEX.lt1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.13, h: 1.05, fontSize: 28, bold: true,
      color: C.text2, valign: "middle", align: "left", margin: 0 }, text: "" } },
    { text: { text: FOOTER, options: { x: 0.6, y: 7.0, w: 8, h: 0.3, fontSize: 10, color: MUTED_HEX, margin: 0 } } },
  ],
  slideNumber: { x: 12.23, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: MUTED_HEX, align: "right", margin: 0 },
});

pres.defineSlideMaster({
  title: "DIVIDER_DARK",
  background: { color: HEX.dk2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.6, w: 9, h: 1.2, fontSize: 40, bold: true,
      color: C.background1, align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 3.8, w: 9, h: 0.8, fontSize: 18,
      color: C.accent4, margin: 0 }, text: "" } },
  ],
});

// Small reusable pieces composed on slides --------------------------------
function sunAndWater(slide, big) {
  // Visual motif: a sun (accent 2) and a water drop circle (accent 1)
  if (big) {
    slide.addShape(pres.shapes.OVAL, { x: 10.3, y: -1.5, w: 4.8, h: 4.8, fill: { color: C.accent2, transparency: 10 }, line: { type: "none" }, objectName: "sun" });
    slide.addShape(pres.shapes.OVAL, { x: 11.2, y: 4.7, w: 3.4, h: 3.4, fill: { color: C.accent1, transparency: 30 }, line: { type: "none" }, objectName: "water" });
  } else {
    slide.addShape(pres.shapes.OVAL, { x: 10.4, y: 2.2, w: 3.0, h: 3.0, fill: { color: C.accent2, transparency: 10 }, line: { type: "none" }, objectName: "sun" });
  }
}

function card(slide, x, y, w, h, name) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h, rectRadius: 0.12, fill: { color: C.background2 }, line: { type: "none" }, objectName: name,
  });
}

function numberDot(slide, x, y, n, color = C.accent1) {
  slide.addShape(pres.shapes.OVAL, { x, y, w: 0.55, h: 0.55, fill: { color }, line: { type: "none" }, objectName: `dot ${n}` });
  slide.addText(String(n), { x, y, w: 0.55, h: 0.55, fontSize: 16, bold: true, color: C.background1, align: "center",
    valign: "middle", margin: 0, isTextBox: true });
}

function tableCell(text, opts = {}) {
  return { text, options: { fontSize: 14, color: C.text1, valign: "middle", ...opts } };
}

function headerRow(labels, fontSize = 13) {
  return labels.map((t, i) =>
    tableCell(t, { bold: true, color: C.background1, fill: { color: HEX.dk2 }, fontSize, align: i ? "right" : "left" }));
}

// ================================================================== MAIN
pres.addSection({ title: "Story" });

// 1. Title ----------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Story" });
  s.addText("What drives bottled-water sales, and what is media really worth?", { placeholder: "title" });
  s.addText("Marketing mix model  ·  161 weeks of data, Jan 2022 – Jan 2025", { placeholder: "body" });
  s.addText("Prepared by Yazan Alrefaai  ·  October 2026", { placeholder: "byline" });
  sunAndWater(s, true);
  s.addNotes(
    "Thank you for having me. The question I was given: help an FMCG bottled-water brand understand how effective its media is, " +
    "and what else drives its sales. I built a marketing mix model on three years of weekly data. " +
    "I will start with the answer, then show the evidence, and finish with recommendations and how far the model can be trusted. " +
    "About 15 minutes, then questions."
  );
}

// 2. Executive summary ------------------------------------------------------
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Story" });
  s.addText("Weather, price and distribution drive sales; media adds about 1% and returns over £1 per £1 in only two channels",
    { placeholder: "title" });

  const items = [
    { big: `${Math.round(share.Weather)}%`, color: C.accent1,
      text: `of volume comes from warm weather: ${pct(D.effects.temp)} per °C, faster above 20°C` },
    { big: pct(D.effects.acv1), color: C.accent1,
      text: `volume for each +1 point of distribution, the strongest lever (about £${D.effects.acv1_revenue_m.toFixed(0)}M a year)` },
    { big: pct(D.effects.price10), color: C.accent3,
      text: `volume when our price rises 10% vs competitors; our premium grew from +${Math.round((D.years.relative_price["2022"] - 1) * 100)}% to +${Math.round((D.years.relative_price["2024"] - 1) * 100)}%` },
    { big: `~${mediaShare.toFixed(0)}%`, color: C.accent1,
      text: `of volume driven by media; ${gbp(D.media_total_roi)} revenue per £1 across modelled channels` },
    { big: gbp(media["Online partnership"].roi), color: C.accent1,
      text: `per £1 from Online partnership, the best proven channel; TV and online video under £0.30` },
    { big: `${Math.round(D.promo.incremental_share * 100)}%`, color: C.accent3,
      text: `of promoted volume is estimated to be extra; discounts deepened from ${Math.round(D.years.promo_depth["2022"] * 100)}% to ${Math.round(D.years.promo_depth["2024"] * 100)}% with no extra volume` },
  ];
  const x0 = 0.6, y0 = 1.6, w = 3.84, h = 2.05, gap = 0.3;
  items.forEach((it, i) => {
    const x = x0 + (i % 3) * (w + gap);
    const y = y0 + Math.floor(i / 3) * (h + gap);
    card(s, x, y, w, h, `summary card ${i + 1}`);
    s.addText(it.big, { x: x + 0.3, y: y + 0.2, w: w - 0.6, h: 0.75, fontSize: 36, bold: true, color: it.color, margin: 0, isTextBox: true });
    s.addText(it.text, { x: x + 0.3, y: y + 1.0, w: w - 0.6, h: 0.9, fontSize: 14, color: C.text1, valign: "top", margin: 0, isTextBox: true });
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 6.2, w: 12.13, h: 0.6, rectRadius: 0.1, fill: { color: C.text2 }, line: { type: "none" }, objectName: "recommendation bar" });
  s.addText([
    { text: "Next moves:  ", options: { bold: true, color: C.accent2 } },
    { text: "grow distribution · mind the price gap · shift TV/video budget to Online partnership · test OOH · shallower promotions", options: { color: C.background1 } },
  ], { x: 0.85, y: 6.2, w: 11.7, h: 0.6, fontSize: 14, valign: "middle", margin: 0, isTextBox: true });
  s.addNotes(
    "Six numbers to remember. One: weather is the biggest swing factor, about a fifth of volume, and each degree adds about 2%. " +
    "Two: distribution is the strongest lever we control; one extra point of weighted distribution is worth about 3.7% volume, around £6M a year. " +
    "Three: price matters relative to competitors; our premium grew a lot and cost volume in 2023. " +
    "Four: media is small, about 0.8% of sales value in spend and about 1% of volume, returning £1.53 per £1 overall. " +
    "Five: Online partnership is the best proven channel at about £3 per £1; TV and online video did not pay back in this data. " +
    "Six: promotions are expensive; only about 28% of promoted volume is truly incremental. " +
    "The bar at the bottom previews the recommendations I will come back to at the end."
  );
}

// 3. Data overview ------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Story" });
  s.addText("Three years of weekly data: sales follow the temperature, prices nearly doubled and media was sparse",
    { placeholder: "title" });
  const labels = D.weekly.date;
  const lineOpts = (title, color, fmt) => ({
    ...axisStyle, ...valGrid(), ...chartTitle(title), showLegend: false, chartColors: [color],
    lineSize: 2, lineDataSymbol: "none", catAxisLabelFrequency: 13, valAxisLabelFormatCode: fmt,
  });
  s.addChart(pres.charts.LINE, [{ name: "Volume (M kg)", labels, values: D.weekly.volume }],
    { x: 0.6, y: 1.55, w: 7.9, h: 2.75, ...lineOpts("Weekly volume sales (million kg)", HEX.accent1, "0.0"), valAxisMinVal: 0,
      altText: "Line chart of weekly volume sales, Jan 2022 to Jan 2025: peaks every summer between 4.5 and 5.4 million kg, winter lows around 2 to 2.5 million kg." });
  s.addChart(pres.charts.LINE, [{ name: "Max temperature", labels, values: D.weekly.temp }],
    { x: 0.6, y: 4.35, w: 7.9, h: 2.4, ...lineOpts("Weekly max temperature (°C)", HEX.accent2, "0"),
      altText: "Line chart of weekly max temperature: summer highs of 26 to 34°C, winter lows of 6 to 10°C, matching the shape of volume sales." });

  const facts = [
    [`${D.facts.weeks} weeks`, `${D.facts.variables} variables: sales, price, promotion, distribution, competitors, weather, media`],
    [`£${Math.round(D.facts.value_sales_m)}M`, `value sales; volume moves with temperature (correlation ${D.facts.temp_corr.toFixed(2)})`],
    [`£${D.years.base_price["2022"].toFixed(2)} → £${D.years.base_price["2024"].toFixed(2)}`, "average base price per kg, 2022 to 2024"],
    [`£${D.facts.media_spend_m.toFixed(1)}M`, `media over 3 years, only ${(D.facts.media_pct_sales * 100).toFixed(1)}% of sales; TV ran 3 weeks, OOH 5`],
  ];
  card(s, 8.85, 1.6, 3.88, 5.15, "facts card");
  facts.forEach(([big, small], i) => {
    s.addText([
      { text: big, options: { fontSize: 24, bold: true, color: C.accent1, breakLine: true } },
      { text: small, options: { fontSize: 14, color: C.text1 } },
    ], { x: 9.1, y: 1.8 + i * 1.22, w: 3.4, h: 1.1, valign: "top", margin: 0, isTextBox: true });
  });
  s.addNotes(
    "The data: 161 weeks, January 2022 to January 2025, 90 variables. Volume peaks every summer and the shape matches temperature almost exactly. " +
    "Prices rose sharply: the base price per kg went from 77p to £1.08. Part of that is a shift to smaller packs, which cost more per kg. " +
    "Media is small and sparse: £3.5M over three years, under 1% of sales; TV ran only three weeks, OOH five. That matters later: " +
    "with so few weeks some media effects are hard to pin down, and I will be upfront about that. " +
    "Data checks: no missing values, no gaps in weeks, promo sales never exceed total sales, price equals value over volume."
  );
}

// 4. What drives sales -----------------------------------------------------------
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Story" });
  s.addText(`Base sales and weather explain ${(100 - mediaShare).toFixed(0)}% of volume; media adds a thin layer of about ${mediaShare.toFixed(0)}%`,
    { placeholder: "title" });
  const m = D.monthly;
  s.addChart(pres.charts.AREA, [
    { name: "Base (brand, price, distribution)", labels: m.labels, values: m.Base },
    { name: "Weather", labels: m.labels, values: m.Weather },
    { name: "Media", labels: m.labels, values: m.Media },
  ], {
    x: 0.6, y: 1.55, w: 7.7, h: 5.2, barGrouping: "stacked", chartColors: [HEX.accent4, HEX.accent2, HEX.accent3],
    altText: "Stacked area chart of average weekly volume per month split into base, weather and media: base about 2.2 to 2.8 million kg, weather adds up to 1.7 million kg in summer, media a thin layer.",
    ...axisStyle, ...valGrid(), ...chartTitle("Average weekly volume by driver, per month (million kg)"),
    showLegend: true, legendPos: "b", legendFontSize: 12, legendFontFace: "+mn-lt", legendColor: MUTED_HEX,
    catAxisLabelFrequency: 3, valAxisLabelFormatCode: "0.0", valAxisMinVal: 0,
  });

  const e = D.effects;
  const rows = [
    ["+1°C max temperature", pct(e.temp)],
    ["Each °C above 20°C (extra)", pct(e.hot)],
    ["+10 mm rain", pct(e.rain10)],
    ["Christmas / New Year week", pct(e.xmas, 0)],
    ["+10% price vs competitors", pct(e.price10)],
    ["+1 point distribution (ACV)", pct(e.acv1)],
  ].map(([k, v], i) => [
    tableCell(k, { fill: { color: i % 2 ? "FFFFFF" : HEX.lt2 } }),
    tableCell(v, { bold: true, align: "right", color: v.startsWith("−") ? HEX.accent3 : HEX.accent1, fill: { color: i % 2 ? "FFFFFF" : HEX.lt2 } }),
  ]);
  s.addTable([headerRow(["Driver", "Effect"], 14), ...rows], { x: 8.7, y: 1.6, w: 4.03, colW: [2.93, 1.1], rowH: 0.5,
    border: { type: "none" }, margin: [0, 0.1, 0, 0.1], objectName: "Table: effect of each driver on weekly volume" });
  s.addText("All effects highly significant (|t| > 4). Base = sales in a cool, dry week without media, at that week's price and distribution.",
    { x: 8.7, y: 5.4, w: 4.03, h: 1.2, fontSize: 12, color: MUTED_HEX, valign: "top", margin: 0, isTextBox: true });
  s.addNotes(
    "This splits an average week in each month into three layers. The base is what the brand sells in a cool, dry week without media, given its price and shelf presence: about 79%. " +
    "Weather, in orange, adds about 20% and drives all the summer peaks. Media is the thin red layer on top, about 1%. " +
    "On the right, the size of each driver. One degree warmer adds about 1.9%, and above 20 degrees each degree adds another 2.2%, so heatwaves matter a lot. " +
    "Christmas week drops about 22%. A 10% higher price relative to competitors costs about 4%. One point of distribution adds 3.7%. " +
    "How we got this: a log-linear regression, so each coefficient reads directly as a percentage effect."
  );
}

// 5. Media effectiveness ------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Story" });
  s.addText(`Online partnership returns ${gbp(media["Online partnership"].roi)} per £1; TV and online video returned under £0.30`,
    { placeholder: "title" });
  const order = ["OOH", "Online partnership", "Online video", "TV"];
  s.addChart(pres.charts.BAR, [{ name: "Revenue per £1", labels: order, values: order.map((c) => media[c].roi) }], {
    x: 0.6, y: 1.55, w: 5.9, h: 4.4, barDir: "bar", chartColors: order.map((c) => (media[c].roi >= 1 ? HEX.accent1 : HEX.accent5)),
    altText: `Bar chart of revenue return per £1 of media: ${order.map((c) => `${c} ${gbp(media[c].roi)}`).join(", ")}.`,
    ...axisStyle, ...valGrid(), ...chartTitle("Revenue return per £1 of media (ROI)"), showLegend: false,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "£0.00", dataLabelColor: HEX.dk1, dataLabelFontSize: 12,
    dataLabelFontFace: "+mn-lt", valAxisLabelFormatCode: "£0", valAxisMinVal: 0, catAxisOrientation: "maxMin", barGapWidthPct: 60,
  });

  const conf = (t) => (Math.abs(t) >= 2 ? "High" : Math.abs(t) >= 1 ? "Medium" : "Low");
  const header = ["Channel", "Spend", "ROI", "95% range", "Evidence"].map((t, i) =>
    tableCell(t, { bold: true, color: C.background1, fill: { color: HEX.dk2 }, fontSize: 13, align: i ? "right" : "left" }));
  const rows = [header, ...order.map((c, i) => {
    const r = media[c];
    const fill = { color: i % 2 ? "FFFFFF" : HEX.lt2 };
    return [
      tableCell(c, { fill }), tableCell(gbpK(r.spend), { fill, align: "right" }),
      tableCell(gbp(r.roi), { fill, align: "right", bold: true }),
      tableCell(`${gbp(r.roi_low)}–${gbp(r.roi_high)}`, { fill, align: "right" }),
      tableCell(conf(r.t_stat), { fill, align: "right" }),
    ];
  })];
  s.addTable(rows, { x: 6.9, y: 1.7, w: 5.83, colW: [1.9, 0.95, 0.85, 1.28, 0.85], rowH: 0.5, border: { type: "none" }, margin: [0, 0.08, 0, 0.08],
    objectName: "Table: spend, ROI, 95% range and evidence by media channel" });
  s.addText([
    { text: "Read the range, not just the bar. ", options: { bold: true } },
    { text: "OOH looks best but rests on 5 weeks of activity, so its range starts at zero. Online partnership is the only channel that is both high and certain." },
  ], { x: 6.9, y: 4.4, w: 5.83, h: 1.3, fontSize: 14, color: C.text1, valign: "top", margin: 0, isTextBox: true });

  const nm = D.not_measured;
  s.addText(`Not measurable: Social (${gbpK(nm.Social)}) showed no positive lift; Search (${gbpK(nm.Search)}) and RDM (${gbpK(nm.RDM)}) are too small to estimate. ` +
    "ROI = incremental revenue ÷ spend (revenue, not profit: no margin data).",
    { x: 0.6, y: 6.15, w: 12.13, h: 0.6, fontSize: 12, color: MUTED_HEX, valign: "middle", margin: 0, isTextBox: true });
  s.addNotes(
    "Return on investment per channel: incremental revenue divided by spend. Incremental means the sales the model says would disappear if the channel were switched off. " +
    `Online partnership: about £3.07 per £1, range £1.65 to £4.52, and a t-statistic above 4, so this is our most reliable result. ` +
    "OOH shows the highest point estimate, over £5, but it ran only five weeks; the range runs from zero to £13, so it is promising, not proven. " +
    "TV returned about 27p and online video about 29p. TV spent £176k a week squeezed into three weeks, which puts it deep into diminishing returns. " +
    "Social, Search and RDM cannot be measured: Social shows no positive lift, the other two are about 1% of budget. " +
    "Important caveat: this is revenue ROI. Without margins I cannot say whether £1.53 overall is profitable."
  );
}

// 6. Budget optimisation ---------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Story" });
  s.addText(`Moving 30% of TV and video budget into Online partnership could add about £${(scenOP.delta_revenue / 1e6).toFixed(1)}M at the same spend`,
    { placeholder: "title" });
  const labels = D.curves.grid_k.map((k) => (k >= 1000 ? `£${(k / 1000).toFixed(1)}M` : `£${k}k`));
  const chans = ["OOH", "Online partnership", "Online video", "TV"];
  s.addChart(pres.charts.LINE, chans.map((c) => ({ name: c, labels, values: D.curves[c] })), {
    x: 0.6, y: 1.55, w: 7.5, h: 5.2, chartColors: [HEX.accent2, HEX.accent1, HEX.accent6, HEX.accent3], lineSize: 2.5,
    altText: "Response curves of incremental revenue against total spend: OOH and Online partnership rise steeply, Online video and TV stay almost flat.",
    lineDataSymbol: "none", ...axisStyle, ...valGrid(), ...chartTitle("Response curves: incremental revenue (£M) vs total spend"),
    showLegend: true, legendPos: "b", legendFontSize: 12, legendFontFace: "+mn-lt", legendColor: MUTED_HEX,
    catAxisLabelFrequency: 4, valAxisLabelFormatCode: "£0.0", valAxisMinVal: 0,
  });

  const rows = chans.map((c, i) => {
    const fill = { color: i % 2 ? "FFFFFF" : HEX.lt2 };
    return [tableCell(c, { fill }), tableCell(`${gbp(media[c].marginal_roi)}`, { fill, bold: true, align: "right",
      color: media[c].marginal_roi >= 1 ? HEX.accent1 : HEX.accent3 }), tableCell(gbpK(media[c].spend), { fill, align: "right", color: MUTED_HEX })];
  });
  s.addTable([headerRow(["Channel", "Next £1 returns", "Spend now"]), ...rows], { x: 8.5, y: 1.6, w: 4.23, colW: [1.75, 1.33, 1.15],
    rowH: 0.45, border: { type: "none" }, margin: [0, 0.08, 0, 0.08], objectName: "Table: what the next £1 returns by channel" });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.5, y: 4.15, w: 4.23, h: 1.45, rectRadius: 0.12, fill: { color: C.text2 }, line: { type: "none" }, objectName: "scenario card" });
  s.addText([
    { text: `+£${(scenOP.delta_revenue / 1e6).toFixed(1)}M revenue`, options: { fontSize: 24, bold: true, color: C.accent2, breakLine: true } },
    { text: `Shift ${gbpK(scenOP.moved)} from TV and online video into Online partnership, same total budget`, options: { fontSize: 14, color: C.background1 } },
  ], { x: 8.75, y: 4.25, w: 3.8, h: 1.25, valign: "middle", margin: 0, isTextBox: true });
  s.addText("TV spent £176k a week for 3 weeks, well past saturation: if kept, spread it over more weeks. Test OOH before scaling it.",
    { x: 8.5, y: 5.75, w: 4.23, h: 1.0, fontSize: 14, color: C.text1, valign: "top", margin: 0, isTextBox: true });
  s.addNotes(
    "Response curves show diminishing returns: each curve flattens as spend grows. The slope at today's spend is the marginal ROI, what the next pound returns, and that is what budget decisions should use. " +
    "OOH and Online partnership are still on the steep part, around £2 to £3 for the next pound. TV and online video are flat, 10p and 20p. " +
    "So a simple scenario: keep the total budget, move 30% of TV and video money, about £534k, into Online partnership in the weeks it already runs. The model says about £0.9M more revenue. " +
    "Two cautions. Moving into OOH looks even better on paper, but OOH rests on five weeks, so I would test it first, for example with a regional test. " +
    "And Online partnership saturates too, so this is a direction, not a precise forecast."
  );
}

// 7. Price, distribution, promotions ---------------------------------------------------------
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Story" });
  s.addText("A wider price gap cost volume in 2023; distribution gains won it back in 2024; deep promotions mostly subsidise sales",
    { placeholder: "title" });
  const br = D.bridge;
  s.addChart(pres.charts.BAR, [
    { name: `2022 → 2023 (volume ${br.totals["2022->2023"]}%)`, labels: br.drivers, values: br["2022->2023"] },
    { name: `2023 → 2024 (volume +${br.totals["2023->2024"]}%)`, labels: br.drivers, values: br["2023->2024"] },
  ], {
    x: 0.6, y: 1.55, w: 6.6, h: 5.2, barDir: "bar", chartColors: [HEX.accent5, HEX.accent1],
    altText: `Bar chart of volume change by driver. 2022 to 2023: relative price ${br["2022->2023"][2]} points, distribution +${br["2022->2023"][3]}. 2023 to 2024: distribution +${br["2023->2024"][3]}, relative price ${br["2023->2024"][2]}.`,
    ...axisStyle, ...valGrid(), ...chartTitle("Why volume changed: contribution by driver (% points)"),
    showLegend: true, legendPos: "b", legendFontSize: 12, legendFontFace: "+mn-lt", legendColor: MUTED_HEX,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "+0.0;−0.0;0.0", dataLabelFontSize: 11,
    dataLabelColor: HEX.dk1, dataLabelFontFace: "+mn-lt", valAxisLabelFormatCode: "+0;−0;0", catAxisOrientation: "maxMin",
    valAxisMinVal: -10, valAxisMaxVal: 15, barGapWidthPct: 40, catAxisLabelPos: "low",
  });

  const y = D.years;
  const cards = [
    ["Price", `Our base price premium over competitors grew from +${Math.round((y.relative_price["2022"] - 1) * 100)}% (2022) to +${Math.round((y.relative_price["2024"] - 1) * 100)}% (2024). Elasticity −${Math.abs(D.effects.elasticity).toFixed(2)}: the 2023 rise cost about 8% volume.`],
    ["Distribution", `ACV rose from ${y.acv["2023"]} to ${y.acv["2024"]} in 2024, worth about +13% volume. We still reach under half of the market.`],
    ["Promotions", `Promoted share of volume went from ${Math.round(y.promo_share["2022"] * 100)}% to ${Math.round(y.promo_share["2024"] * 100)}%. Promotions lift sales by widening store reach, not through discount depth; an estimated ~${Math.round(D.promo.incremental_share * 100)}% of promoted volume is extra.`],
  ];
  cards.forEach(([head, body], i) => {
    const cy = 1.6 + i * 1.75;
    card(s, 7.6, cy, 5.13, 1.6, `${head} card`);
    s.addText([
      { text: head, options: { fontSize: 16, bold: true, color: C.text2, breakLine: true } },
      { text: body, options: { fontSize: 14, color: C.text1 } },
    ], { x: 7.85, y: cy + 0.12, w: 4.7, h: 1.38, valign: "top", margin: 0, isTextBox: true });
  });
  s.addNotes(
    "Why did volume fall about 6% in 2023 and grow about 7% in 2024? In a log model the change splits exactly into each driver's contribution. " +
    "2023: the main cause is price. Our base price rose about 40% while competitors rose about 9%, so our premium over the competitor average went from 46% to 75%. That cost about 8 points of volume. " +
    "2024: distribution. Weighted distribution rose from about 40 to 43.5, worth about 13 points of volume, more than offsetting price and slightly cooler weather. " +
    "Promotions: once distribution is in the model, no promotion variable adds explanatory power, including discount depth. " +
    "Promotions seem to work by getting the brand sold in more stores. Through that route they add about 8% volume, while 26% of volume is sold on deal, " +
    "so roughly 28% of promoted volume is extra and the rest would have sold at full price. Discounts doubled from 22% to 46% without extra volume per store."
  );
}

// 8. Method and trust ---------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Story" });
  s.addText(`A simple, transparent regression that forecasts unseen weeks within ${(D.model.holdout_mape * 100).toFixed(0)}%, with clear limits`,
    { placeholder: "title" });
  const steps = [
    ["Clean and explore", "Dates, gaps, definitions; 18 charts; traps found (e.g. store counts follow demand)"],
    ["Transform media", "Carryover (adstock) and diminishing returns (saturation) per channel"],
    ["Regress", "Log of weekly volume on 10 drivers, robust (Newey-West) errors"],
    ["Validate", "12-week holdout, residuals, multicollinearity, leave-one-year-out"],
  ];
  const sw = 2.83, sg = 0.27;
  steps.forEach(([h, b], i) => {
    const x = 0.6 + i * (sw + sg);
    card(s, x, 1.6, sw, 1.95, `step ${i + 1}`);
    numberDot(s, x + 0.2, 1.75, i + 1);
    s.addText(h, { x: x + 0.9, y: 1.75, w: sw - 1.0, h: 0.55, fontSize: 16, bold: true, color: C.text2, valign: "middle", margin: 0, isTextBox: true });
    s.addText(b, { x: x + 0.2, y: 2.45, w: sw - 0.4, h: 1.0, fontSize: 14, color: C.text1, valign: "top", margin: 0, isTextBox: true });
  });

  const stats = [
    [D.model.adj_r2.toFixed(2), "adjusted R²: share of weekly variation explained"],
    [`${(D.model.mape * 100).toFixed(1)}%`, "average weekly error"],
    [`${(D.model.holdout_mape * 100).toFixed(1)}%`, "error on 12 unseen weeks"],
    ["< 4", "variance inflation for every driver: no harmful overlap"],
  ];
  stats.forEach(([big, small], i) => {
    const y = 3.85 + i * 0.75;
    s.addText(big, { x: 0.6, y, w: 1.6, h: 0.7, fontSize: 32, bold: true, color: C.accent1, valign: "middle", margin: 0, isTextBox: true });
    s.addText(small, { x: 2.3, y, w: 3.9, h: 0.7, fontSize: 14, color: C.text1, valign: "middle", margin: 0, isTextBox: true });
  });

  s.addText("How far to trust it", { x: 6.6, y: 3.85, w: 6.13, h: 0.45, fontSize: 18, bold: true, color: C.text2, margin: 0, isTextBox: true });
  const caveats = [
    "TV ran 3 weeks and OOH 5: their ROIs have wide ranges",
    "Channels overlap in time (TV inside the Online partnership burst)",
    "Revenue ROI, short-term only: no margins, no long-term brand effect",
    `Price effect shrinks if a time trend is added (−${Math.abs(D.effects.elasticity).toFixed(2)} vs −0.10)`,
    "Distribution counts stores that sold, so it can partly follow demand",
  ];
  s.addText(caveats.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < caveats.length - 1 } })),
    { x: 6.6, y: 4.35, w: 6.13, h: 2.4, fontSize: 14, color: C.text1, valign: "top", margin: 0, paraSpaceAfter: 8, isTextBox: true });
  s.addNotes(
    "How I built it. First cleaning and exploration, which found traps: for example the number of stores selling rises every summer because it counts stores that sold at least one bottle, so it follows demand and cannot explain it. " +
    "Second, media transformations: adstock, meaning an ad keeps working for a few weeks with a fading carryover; and saturation, meaning each extra pound does less. Carryover rates come from a grid search within sensible ranges, keeping only models where media has a positive effect. " +
    "Third, an ordinary least squares regression on the log of weekly volume with ten drivers. Errors are correlated week to week, so I use Newey-West robust standard errors. " +
    "Fourth, validation: trained without the last 12 weeks, the model forecast them within about 4%, so it is not overfitting. All variance inflation factors are below 4. Coefficients hold when any one year is dropped. " +
    "The limits are on the right and I would rather state them than have them found: sparse media, overlapping campaigns, revenue rather than profit, and a price effect that depends on whether you allow a trend."
  );
}

// 9. Recommendations -----------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Story" });
  s.addText("Recommendations: grow reach, mind the price gap, rebalance media, rethink promotions", { placeholder: "title" });
  const recs = [
    ["Protect and grow distribution", `Each +1 point of ACV is worth about £${D.effects.acv1_revenue_m.toFixed(0)}M a year; we reach under half the market. Target the missing retailers.`],
    ["Manage the price gap", `Our premium over competitors reached +${Math.round((D.years.relative_price["2024"] - 1) * 100)}%. Price against competitors, not in isolation; test before further rises.`],
    ["Rebalance media", "Move TV and video money to Online partnership; run a regional test of OOH; if TV stays, spread it over more weeks."],
    ["Rethink promotions", "Test shallower discounts (25–30%) and focus on store reach rather than depth."],
  ];
  recs.forEach(([h, b], i) => {
    const y = 1.65 + i * 1.28;
    numberDot(s, 0.6, y + 0.05, i + 1, i % 2 ? C.accent2 : C.accent1);
    s.addText([
      { text: h, options: { fontSize: 18, bold: true, color: C.text2, breakLine: true } },
      { text: b, options: { fontSize: 14, color: C.text1 } },
    ], { x: 1.4, y, w: 6.9, h: 1.15, valign: "top", margin: 0, isTextBox: true });
  });
  card(s, 8.75, 1.6, 3.98, 5.15, "questions and next steps card");
  const bulletList = (items) => items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1 } }));
  s.addText("Questions for the client", { x: 9.0, y: 1.8, w: 3.5, h: 0.45, fontSize: 18, bold: true, color: C.text2, margin: 0, isTextBox: true });
  s.addText(bulletList([
    "Price per kg nearly doubled: list price rises or a shift to smaller packs?",
    "Why were promotions paused from June to December 2022?",
    "What exactly are Online partnership and RDM?",
    "Is other marketing (in-store, trade) missing from the data?",
  ]), { x: 9.0, y: 2.3, w: 3.5, h: 2.5, fontSize: 14, color: C.text1, valign: "top", margin: 0, paraSpaceAfter: 6, isTextBox: true });
  s.addText("Next steps for the model", { x: 9.0, y: 4.85, w: 3.5, h: 0.45, fontSize: 18, bold: true, color: C.text2, margin: 0, isTextBox: true });
  s.addText(bulletList([
    "Bayesian MMM with priors",
    "Regional data and lift tests",
    "Margin data for profit ROI",
  ]), { x: 9.0, y: 5.35, w: 3.5, h: 1.25, fontSize: 14, color: C.text1, valign: "top", margin: 0, paraSpaceAfter: 4, isTextBox: true });
  s.addNotes(
    "Four recommendations. One: distribution is the biggest controllable lever; find out which retailers are missing. " +
    "Two: price relative to competitors; our premium has grown to almost double the competitor average, and that cost volume in 2023. " +
    "Three: media; shift money from TV and online video to Online partnership, and test OOH before scaling it. " +
    "Four: promotions; deeper discounts did not buy more volume, so test shallower ones. " +
    "The data also raises questions I would put to the client: did the price per kg rise because of list prices or a move to smaller packs; " +
    "why promotions stopped in the second half of 2022; what Online partnership and RDM actually are; and whether in-store or trade activity is missing from the data. " +
    "For the model itself, the natural next steps are a Bayesian version with priors, regional data with lift tests to calibrate it, and margin data for profit ROI. " +
    "Happy to take questions."
  );
}

// ================================================================== APPENDIX
pres.addSection({ title: "Appendix" });
{
  const s = pres.addSlide({ masterName: "DIVIDER_DARK", sectionTitle: "Appendix" });
  s.addText("Appendix", { placeholder: "title" });
  s.addText("Model details, diagnostics, media calendar and variables tested", { placeholder: "body" });
  sunAndWater(s, false);
}

// A1 coefficients
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Appendix" });
  s.addText("Model specification: log-linear OLS on weekly volume, 10 drivers", { placeholder: "title" });
  s.addText("ln(volume) = b0 + weather + Christmas + b·ln(price / competitor price) + b·ACV + Σ b·ln(1 + adstock(spend) / scale)",
    { x: 0.6, y: 1.5, w: 12.13, h: 0.45, fontSize: 14, color: C.text2, italic: true, margin: 0, isTextBox: true });
  const header = ["Driver", "Coefficient", "t-stat (HAC)", "Evidence"].map((t, i) =>
    tableCell(t, { bold: true, color: C.background1, fill: { color: HEX.dk2 }, fontSize: 13, align: i ? "right" : "left" }));
  const rows = [header, ...D.model.coefficients.map((r, i) => {
    const fill = { color: i % 2 ? "FFFFFF" : HEX.lt2 };
    const ev = Math.abs(r.t) >= 2 ? "High" : Math.abs(r.t) >= 1 ? "Medium" : "Low";
    return [tableCell(r.driver, { fill, fontSize: 13 }), tableCell(r.coef.toFixed(4), { fill, align: "right", fontSize: 13 }),
      tableCell(r.t.toFixed(1), { fill, align: "right", fontSize: 13 }), tableCell(ev, { fill, align: "right", fontSize: 13 })];
  })];
  s.addTable(rows, { x: 0.6, y: 2.05, w: 8.0, colW: [4.0, 1.4, 1.4, 1.2], rowH: 0.4, border: { type: "none" }, margin: [0, 0.08, 0, 0.08],
    objectName: "Table: model coefficients, t-statistics and strength of evidence" });
  card(s, 9.0, 2.05, 3.73, 4.4, "adstock card");
  const r = D.model.rates;
  s.addText([
    { text: "Weekly carryover rates", options: { fontSize: 16, bold: true, color: C.text2, breakLine: true } },
    ...Object.entries(r).map(([k, v], i) => ({ text: `${k}: ${v.toFixed(1)}`, options: { fontSize: 14, color: C.text1, bullet: true, breakLine: true } })),
    { text: "Grid search within business ranges; best AIC among models with all media effects positive. Saturation scale = average adstocked spend in on-air weeks.", options: { fontSize: 12, color: MUTED_HEX } },
  ], { x: 9.25, y: 2.25, w: 3.25, h: 4.0, valign: "top", margin: 0, paraSpaceAfter: 6, isTextBox: true });
  s.addNotes("Full model table. Coefficients are in log points: multiply by 100 for an approximate percentage effect per unit. Media coefficients apply to the transformed media variable.");
}

// A2 journey + diagnostics
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Appendix" });
  s.addText("Model building and diagnostics: each driver group earns its place; residuals checked", { placeholder: "title" });
  s.addChart(pres.charts.LINE, [
    { name: "Actual", labels: D.weekly.date, values: D.fit.actual },
    { name: "Model", labels: D.weekly.date, values: D.fit.model },
  ], {
    x: 0.6, y: 1.5, w: 12.13, h: 2.55, chartColors: [HEX.accent1, HEX.accent2], lineSize: 1.75, lineDataSymbol: "none",
    altText: "Line chart of actual versus model weekly volume: the two lines overlap closely across all three years.",
    ...axisStyle, ...valGrid(), ...chartTitle("Actual vs model, weekly volume (million kg)"), showLegend: true, legendPos: "r",
    legendFontSize: 12, legendFontFace: "+mn-lt", legendColor: MUTED_HEX, catAxisLabelFrequency: 13, valAxisLabelFormatCode: "0.0", valAxisMinVal: 0,
  });
  const jh = ["Stage", "Adj. R²", "Error"].map((t, i) => tableCell(t, { bold: true, color: C.background1, fill: { color: HEX.dk2 }, fontSize: 13, align: i ? "right" : "left" }));
  const jr = [jh, ...D.model.journey.map((j, i) => {
    const fill = { color: i % 2 ? "FFFFFF" : HEX.lt2 };
    return [tableCell(j.stage, { fill, fontSize: 13 }), tableCell(j.adj_R2.toFixed(3), { fill, align: "right", fontSize: 13 }),
      tableCell(`${(j.MAPE * 100).toFixed(1)}%`, { fill, align: "right", fontSize: 13 })];
  })];
  s.addTable(jr, { x: 0.6, y: 4.25, w: 6.2, colW: [4.2, 1.0, 1.0], rowH: 0.4, border: { type: "none" }, margin: [0, 0.08, 0, 0.08],
    objectName: "Table: model fit at each building stage" });
  const dh = ["Check", "Value", "p-value"].map((t, i) => tableCell(t, { bold: true, color: C.background1, fill: { color: HEX.dk2 }, fontSize: 13, align: i ? "right" : "left" }));
  const dr = [dh, ...D.diagnostics.map((d, i) => {
    const fill = { color: i % 2 ? "FFFFFF" : HEX.lt2 };
    return [tableCell(d.check, { fill, fontSize: 13 }), tableCell(Number(d.value).toFixed(2), { fill, align: "right", fontSize: 13 }),
      tableCell(d.p_value == null || Number.isNaN(d.p_value) ? "–" : Number(d.p_value).toFixed(3), { fill, align: "right", fontSize: 13 })];
  })];
  s.addTable(dr, { x: 7.2, y: 4.25, w: 5.53, colW: [3.3, 1.1, 1.13], rowH: 0.4, border: { type: "none" }, margin: [0, 0.08, 0, 0.08],
    objectName: "Table: residual diagnostic tests" });
  s.addNotes(
    "Model journey: temperature alone explains 61% of weekly variation; adding hot weeks, rain and Christmas takes it to 72%; price alone adds nothing until distribution is added, " +
    "which jumps the fit to 91%. That is omitted-variable bias in action: distribution and price rose together in 2024, so without distribution the price effect was hidden. " +
    "Diagnostics: Durbin-Watson 1.26 and Breusch-Godfrey show correlated errors, handled with Newey-West robust errors. Mild heteroskedasticity and fat tails from a few unusual weeks."
  );
}

// A3 media calendar
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Appendix" });
  s.addText("Media calendar: sparse, bursty activity with channels overlapping in time", { placeholder: "title" });
  const cal = D.calendar;
  const maxK = Math.max(...cal.spend_k.flat());
  const shade = (v) => {
    if (v <= 0) return "FFFFFF";
    const t = Math.min(1, Math.sqrt(v / maxK));
    const mix = (a, b) => Math.round(a + (b - a) * (0.25 + 0.75 * t)).toString(16).padStart(2, "0");
    return mix(0xEE, 0x1B) + mix(0xF6, 0x7F) + mix(0xF7, 0x8C);
  };
  const monthLabel = cal.months.map((m, i) => (i % 6 === 0 ? m : ""));
  const head = [tableCell("", { fontSize: 10 }), ...monthLabel.map((m) => tableCell(m, { fontSize: 10, color: MUTED_HEX, align: "left" }))];
  const rows = [head, ...cal.channels.map((ch, r) => [
    tableCell(ch, { fontSize: 12, bold: true }),
    ...cal.spend_k[r].map((v) => tableCell("", { fill: { color: shade(v) }, border: [{ type: "solid", color: "FFFFFF", pt: 1 }, { type: "solid", color: "FFFFFF", pt: 1 }, { type: "solid", color: "FFFFFF", pt: 1 }, { type: "solid", color: "FFFFFF", pt: 1 }] })),
  ])];
  const cellW = (12.13 - 1.9) / cal.months.length;
  s.addTable(rows, { x: 0.6, y: 1.7, w: 12.13, colW: [1.9, ...cal.months.map(() => cellW)], rowH: [0.35, ...cal.channels.map(() => 0.45)], margin: [0, 0.0, 0, 0.03],
    objectName: "Table: monthly media calendar, darker cells mean more spend" });
  s.addText("Darker = more spend that month. TV ran inside the Online partnership burst (spring 2023); in summer 2024 VOD, OLV, Social and RDM all ran together, during hot weather and heavy promotion. " +
    "That overlap is why VOD and OLV are combined as Online video.",
    { x: 0.6, y: 6.05, w: 12.13, h: 0.8, fontSize: 14, color: C.text1, valign: "top", margin: 0, isTextBox: true });
  s.addNotes("Use this slide if asked why some channels could not be separated: they ran in the same weeks, so the data cannot tell their effects apart.");
}

// A4 variables rejected
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Appendix" });
  s.addText("Variables tested and left out, and why", { placeholder: "title" });
  const reason = {
    "Promo ACV distribution": "No effect once distribution is in; promotions work through store reach",
    "Promo discount depth (%)": "No effect: deeper discounts did not add volume",
    "Linear trend (per year)": "Collinear with relative price and has no business meaning (sensitivity only)",
    "Competitor A media": "Positive (category halo?) but overlaps our 2024 video burst",
    "Competitor B media": "No effect",
    "Social media": "Negative sign in every specification: not measurable",
    "Search media": "1% of budget; spurious negative sign",
    "RDM media": "Under 1% of budget; no effect",
  };
  const header = ["Variable", "Coef.", "t", "Why it is out"].map((t, i) => tableCell(t, { bold: true, color: C.background1, fill: { color: HEX.dk2 }, fontSize: 13, align: i === 1 || i === 2 ? "right" : "left" }));
  const rows = [header, ...D.rejected.map((r, i) => {
    const fill = { color: i % 2 ? "FFFFFF" : HEX.lt2 };
    return [tableCell(r.variable, { fill, fontSize: 13 }), tableCell(fixed(r.coef, 4), { fill, align: "right", fontSize: 13 }),
      tableCell(fixed(r.t, 1), { fill, align: "right", fontSize: 13 }), tableCell(reason[r.variable] || "", { fill, fontSize: 13 })];
  })];
  s.addTable(rows, { x: 0.6, y: 1.6, w: 12.13, colW: [3.0, 1.1, 0.8, 7.23], rowH: 0.5, border: { type: "none" }, margin: [0, 0.08, 0, 0.08],
    objectName: "Table: variables tested and left out, with reasons" });
  s.addNotes("Each candidate was added on top of the final model one at a time. Also tested and rejected earlier: number of stores selling (follows demand), competitor volumes (same demand drivers), average price (mixes in promotions).");
}

// ------------------------------------------------------------------ write
(async () => {
  const out = path.join(__dirname, "..", "MMM_presentation.pptx");
  await pres.writeFile({ fileName: out });
  // pptxgenjs cannot write theme colours itself; this writes THEME into the file
  const { applyTheme } = require("./apply_theme.js");
  await applyTheme(out, THEME);
  // Decorative shapes, table descriptions and header rows (pptxgenjs cannot write these)
  const { fixAccessibility } = require("./accessibility.js");
  await fixAccessibility(out);
  console.log("Wrote", out);
})();
