const select = (s, root = document) => root.querySelector(s);
const all = (s, root = document) => [...root.querySelectorAll(s)];
const menu = select('#mobile-menu');
const toggle = select('[data-menu-toggle]');
toggle?.addEventListener('click', () => {
  const open = toggle.getAttribute('aria-expanded') !== 'true';
  toggle.setAttribute('aria-expanded', String(open));
  menu.hidden = !open;
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && menu && !menu.hidden) {
    menu.hidden = true;
    toggle.setAttribute('aria-expanded', 'false');
    toggle.focus();
  }
});
const cards = all('[data-episode-card]');
const search = select('[data-episode-search]');
let currentGroup = 'all';
function filterEpisodes() {
  const query = (search?.value || '').trim().toLocaleLowerCase();
  let count = 0;
  for (const card of cards) {
    const matchesGroup = currentGroup === 'all' || card.dataset.group === currentGroup;
    const matchesQuery = !query || card.dataset.search.toLocaleLowerCase().includes(query);
    card.hidden = !(matchesGroup && matchesQuery);
    count += !card.hidden;
  }
  const result = select('[data-result-count]');
  if (result) result.textContent = document.documentElement.lang === 'zh-CN' ? `显示 ${count} / 32 集` : `${count} of 32 episodes`;
  const empty = select('[data-empty]');
  if (empty) empty.hidden = count > 0;
}
all('[data-filter]').forEach(button => {
  button.addEventListener('click', () => {
    currentGroup = button.dataset.filter;
    all('[data-filter]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
    filterEpisodes();
  });
});
search?.addEventListener('input', filterEpisodes);
const reader = select('.reader-content');
if (reader) {
  // Preferences are local-only; the complete chapter is already in the HTML.
  let size = 19;
  function applySize(next) {
    size = Math.max(16, Math.min(26, next));
    reader.style.setProperty('--reading-size', `${size}px`);
    try { localStorage.setItem('snowmoon:font-size', String(size)); } catch {}
  }
  try {
    const stored = Number(localStorage.getItem('snowmoon:font-size'));
    if (stored >= 16 && stored <= 26) applySize(stored);
    if (localStorage.getItem('snowmoon:reader-dark') === 'true') document.body.classList.add('reader-dark');
  } catch {}
  select('[data-font-smaller]')?.addEventListener('click', () => applySize(size - 1));
  select('[data-font-larger]')?.addEventListener('click', () => applySize(size + 1));
  const theme = select('[data-reader-theme]');
  theme?.setAttribute('aria-pressed', String(document.body.classList.contains('reader-dark')));
  theme?.addEventListener('click', () => {
    const dark = document.body.classList.toggle('reader-dark');
    theme.setAttribute('aria-pressed', String(dark));
    try { localStorage.setItem('snowmoon:reader-dark', String(dark)); } catch {}
  });
  function progress() {
    const start = reader.offsetTop;
    const max = Math.max(1, reader.scrollHeight - window.innerHeight);
    const amount = Math.min(100, Math.max(0, (window.scrollY - start) / max * 100));
    select('[data-reading-progress]').style.width = `${amount}%`;
  }
  window.addEventListener('scroll', progress, {passive:true});
  window.addEventListener('resize', progress, {passive:true});
  progress();
}
