/* ===== ДАННЫЕ ТОВАРОВ ===== */
const PRODUCTS = [
  { id: 'slider1', category: 'gazebos', size: '2.5x2.5', title: 'Беседки 2,5х2,5м',      type: 'standard' },
  { id: 'slider2', category: 'gazebos', size: '3x3',     title: 'Беседки 3х3м',           type: 'standard' },
  { id: 'slider3', category: 'gazebos', size: '3x4',     title: 'Беседки 3х4м',           type: 'standard' },
  { id: 'slider4', category: 'gazebos', size: '3x5',     title: 'Беседки 3х5м',           type: 'standard' },
  { id: 'slider5', category: 'gazebos', size: '4x4',     title: 'Беседки 4х4м',           type: 'standard' },
  { id: 'slider6', category: 'gazebos', size: '4x5',     title: 'Беседки 4х5м',           type: 'standard' },
  { id: 'slider7', category: 'gazebos', size: '4x6',     title: 'Беседки 4х6м',           type: 'standard' },
  { id: 'slider8', category: 'gazebos', size: null,      title: 'Нестандартные беседки',  type: 'custom'   },
];

const CATEGORY_LABELS = {
  gazebos:  'Беседки',
  houses:   'Дома',
  baths:    'Бани',
  plots:    'Участки',
  products: 'Изделия',
};

const CATEGORY_SECTION = {
  gazebos:  'gazebos-section',
  houses:   'houses-section',
  baths:    'baths-section',
  plots:    'plots-section',
  products: 'products-section',
};

/* ===== НОРМАЛИЗАЦИЯ ДЛЯ ПОИСКА ===== */
function normalize(str) {
  return str
    .toLowerCase()
    .replace(/х/g, 'x')
    .replace(/\*/g, 'x')
    .replace(/\s+/g, ' ')
    .trim();
}

function matchProducts(query) {
  const q = normalize(query);
  if (!q) return [];
  return PRODUCTS.filter(p => normalize(p.title).includes(q));
}

function highlightMatch(title, query) {
  const normTitle = normalize(title);
  const normQuery = normalize(query);
  const idx = normTitle.indexOf(normQuery);
  if (idx === -1) return title;
  return title.slice(0, idx) +
    `<mark>${title.slice(idx, idx + query.length)}</mark>` +
    title.slice(idx + query.length);
}

/* ===== АККОРДЕОН ===== */
function initAccordion() {
  document.querySelectorAll('.accordion-header').forEach(header => {
    header.addEventListener('click', () => {
      const item = header.parentElement;
      const isActive = item.classList.contains('active');
      document.querySelectorAll('.accordion-item').forEach(i => i.classList.remove('active'));
      if (!isActive) item.classList.add('active');
      // rebind lightbox for newly visible images
      setTimeout(() => { if (window._lbBind) window._lbBind(); }, 50);
    });
  });
}

/* ===== СЛАЙДЕР ===== */
function getSlides(sliderId) {
  return document.querySelectorAll(`#${sliderId} .slide`);
}

function showSlide(sliderId, index) {
  const slides = getSlides(sliderId);
  if (!slides.length) return;
  slides.forEach(s => s.classList.remove('active'));
  const i = (index + slides.length) % slides.length;
  slides[i].classList.add('active');
  const indicators = document.querySelectorAll(`#${sliderId} .indicator`);
  indicators.forEach((dot, j) => dot.classList.toggle('active', j === i));
}

function currentSlideIndex(sliderId) {
  const slides = getSlides(sliderId);
  for (let i = 0; i < slides.length; i++) {
    if (slides[i].classList.contains('active')) return i;
  }
  return 0;
}

window.prevSlide = id => showSlide(id, currentSlideIndex(id) - 1);
window.nextSlide = id => showSlide(id, currentSlideIndex(id) + 1);

function initIndicators() {
  document.querySelectorAll('.slider').forEach(slider => {
    const slides = slider.querySelectorAll('.slide');
    if (slides.length <= 1) return;
    const wrap = document.createElement('div');
    wrap.className = 'slider-indicators';
    slides.forEach((_, i) => {
      const dot = document.createElement('div');
      dot.className = 'indicator' + (i === 0 ? ' active' : '');
      dot.addEventListener('click', () => showSlide(slider.id, i));
      wrap.appendChild(dot);
    });
    slider.appendChild(wrap);
  });
}

/* ===== ПОИСК ===== */
function initSearch() {
  document.querySelectorAll('.search input').forEach(input => {
    const wrapper = input.closest('.search-container');
    if (!wrapper) return;

    const dropdown = document.createElement('div');
    dropdown.className = 'search-dropdown';
    wrapper.appendChild(dropdown);

    function renderDropdown(query) {
      dropdown.innerHTML = '';
      if (!query) { dropdown.classList.remove('open'); return; }

      const matched = matchProducts(query);

      if (!matched.length) {
        dropdown.innerHTML = '<div class="search-no-results">Ничего не найдено</div>';
        dropdown.classList.add('open');
        return;
      }

      matched.forEach(p => {
        const item = document.createElement('div');
        item.className = 'search-item';
        item.innerHTML = `
          <span class="search-item-cat">${CATEGORY_LABELS[p.category]}</span>
          <span class="search-item-title">${highlightMatch(p.title, query)}</span>
        `;
        item.addEventListener('mousedown', e => {
          e.preventDefault();
          input.value = p.title;
          dropdown.classList.remove('open');
          goToProduct(p);
        });
        dropdown.appendChild(item);
      });

      dropdown.classList.add('open');
    }

    input.addEventListener('input', () => renderDropdown(input.value.trim()));

    input.addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        const matched = matchProducts(input.value.trim());
        dropdown.classList.remove('open');
        if (matched.length) goToProduct(matched[0]);
      }
      if (e.key === 'Escape') dropdown.classList.remove('open');
    });

    input.addEventListener('blur', () => {
      setTimeout(() => dropdown.classList.remove('open'), 150);
    });

    const btn = wrapper.querySelector('button:not(.search-filters)');
    if (btn) {
      btn.addEventListener('click', () => {
        const matched = matchProducts(input.value.trim());
        dropdown.classList.remove('open');
        if (matched.length) goToProduct(matched[0]);
      });
    }
  });
}

function goToProduct(product) {
  if (window.location.pathname.includes('katalog')) {
    scrollToProduct(product);
  } else {
    localStorage.setItem('searchTarget', JSON.stringify(product));
    window.location.href = '/static/templates/katalog.html';
  }
}

function scrollToProduct(product) {
  const sectionId = CATEGORY_SECTION[product.category];
  document.querySelectorAll('.accordion-item').forEach(i => i.classList.remove('active'));
  const section = document.getElementById(sectionId);
  const accordionItem = section?.closest('.accordion-item') || section;
  if (accordionItem) accordionItem.classList.add('active');

  setTimeout(() => {
    const slider = document.getElementById(product.id);
    const target = slider?.closest('.slider-container') || section;
    if (!target) return;
    target.scrollIntoView({ behavior: 'smooth', block: 'center' });
    target.classList.add('search-highlight');
    setTimeout(() => target.classList.remove('search-highlight'), 2200);
  }, 350);
}

/* ===== ФИЛЬТРЫ ===== */
let activeFilters = { categories: [], sizes: [], types: [] };

function initFilters() {
  const filterBtn = document.querySelector('.search-filters');
  if (!filterBtn) return;

  const panel = document.createElement('div');
  panel.className = 'filter-panel';
  panel.innerHTML = `
    <div class="filter-panel-inner">
      <div class="filter-header">
        <h3>Фильтры</h3>
        <button class="filter-close" aria-label="Закрыть">&times;</button>
      </div>
      <div class="filter-group">
        <div class="filter-group-title">Категория</div>
        <div class="filter-options" id="fc-category">
          ${Object.entries(CATEGORY_LABELS).map(([val, label]) =>
            `<label class="filter-chip"><input type="checkbox" name="category" value="${val}">${label}</label>`
          ).join('')}
        </div>
      </div>
      <div class="filter-group">
        <div class="filter-group-title">Размер</div>
        <div class="filter-options" id="fc-size">
          ${['2.5x2.5','3x3','3x4','3x5','4x4','4x5','4x6'].map(s =>
            `<label class="filter-chip"><input type="checkbox" name="size" value="${s}">${s.replace('x','×')} м</label>`
          ).join('')}
        </div>
      </div>
      <div class="filter-group">
        <div class="filter-group-title">Тип</div>
        <div class="filter-options" id="fc-type">
          <label class="filter-chip"><input type="checkbox" name="type" value="standard">Стандартные</label>
          <label class="filter-chip"><input type="checkbox" name="type" value="custom">Нестандартные</label>
        </div>
      </div>
      <div class="filter-actions">
        <button class="filter-reset">Сбросить</button>
        <button class="filter-apply">Применить</button>
      </div>
    </div>
  `;
  document.body.appendChild(panel);

  filterBtn.addEventListener('click', e => { e.stopPropagation(); panel.classList.toggle('open'); });
  panel.querySelector('.filter-close').addEventListener('click', () => panel.classList.remove('open'));
  document.addEventListener('click', e => {
    if (!panel.contains(e.target) && e.target !== filterBtn) panel.classList.remove('open');
  });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') panel.classList.remove('open'); });

  panel.querySelector('.filter-reset').addEventListener('click', () => {
    panel.querySelectorAll('input[type=checkbox]').forEach(cb => cb.checked = false);
    activeFilters = { categories: [], sizes: [], types: [] };
    applyFilters();
    updateBadge(filterBtn);
  });

  panel.querySelector('.filter-apply').addEventListener('click', () => {
    activeFilters.categories = [...panel.querySelectorAll('input[name=category]:checked')].map(cb => cb.value);
    activeFilters.sizes      = [...panel.querySelectorAll('input[name=size]:checked')].map(cb => cb.value);
    activeFilters.types      = [...panel.querySelectorAll('input[name=type]:checked')].map(cb => cb.value);
    applyFilters();
    updateBadge(filterBtn);
    panel.classList.remove('open');
  });
}

function applyFilters() {
  const { categories, sizes, types } = activeFilters;
  const hasFilters = categories.length || sizes.length || types.length;

  if (!hasFilters) {
    document.querySelectorAll('.slider-container').forEach(el => el.style.display = '');
    document.querySelectorAll('.accordion-item').forEach(el => el.style.display = '');
    return;
  }

  PRODUCTS.forEach(p => {
    const catOk  = !categories.length || categories.includes(p.category);
    const sizeOk = !sizes.length      || (p.size && sizes.includes(p.size));
    const typeOk = !types.length      || types.includes(p.type);
    const sliderEl = document.getElementById(p.id);
    if (!sliderEl) return;
    const container = sliderEl.closest('.slider-container');
    if (container) container.style.display = (catOk && sizeOk && typeOk) ? '' : 'none';
  });

  document.querySelectorAll('.accordion-item').forEach(item => {
    const visible = item.querySelectorAll('.slider-container:not([style*="display: none"])').length;
    item.style.display = visible ? '' : 'none';
  });
}

function updateBadge(btn) {
  const count = activeFilters.categories.length + activeFilters.sizes.length + activeFilters.types.length;
  let badge = btn.querySelector('.filter-badge');
  if (count > 0) {
    if (!badge) { badge = document.createElement('span'); badge.className = 'filter-badge'; btn.appendChild(badge); }
    badge.textContent = count;
  } else {
    badge?.remove();
  }
}

/* ===== ПЕРЕХОД С ГЛАВНОЙ ===== */
function handleSearchTarget() {
  const raw = localStorage.getItem('searchTarget');
  if (!raw) return;
  localStorage.removeItem('searchTarget');
  try { scrollToProduct(JSON.parse(raw)); } catch {}
}

function handleCategoryTarget() {
  const cat = localStorage.getItem('selectedCategory');
  if (!cat) return;
  localStorage.removeItem('selectedCategory');
  const section = document.getElementById(cat);
  const item = section?.closest('.accordion-item') || section;
  if (item) {
    item.classList.add('active');
    setTimeout(() => item.scrollIntoView({ behavior: 'smooth', block: 'start' }), 300);
  }
}

/* ===== ВОССТАНОВЛЕНИЕ ФИЛЬТРОВ С ГЛАВНОЙ ===== */
function handleIncomingFilters() {
  const raw = localStorage.getItem('catalogFilters');
  if (!raw) return;
  localStorage.removeItem('catalogFilters');
  try {
    const incoming = JSON.parse(raw);
    const total = (incoming.categories?.length || 0) + (incoming.sizes?.length || 0) + (incoming.types?.length || 0);
    if (total === 0) return;

    // Проставляем чекбоксы в панели фильтров
    if (incoming.categories?.length) {
      incoming.categories.forEach(val => {
        const cb = document.querySelector(`#fc-category input[value="${val}"]`);
        if (cb) cb.checked = true;
      });
    }
    if (incoming.sizes?.length) {
      incoming.sizes.forEach(val => {
        const cb = document.querySelector(`#fc-size input[value="${val}"]`);
        if (cb) cb.checked = true;
      });
    }
    if (incoming.types?.length) {
      incoming.types.forEach(val => {
        const cb = document.querySelector(`#fc-type input[value="${val}"]`);
        if (cb) cb.checked = true;
      });
    }

    // Применяем фильтры
    activeFilters = incoming;
    applyFilters();

    // Обновляем бейдж
    const btn = document.querySelector('.search-filters');
    if (btn) updateBadge(btn);
  } catch {}
}

/* ===== ИНИЦИАЛИЗАЦИЯ ===== */
document.addEventListener('DOMContentLoaded', () => {
  initAccordion();
  initIndicators();
  initSearch();
  initFilters();
  handleIncomingFilters();
  handleSearchTarget();
  handleCategoryTarget();
});