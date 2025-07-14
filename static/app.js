document.getElementById("add-category-btn").addEventListener("click", function () {
    document.getElementById("add-category-modal").style.display = "block";
  });
  
  document.getElementById("close-modal").addEventListener("click", function () {
    document.getElementById("add-category-modal").style.display = "none";
  });
  
  document.getElementById("add-category-form").addEventListener("submit", function (event) {
    event.preventDefault();
  
    const title = document.getElementById("category-title").value;
    const image = document.getElementById("category-image").value;
  
    const categoriesContainer = document.getElementById("categories-container");
  
    const newCategory = document.createElement("div");
    newCategory.className = "category";
  
    const categoryImage = document.createElement("div");
    categoryImage.className = "image";
    categoryImage.style.backgroundImage = `url(${image})`;
  
    const categoryTitle = document.createElement("p");
    categoryTitle.textContent = title;
  
    newCategory.appendChild(categoryImage);
    newCategory.appendChild(categoryTitle);
  
    categoriesContainer.appendChild(newCategory);
  
    document.getElementById("add-category-modal").style.display = "none";
    document.getElementById("add-category-form").reset();
  });
  // Mobile menu toggle
document.getElementById('hamburger').addEventListener('click', function() {
  const navMenu = document.getElementById('navMenu');
  navMenu.classList.toggle('active');
});

// Animate elements when they come into view
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('animate-fade');
    }
  });
}, { threshold: 0.1 });

// Observe all elements with the 'animate-on-scroll' class
document.querySelectorAll('.category, .about-section, .contact-section').forEach(el => {
  observer.observe(el);
});
