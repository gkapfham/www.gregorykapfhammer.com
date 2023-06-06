<script type="module">
  // import the rough notation module
  import { annotate, annotationGroup } from 'https://unpkg.com/rough-notation?module';
  // define a highlight that will be a mutiple-line underline that appears for all annotated text
  const config = { type: 'underline', multiline: true, iterations: 1, strokeWidth: 4, animationDuration: 200, color: '#EF6C00' };
  // const n1 = document.querySelectorAll('.abstract .special');
  const n1 = document.querySelectorAll('.special');
  // const n1 = document.querySelector('.abstract span');
  // const a1 = annotate(n1, config);
  var al = []
  for (let i = 0; i < n1.length; i++) {
    var newA = annotate(n1[i], config);
    al.push(newA)
  }
  // Get the checkbox element
  var toggleButtonCheckbox = document.getElementById('toggle-button-checkbox');
  // Function to toggle the rough notation
  function toggleRoughNotation() {
    if (toggleButtonCheckbox.checked) {
      for (let i = 0; i < al.length; i++) {
        var newA = al[i];
        newA.hide();
        newA.show();
      }
    } else {
      for (let i = 0; i < al.length; i++) {
        var newA = al[i];
        newA.hide();
      }
    }
  }
  // Add event listener to the checkbox
  toggleButtonCheckbox.addEventListener('change', toggleRoughNotation);
</script>
