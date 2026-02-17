;(() => {
  const applyTheme = (name) => {
    const map = {
      'dark-blue': { bs: 'dark', rsc: 'dark-blue' },
      'dark-amber': { bs: 'dark', rsc: 'dark-amber' },
      'light': { bs: 'light', rsc: 'light' },
      'high-contrast': { bs: 'dark', rsc: 'high-contrast' },
      'terminal': { bs: 'dark', rsc: 'terminal' },
    }
    const cfg = map[name] || map['dark-blue']
    document.documentElement.setAttribute('data-bs-theme', cfg.bs)
    document.documentElement.setAttribute('data-rsc-theme', cfg.rsc)
    try { localStorage.setItem('rsc-theme', name) } catch (_) {}
  }
  try {
    const saved = localStorage.getItem('rsc-theme') || 'dark-blue'
    applyTheme(saved)
  } catch (_) { applyTheme('dark-blue') }
  document.querySelectorAll('.theme-option').forEach(a => {
    a.addEventListener('click', (e) => {
      e.preventDefault()
      const name = a.getAttribute('data-theme')
      if (name) applyTheme(name)
    })
  })
  const filter = document.getElementById('filesFilter')
  if (filter) {
    filter.addEventListener('input', () => {
      const val = filter.value.toLowerCase()
      document.querySelectorAll('#filesTable tbody tr').forEach(tr => {
        const name = tr.getAttribute('data-name') || ''
        tr.style.display = name.includes(val) ? '' : 'none'
      })
    })
  }
  const copyBtn = document.getElementById('copyBtn')
  const codeText = document.getElementById('codeText')
  if (copyBtn && codeText) {
    copyBtn.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(codeText.textContent || '')
        copyBtn.classList.add('btn-success')
        setTimeout(() => copyBtn.classList.remove('btn-success'), 1000)
      } catch (_) {}
    })
  }
  const wrapBtn = document.getElementById('wrapBtn')
  if (wrapBtn && codeText) {
    wrapBtn.addEventListener('click', () => {
      const wrap = codeText.style.whiteSpace === 'pre-wrap'
      codeText.style.whiteSpace = wrap ? 'pre' : 'pre-wrap'
    })
  }
})()
