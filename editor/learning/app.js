// SPDX-License-Identifier: AGPL-3.0-or-later
'use strict';
const learning = window.EDITOR8_LEARNING;
const slides = learning.course.lessons.flatMap(lesson => lesson.slides.map(slide => ({...slide, lesson})));
const chapters = learning.handbook.chapters;
const query = new URLSearchParams(location.search);
document.documentElement.classList.toggle('embedded', query.get('embedded') === '1');
let mode = query.get('mode') === 'handbook' ? 'handbook' : 'training';
let index = Math.max(0, slides.findIndex(slide => slide.lesson.id === query.get('lesson')));
let chapterIndex = 0, timer = null;
const labels = new Map(learning.example.nodes.map(node => [node.id, node.label]));
const $ = id => document.getElementById(id);
const el = (tag, text, cls) => { const item = document.createElement(tag); if (text) item.textContent = text; if (cls) item.className = cls; return item; };
function stop() { if (timer) clearInterval(timer); timer = null; $('play').textContent = 'Abspielen'; }
function button(text, action) { const item = el('button', text); item.type = 'button'; item.addEventListener('click', action); return item; }
function model(focus) {
  const pane = el('section', '', 'model'); pane.append(el('h2', learning.example.title));
  const explanation = el('p', '', 'explanation');
  for (const node of learning.example.nodes) {
    const item = button('', () => { pane.querySelectorAll('button').forEach(b => b.classList.remove('selected')); item.classList.add('selected'); explanation.textContent = node.detail; });
    item.append(el('span', learning.categories[node.category] || node.category, 'category'), el('strong', labels.get(node.id)));
    if (node.id === focus) { item.classList.add('selected'); explanation.textContent = node.detail; }
    pane.append(item);
  }
  pane.append(explanation);
  const relations = {belegtDurch:'belegt durch', informiert:'informiert', erfordert:'erfordert'};
  for (const edge of learning.example.edges) pane.append(el('p', `${labels.get(edge.from)} → ${relations[edge.relation] || edge.relation} → ${labels.get(edge.to)}`, 'relationship'));
  return pane;
}
function renderSlide(slide, printable = false) {
  const article = el('article', '', printable ? 'print-slide' : 'slide'); article.dataset.slide = slide.id;
  article.append(el('h1', slide.title));
  const body = el('div', '', 'slide-body'), text = el('section', '', 'slide-text');
  text.append(el('p', slide.text)); const steps = el('ol', '', 'steps'); slide.steps.forEach(step => steps.append(el('li', step))); text.append(steps);
  if (!printable) text.append(button('Bezeichnung üben', openPractice));
  const quiz = el('section', '', 'quiz'); quiz.append(el('h2', slide.question));
  if (printable) { quiz.append(el('p', slide.choices[slide.answer]), el('p', slide.explanation)); }
  else {
    const choices = el('div', '', 'choices'), feedback = el('p', '', 'feedback'); feedback.setAttribute('role', 'status');
    slide.choices.forEach((choice, choiceIndex) => choices.append(button(choice, () => { stop(); feedback.textContent = (choiceIndex === slide.answer ? 'Richtig. ' : 'Versuche es noch einmal. ') + slide.explanation; })));
    quiz.append(choices, feedback);
  }
  text.append(quiz); body.append(text, model(slide.focus)); article.append(body); return article;
}
function renderChapter(chapter, printable = false) {
  const article = el('article', '', printable ? 'print-slide' : 'chapter'); article.dataset.chapter = chapter.id;
  article.append(el('h1', chapter.title)); chapter.paragraphs.forEach(text => article.append(el('p', text)));
  const steps = el('ol'); chapter.steps.forEach(step => steps.append(el('li', step))); article.append(steps);
  const table = el('table'); const caption = el('caption', 'Begriffe und Hinweise'); table.append(caption);
  chapter.facts.forEach(([label, text]) => { const row = el('tr'), heading = el('th', label); heading.scope = 'row'; row.append(heading, el('td', text)); table.append(row); });
  article.append(table); return article;
}
function render() {
  $('training-mode').setAttribute('aria-pressed', String(mode === 'training')); $('handbook-mode').setAttribute('aria-pressed', String(mode === 'handbook'));
  $('sections').replaceChildren(); $('nav-title').textContent = mode === 'training' ? 'Lektionen' : 'Kapitel';
  const items = mode === 'training' ? learning.course.lessons : chapters;
  items.forEach((item, itemIndex) => {
    const nav = button(item.title, () => { stop(); if (mode === 'training') index = slides.findIndex(slide => slide.lesson.id === item.id); else chapterIndex = itemIndex; render(); });
    if (mode === 'training' ? slides[index].lesson.id === item.id : chapterIndex === itemIndex) nav.setAttribute('aria-current', 'page');
    $('sections').append(nav);
  });
  $('content').replaceChildren(mode === 'training' ? renderSlide(slides[index]) : renderChapter(chapters[chapterIndex])); $('content').scrollTop = 0;
  const current = mode === 'training' ? index : chapterIndex, total = mode === 'training' ? slides.length : chapters.length;
  $('position').textContent = `${mode === 'training' ? 'Folie' : 'Kapitel'} ${current + 1} von ${total}`;
  $('previous').disabled = current === 0; $('next').disabled = current === total - 1; $('play').hidden = mode !== 'training';
  document.dispatchEvent(new Event('learning-change'));
}
function move(delta) { if (mode === 'training') index = Math.max(0, Math.min(slides.length - 1, index + delta)); else chapterIndex = Math.max(0, Math.min(chapters.length - 1, chapterIndex + delta)); render(); }
function openPractice() { stop(); $('practice-label').value = labels.get('local.schutz'); $('practice-diff').hidden = true; $('practice-result').textContent = ''; $('practice').showModal(); }
$('practice-preview').addEventListener('click', () => {
  const value = $('practice-label').value.trim(); if (!value) { $('practice-result').textContent = 'Bitte eine Bezeichnung eingeben.'; $('practice-diff').hidden = true; return; }
  $('practice-before').textContent = 'Bisher: ' + labels.get('local.schutz'); $('practice-after').textContent = 'Neu: ' + value; $('practice-diff').hidden = false;
});
$('practice-label').addEventListener('input', () => { $('practice-diff').hidden = true; });
$('practice-confirm').addEventListener('click', () => { labels.set('local.schutz', $('practice-label').value.trim()); $('practice-diff').hidden = true; $('practice-result').textContent = 'Nur das künstliche Beispiel im Browser wurde geändert. Neu laden setzt es zurück.'; render(); });
$('training-mode').addEventListener('click', () => { stop(); mode = 'training'; render(); });
$('handbook-mode').addEventListener('click', () => { stop(); mode = 'handbook'; render(); });
$('previous').addEventListener('click', () => { stop(); move(-1); }); $('next').addEventListener('click', () => { stop(); move(1); });
$('play').addEventListener('click', () => { if (timer) { stop(); return; } if (index === slides.length - 1) { index = 0; render(); } $('play').textContent = 'Anhalten'; timer = setInterval(() => { if (index === slides.length - 1) stop(); else move(1); }, 15000); });
$('print').addEventListener('click', () => { stop(); $('print-content').replaceChildren(...(mode === 'training' ? slides.map(slide => renderSlide(slide, true)) : chapters.map(chapter => renderChapter(chapter, true)))); window.print(); });
document.addEventListener('keydown', event => { if ($('practice').open || /INPUT|TEXTAREA|SELECT/.test(event.target.tagName)) return; if (['ArrowRight', 'ArrowLeft'].includes(event.key)) { event.preventDefault(); stop(); move(event.key === 'ArrowRight' ? 1 : -1); } });
render();
