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
      const attending = answer('attending') === 'yes';
      toggle(form.querySelector('[data-field="party_size"]'), attending);
      toggle(document.getElementById('attendance-guests'), attending);
      if (attending) {
        const add = document.getElementById('add-guest');
        const guests = document.getElementById('guest-list');
        add.disabled = guests.children.length >= Number(guests.dataset.maxGuests);
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

  const snapshot = () => JSON.stringify([...new FormData(form)]);
  const initialAnswers = snapshot();
  const hasUnsavedSubmission = Boolean(form.querySelector('.error-summary'));
  const hasChanges = () => hasUnsavedSubmission || snapshot() !== initialAnswers;
  let leaving = false;

  form.addEventListener('submit', () => {
    leaving = true;
  });

  const confirmDeparture = event => {
    if (hasChanges() && !window.confirm(form.dataset.leaveMessage)) {
      event.preventDefault();
      return;
    }
    leaving = true;
  };
  document.querySelector('.language-switch').addEventListener('submit', confirmDeparture);
  document.addEventListener('click', event => {
    if (event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    const link = event.target.closest('a[href]');
    if (!link || (link.target && link.target !== '_self') || link.hasAttribute('download')) return;
    const url = new URL(link.href);
    const samePageAnchor = url.pathname === location.pathname && url.search === location.search && url.hash;
    if (url.origin !== location.origin || samePageAnchor) return;
    confirmDeparture(event);
  });
  window.addEventListener('beforeunload', event => {
    if (!leaving && hasChanges()) {
      event.preventDefault();
      event.returnValue = '';
    }
  });
  window.addEventListener('pageshow', () => {
    leaving = false;
  });
})();
