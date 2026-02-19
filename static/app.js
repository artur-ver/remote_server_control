;(() => {
  const THEMES = [
    // Essentials
    { name: 'dark-blue', bs: 'dark', rsc: 'dark-blue' },
    { name: 'dark-amber', bs: 'dark', rsc: 'dark-amber' },
    { name: 'light', bs: 'light', rsc: 'light' },
    { name: 'high-contrast', bs: 'dark', rsc: 'high-contrast' },
    
    // Professional
    { name: 'nord', bs: 'dark', rsc: 'nord' },
    { name: 'dracula', bs: 'dark', rsc: 'dracula' },
    { name: 'solarized-dark', bs: 'dark', rsc: 'solarized-dark' },
    { name: 'gruvbox-dark', bs: 'dark', rsc: 'gruvbox-dark' },
    { name: 'monokai', bs: 'dark', rsc: 'monokai' },

    // Hacker
    { name: 'terminal', bs: 'dark', rsc: 'terminal' },
    { name: 'matrix', bs: 'dark', rsc: 'matrix' },

    // Cyberpunk
    { name: 'cyberpunk', bs: 'dark', rsc: 'cyberpunk' },
    { name: 'cyberpunk-red', bs: 'dark', rsc: 'cyberpunk-red' },
    { name: 'cyberpunk-green', bs: 'dark', rsc: 'cyberpunk-green' },
    { name: 'cyberpunk-blue', bs: 'dark', rsc: 'cyberpunk-blue' },
  ]

  const applyTheme = (name) => {
    const cfg = THEMES.find(t => t.name === name) || THEMES[0]
    document.documentElement.setAttribute('data-bs-theme', cfg.bs)
    document.documentElement.setAttribute('data-rsc-theme', cfg.rsc)
    try { localStorage.setItem('rsc-theme', cfg.name) } catch (_) {}
    
    // Update active state in dropdown
    document.querySelectorAll('.theme-option').forEach(el => {
      if (el.getAttribute('data-theme') === cfg.name) {
        el.classList.add('active')
      } else {
        el.classList.remove('active')
      }
    })
  }

  const cycleTheme = (dir) => {
    const current = document.documentElement.getAttribute('data-rsc-theme') || 'dark-blue'
    let idx = THEMES.findIndex(t => t.rsc === current)
    if (idx === -1) idx = 0
    
    let nextIdx = idx + dir
    if (nextIdx >= THEMES.length) nextIdx = 0
    if (nextIdx < 0) nextIdx = THEMES.length - 1
    
    applyTheme(THEMES[nextIdx].name)
  }

  // Initial load
  try {
    const saved = localStorage.getItem('rsc-theme') || 'dark-blue'
    applyTheme(saved)
  } catch (_) { applyTheme('dark-blue') }

  // Dropdown click handlers
  document.querySelectorAll('.theme-option').forEach(a => {
    a.addEventListener('click', (e) => {
      e.preventDefault()
      const name = a.getAttribute('data-theme')
      if (name) applyTheme(name)
    })
  })

  // Prev/Next buttons
  const prevThemeBtn = document.getElementById('prevThemeBtn')
  const nextThemeBtn = document.getElementById('nextThemeBtn')
  if (prevThemeBtn) prevThemeBtn.addEventListener('click', (e) => { e.preventDefault(); e.stopPropagation(); cycleTheme(-1) })
  if (nextThemeBtn) nextThemeBtn.addEventListener('click', (e) => { e.preventDefault(); e.stopPropagation(); cycleTheme(1) })

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

  // Sorting logic
  const parseSize = (str) => {
    const match = str.trim().match(/^([\d.]+)\s*(B|KB|MB|GB|TB)$/i)
    if (!match) return null
    const val = parseFloat(match[1])
    const unit = match[2].toUpperCase()
    const units = { 'B': 1, 'KB': 1024, 'MB': 1024 ** 2, 'GB': 1024 ** 3, 'TB': 1024 ** 4 }
    return val * (units[unit] || 1)
  }

  const getVal = (tr, idx) => {
    const td = tr.children[idx]
    if (!td) return ''
    const txt = td.innerText.trim()
    if (!txt) return ''
    // Try size
    const size = parseSize(txt)
    if (size !== null) return size
    // Try strict number
    if (/^-?\d+(\.\d+)?$/.test(txt)) {
      return parseFloat(txt)
    }
    return txt.toLowerCase()
  }

  document.querySelectorAll('table').forEach(table => {
    const ths = table.querySelectorAll('thead th')
    ths.forEach((th, idx) => {
      th.addEventListener('click', () => {
        const tbody = table.querySelector('tbody')
        if (!tbody) return
        const rows = Array.from(tbody.querySelectorAll('tr'))
        const asc = !th.classList.contains('asc')

        rows.sort((a, b) => {
          const v1 = getVal(a, idx)
          const v2 = getVal(b, idx)

          if (typeof v1 === 'number' && typeof v2 === 'number') {
            return asc ? v1 - v2 : v2 - v1
          }
          const s1 = String(v1)
          const s2 = String(v2)
          return asc
            ? s1.localeCompare(s2, undefined, { numeric: true, sensitivity: 'base' })
            : s2.localeCompare(s1, undefined, { numeric: true, sensitivity: 'base' })
        })

        rows.forEach(r => tbody.appendChild(r))
        ths.forEach(t => t.classList.remove('asc', 'desc'))
        th.classList.add(asc ? 'asc' : 'desc')
      })
    })
  })
})()
