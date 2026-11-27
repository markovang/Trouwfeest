(() => {
  const form = document.getElementById('registration-form');
  if (!form) return;
  const answer = name => form.querySelector(`[name="${name}"]:checked`)?.value;
  const toggle = (element, visible) => {
    if (!element) return;
    element.hidden = !visible;
    element.querySelectorAll('input, select, textarea, button').forEach(input => {
      input.disabled = !visible;
    });
  };
  const refresh = () => {
    if (form.elements.attending) {
      const attending = answer('attending') !== 'no';
      toggle(form.querySelector('[data-field="party_size"]'), attending);
      toggle(document.getElementById('attendance-guests'), attending);
      if (attending) {
        const add = document.getElementById('add-guest');
        add.disabled = document.getElementById('guest-list').children.length >= 10;
      }
    }
    if (form.elements.accommodation_help) {
      const needsHelp = answer('accommodation_help') !== 'no';
      ['accommodation_people', 'accommodation_nights', 'accommodation_preference'].forEach(name => {
        toggle(form.querySelector(`[data-field="${name}"]`), needsHelp);
      });
    }
    if (form.elements.travel_method) {
      const method = form.elements.travel_method.value;
      toggle(form.querySelector('[data-field="travel_other"]'), method === 'other');
      toggle(form.querySelector('[data-field="carpool_available"]'), method === 'car');
    }
  };
  form.addEventListener('change', refresh);
  refresh();
})();
