// simple chat client using fetch + CSRF
(function(){
  const toggle = document.getElementById('edu-ai-toggle');
  const panel = document.getElementById('edu-ai-panel');
  const closeBtn = document.getElementById('edu-ai-close');
  const form = document.getElementById('edu-ai-form');
  const input = document.getElementById('edu-ai-input');
  const messages = document.getElementById('edu-ai-messages');

  toggle.addEventListener('click', () => panel.classList.toggle('hidden'));
  closeBtn.addEventListener('click', () => panel.classList.add('hidden'));

  function addMessage(who, text) {
    const el = document.createElement('div');
    el.className = who === 'user' ? "text-right mb-2" : "text-left mb-2";
    el.innerHTML = `<div class="inline-block p-2 rounded ${who==='user'?'bg-blue-100':'bg-gray-100'}">${text}</div>`;
    messages.appendChild(el);
    messages.scrollTop = messages.scrollHeight;
  }

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
  const csrf = getCookie('csrftoken');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    addMessage('user', text);
    input.value = '';
    addMessage('system', 'Escribiendo…');

    try {
      const resp = await fetch('/ai/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrf
        },
        body: JSON.stringify({message: text})
      });
      const j = await resp.json();
      // quitar "Escribiendo…"
      const sys = messages.querySelectorAll('.system');
      // not robust but ok
      messages.lastChild.remove();
      if (j.reply) addMessage('assistant', j.reply);
      else addMessage('assistant', j.error || 'Error en la respuesta');
    } catch (err) {
      messages.lastChild.remove();
      addMessage('assistant', 'Error de red. Intenta de nuevo.');
    }
  });

})();
