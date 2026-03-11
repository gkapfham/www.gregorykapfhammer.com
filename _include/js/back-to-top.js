<script>
// Back to Top Button functionality
(function() {
  const backToTopButton = document.getElementById('back-to-top');
  
  if (!backToTopButton) return;
  
  // Show/hide button based on scroll position
  function toggleBackToTop() {
    if (window.pageYOffset > 300) {
      backToTopButton.classList.add('visible');
    } else {
      backToTopButton.classList.remove('visible');
    }
  }
  
  // Smooth scroll to top
  function scrollToTop(e) {
    e.preventDefault();
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  }
  
  // Event listeners
  window.addEventListener('scroll', toggleBackToTop, { passive: true });
  backToTopButton.addEventListener('click', scrollToTop);
  
  // Initial check
  toggleBackToTop();
})();
</script>
