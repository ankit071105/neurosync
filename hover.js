document.addEventListener('pointermove', (e) => {
  document.querySelectorAll('.stButton>button').forEach(b => {
    b.style.setProperty('--x', e.clientX - b.getBoundingClientRect().left + 'px');
    b.style.setProperty('--y', e.clientY - b.getBoundingClientRect().top + 'px');
  });
  
  // Add hover effect to chips
  document.querySelectorAll('.chip').forEach(chip => {
    const rect = chip.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    chip.style.setProperty('--x', `${x}px`);
    chip.style.setProperty('--y', `${y}px`);
  });
  
  // Add hover effect to code action buttons
  document.querySelectorAll('.copy-btn, .run-btn').forEach(btn => {
    const rect = btn.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    btn.style.setProperty('--x', `${x}px`);
    btn.style.setProperty('--y', `${y}px`);
  });
});