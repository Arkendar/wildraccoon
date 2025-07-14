document.addEventListener('DOMContentLoaded', function() {
    // 1. Обработка сохраненной категории
    const selectedCategory = localStorage.getItem('selectedCategory');
    if (selectedCategory) {
        const targetSection = document.getElementById(selectedCategory);
        if (targetSection) {
            document.querySelectorAll('.accordion-item').forEach(item => {
                item.classList.remove('active');
            });
            targetSection.classList.add('active');
            
            // Добавьте задержку для гарантии отрисовки
            setTimeout(() => {
                targetSection.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start',
                    inline: 'nearest'
                });
            }, 300);
            
            localStorage.removeItem('selectedCategory');
        }
    }

    // 2. Инициализация аккордеона
    const accordionItems = document.querySelectorAll('.accordion-item');
    accordionItems.forEach(item => {
        const header = item.querySelector('.accordion-header');
        header.addEventListener('click', () => {
            accordionItems.forEach(otherItem => {
                if (otherItem !== item) otherItem.classList.remove('active');
            });
            item.classList.toggle('active');
        });
    });

    // 3. Инициализация слайдеров
       const sliders = document.querySelectorAll('.slider');
    
    sliders.forEach(slider => {
        const slides = slider.querySelectorAll('.slide');
        const indicators = slider.querySelectorAll('.indicator');
        let currentSlide = 0;
        
        // Показываем первый слайд
        slides[currentSlide].classList.add('active');
        if (indicators.length > 0) indicators[currentSlide].classList.add('active');
        
        // Находим кнопки
        const prevBtn = slider.querySelector('.prev');
        const nextBtn = slider.querySelector('.next');
        
        // Обработчики
        prevBtn.onclick = () => changeSlide(slider, -1);
        nextBtn.onclick = () => changeSlide(slider, 1);
    });

    function changeSlide(slider, direction) {
        const slides = slider.querySelectorAll('.slide');
        const indicators = slider.querySelectorAll('.indicator');
        let currentSlide = 0;
        
        // Находим текущий слайд
        slides.forEach((slide, index) => {
            if (slide.classList.contains('active')) {
                currentSlide = index;
                slide.classList.remove('active');
                if (indicators.length > index) {
                    indicators[index].classList.remove('active');
                }
            }
        });
        
        // Вычисляем новый индекс
        let newSlide = currentSlide + direction;
        if (newSlide < 0) newSlide = slides.length - 1;
        if (newSlide >= slides.length) newSlide = 0;
        
        // Показываем новый слайд
        slides[newSlide].classList.add('active');
        if (indicators.length > newSlide) {
            indicators[newSlide].classList.add('active');
        }
    }
});