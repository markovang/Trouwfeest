(() => {
  const list = document.getElementById('guest-list');
  if (!list) return;
  const add = document.getElementById('add-guest');
  const total = document.getElementById('id_guests-TOTAL_FORMS');
  const partySize = document.getElementById('id_party_size');
  const guestCount = document.getElementById('guest-count');
  const template = document.getElementById('guest-template');
  const status = document.getElementById('guest-status');
  const limit = Number(list.dataset.maxGuests);
  const update = () => {
    const cards = [...list.children];
    cards.forEach((card, index) => {
      card.querySelector('.guest-number').textContent = index + 1;
      card.querySelectorAll('input, label, [id]').forEach(element => {
        ['name', 'id', 'for', 'aria-describedby'].forEach(attribute => {
          if (element.hasAttribute(attribute)) {
            element.setAttribute(attribute, element.getAttribute(attribute).replace(/guests-(\d+|__prefix__)-/g, `guests-${index}-`));
          }
        });
      });
      card.querySelectorAll('input').forEach(input => {
        input.required = true;
      });
    });
    total.value = cards.length;
    partySize.value = cards.length + 1;
    guestCount.value = partySize.value;
    add.disabled = cards.length >= limit;
    status.textContent = cards.length >= limit ? list.dataset.limitMessage : '';
  };
  add.addEventListener('click', () => {
    if (list.children.length >= limit) return;
    const content = template.content.cloneNode(true);
    list.appendChild(content);
    update();
    list.lastElementChild.querySelector('input').focus();
  });
  list.addEventListener('click', event => {
    const button = event.target.closest('.remove-guest');
    if (!button) return;
    button.closest('.guest-card').remove();
    update();
    add.focus();
  });
  update();
  partySize.closest('[data-field="party_size"]').classList.add('has-derived-count');
  list.classList.add('has-remove-controls');
  document.getElementById('party-total').hidden = false;
  add.hidden = false;
})();
