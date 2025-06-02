(async () => {
  const grid = document.getElementById('prompt-grid');
  const emptyState = document.getElementById('empty-state');
  const promptCount = document.getElementById('prompt-count');
  const fileCount = document.getElementById('file-count');
  const experimentBar = document.getElementById('experiment-bar');
  
  try {
    const basePath = window.location.pathname.startsWith('/strudel-jam/') ? '/strudel-jam' : '';
    const data = await fetch(`${basePath}/data/index.json`).then(r => r.json());

    if (data.length === 0) {
      grid.classList.add('hidden');
      emptyState.classList.remove('hidden');
      promptCount.innerHTML = 'EXPERIMENTS: <span class="blink text-red-600">0 FOUND</span>';
      fileCount.textContent = '0';
      return;
    }

    // Update counters with retro styling
    promptCount.innerHTML = `EXPERIMENTS: <span class="text-green-600">${data.length}</span>`;
    fileCount.textContent = data.length;
    
    // Animate experiment loading bar
    let progress = 0;
    const loadInterval = setInterval(() => {
      progress += 20;
      experimentBar.style.setProperty('--progress', Math.min(progress, 100) + '%');
      if (progress >= 100) clearInterval(loadInterval);
    }, 100);

    // Generate fake file sizes and attributes
    const generateFileSize = () => {
      const sizes = ['1.2KB', '3.4KB', '2.1KB', '892B', '4.7KB'];
      return sizes[Math.floor(Math.random() * sizes.length)];
    };

    const generateAttributes = (successRate) => {
      const base = 'r--';
      if (successRate === 100) return base + 'A'; // Archive
      if (successRate === 0) return base + 'H';   // Hidden (broken)
      return base + 'S'; // System
    };

    for (const prompt of data) {
      const row = document.createElement('a');
      row.href = `${basePath}/p/${prompt.promptSlug}.html`;
      row.className = `
        block hover:bg-blue-100 p-2 font-system text-xs flex items-center
        border-l-2 border-transparent hover:border-blue-500 transition-colors duration-200
        cursor-pointer
      `;
      
      const successCount = prompt.models.filter(m => m.success !== false).length;
      const successRate = prompt.models.length > 0 ? Math.round((successCount / prompt.models.length) * 100) : 0;
      const fileSize = generateFileSize();
      const attributes = generateAttributes(successRate);
      
      // Add selection behavior
      row.addEventListener('click', (e) => {
        e.preventDefault();
        // Remove selection from other rows
        document.querySelectorAll('#prompt-grid a').forEach(r => {
          r.classList.remove('bg-blue-600', 'text-white');
        });
        // Select this row
        row.classList.add('bg-blue-600', 'text-white');
        
        // Update status bar
        const statusBar = document.getElementById('status-bar-text');
        statusBar.textContent = `Selected: ${prompt.title.replace(/\s+/g, '_').toUpperCase()}.PROMPT`;
      });
      
      row.innerHTML = `
        <!-- File icon -->
        <div class="w-8 flex items-center justify-center flex-shrink-0">
          <div class="w-4 h-4 ${successRate === 100 ? 'bg-green-500' : successRate > 0 ? 'bg-yellow-500' : 'bg-red-500'} border border-gray-600 text-white text-xs flex items-center justify-center">
            ${successRate === 100 ? '♪' : successRate > 0 ? '⚠' : '✗'}
          </div>
        </div>
        
        <!-- File name with extension -->
        <div class="flex-1 flex items-center space-x-1 min-w-0">
          <span class="font-mono font-bold text-black truncate">
            ${prompt.title.replace(/\s+/g, '_').toUpperCase()}
          </span>
          <span class="font-mono text-blue-600 flex-shrink-0">.PROMPT</span>
        </div>
        
        <!-- File size -->
        <div class="w-16 sm:w-20 text-right font-mono hidden xs:block">
          ${fileSize}
        </div>
        
        <!-- Models count -->
        <div class="w-16 sm:w-24 text-center font-mono">
          ${prompt.models.length}
        </div>
        
        <!-- Success rate with status -->
        <div class="w-20 sm:w-24 text-center hidden sm:block">
          <span class="font-mono ${successRate === 100 ? 'text-green-600' : successRate > 0 ? 'text-yellow-600' : 'text-red-600'} font-bold">
            ${successRate}%
          </span>
        </div>
        
        <!-- Date in old format -->
        <div class="w-24 sm:w-32 text-center font-mono text-xs hidden md:block">
          ${new Date(prompt.dateRun).toLocaleDateString('en-US', {
            month: '2-digit',
            day: '2-digit', 
            year: '2-digit'
          })} ${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', hour12: false})}
        </div>
        
        <!-- File attributes -->
        <div class="w-16 text-center font-mono text-xs text-gray-600 hidden lg:block">
          ${attributes}
        </div>
      `;
      
      // Add authentic double-click handler
      let clickTimer = null;
      row.addEventListener('click', (e) => {
        if (clickTimer) {
          clearTimeout(clickTimer);
          clickTimer = null;
          
          // Double-click action - show loading effect
          e.preventDefault();
          row.style.backgroundColor = '#316AC5';
          row.style.color = 'white';
          
          // Add fake loading delay
          const statusBar = document.getElementById('status-bar-text');
          statusBar.textContent = 'Loading pattern analysis data...';
          
          setTimeout(() => {
            statusBar.textContent = 'Initializing neural comparison matrix...';
            setTimeout(() => {
              window.location.href = row.href;
            }, 500);
          }, 300);
        } else {
          clickTimer = setTimeout(() => {
            clickTimer = null;
            // Single click - just select
          }, 300);
        }
      });
      
      // Add context menu simulation
      row.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        const statusBar = document.getElementById('status-bar-text');
        statusBar.textContent = 'Right-click menu: Analyze, Properties, Export (simulation)';
        setTimeout(() => {
          statusBar.textContent = 'Ready';
        }, 2000);
      });
      
      grid.append(row);
    }

    // Add some random "background processes"
    setTimeout(() => {
      const statusBar = document.getElementById('status-bar-text');
      const messages = [
        'Indexing pattern database...',
        'Analyzing creative signatures...',
        'Checking neural coherence...',
        'Scanning for anomalies...',
        'Optimizing pattern recognition...',
        'Ready'
      ];
      
      let msgIndex = 0;
      const statusInterval = setInterval(() => {
        if (msgIndex < messages.length - 1) {
          statusBar.textContent = messages[msgIndex];
          msgIndex++;
        } else {
          clearInterval(statusInterval);
          statusBar.textContent = 'Ready';
        }
      }, 1500);
    }, 3000);

  } catch (e) {
    grid.classList.add('hidden');
    emptyState.classList.remove('hidden');
    promptCount.innerHTML = 'EXPERIMENTS: <span class="blink text-red-600">ERROR</span>';
    fileCount.textContent = '0';
    console.error('Failed to load prompt data:', e);
    
    // Show error in status bar
    const statusBar = document.getElementById('status-bar-text');
    if (statusBar) {
      statusBar.textContent = 'Error: Failed to load pattern database';
    }
  }
})(); 